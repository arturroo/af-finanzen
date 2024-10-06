__author__ = "artur.fejklowicz@gmail.com"
__version__ = '0.1.0'
__doc__ = """
Loads sklearn logistic regression model from file that is in Google cloud storage.
Loads test text from request or from BigQuery
Vectorizes the raw data and performs prediction.
"""
import logging
import traceback
import backoff
import google.cloud.logging
from google.cloud import storage
from google.cloud import bigquery
# from flask import jsonify, request
import os
from datetime import datetime
from FeatureEngineering import FeatureEngineering
import pandas as pd
from pathlib import Path
import pickle
import joblib

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression


# setup logging
log_client = google.cloud.logging.Client()
log_client.setup_logging()
logging.basicConfig(level=logging.INFO)
logging.getLogger('backoff').addHandler(logging.StreamHandler())

# load sklearn logistic regression from file that is in google cloud storage
BUCKET_NAME = os.environ.get('BUCKET_NAME', 'af-finanzen-banks')


def parse_request(request):
    logging.info(f"parse_request: start")
    try:
        request_json = request.get_json()
        timestamp = request_json['timestamp']
        vectorizer_fn = request_json['vectorizer_fn']
        model_fn = request_json['model_fn']
    except Exception as e:
        logging.error(f"Error parsing request: {str(e)}")
        raise ValueError(f"Error parsing request: {str(e)}")

    test_text = None
    if "test_text" in request_json:
        test_text = pd.DataFrame({'description': [request_json['test_text']]})
    month = request_json['month'] if 'month' in request_json else None
    logging.info(f"parse_request: timestamp: {timestamp}")
    logging.info(f"parse_request: vectorizer_fn: {vectorizer_fn}")
    logging.info(f"parse_request: model_fn: {model_fn}")
    logging.info(f"parse_request: test_text: {test_text}")
    logging.info(f"parse_request: month: {month} ")

    return timestamp, vectorizer_fn, model_fn, test_text, month

@backoff.on_exception(backoff.expo, Exception, max_tries=5)
def load_from_gcs(timestamp: str = None, object_fn:str = None):
    """Loads the model or vectorizer from Google Cloud Storage."""
    bucket_name = "af-finanzen-banks"
    method = object_fn.split(".")[-1]
    blob_name = f"models/lr/{timestamp}/{object_fn}"

    try:
        gs = storage.Client()
        bucket = gs.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        file_path = Path("/tmp") / object_fn
        blob.download_to_filename(file_path)
        with open(file_path, 'rb') as f:
            if method == "pkl":
                python_object = pickle.load(f)
            elif method == "joblib":
                python_object = joblib.load(f)
            else:
                raise Exception(f"No such save method: {method}")
        print(f"Loaded object from gs://{bucket_name}/{blob_name}")
        return python_object
    except Exception as e:
        raise Exception(f"Error loading object from gs://{bucket_name}/{blob_name}: {str(e)}")


@backoff.on_exception(backoff.expo, Exception, max_tries=5)
def load_test_data(month: str = None):
    """Loads test data from Google BigQuery."""
    if not month:
        month = datetime.now().strftime('%Y-%m')
    logging.info(f"load_test_data: Loading test data for month {month}")
    try:
        bq = bigquery.Client()
        query = f"""
            SELECT DISTINCT description
            FROM banks.revolut_v
            WHERE month = "{month}"
        """
        return bq.query(query).to_dataframe()
    except Exception as e:
        raise Exception(f"Error loading test data: {str(e)}")

def predict(X_pred, model):
    """Handles prediction requests."""
    logging.info(f"predict: starting prediction for {X_pred}")
    y_pred = model.predict(X_pred)
    y_pred_proba = model.predict_proba(X_pred)
    logging.info(f"predict: y_pred {y_pred}")
    logging.info(f"predict: y_pred_proba {y_pred_proba}")
    return y_pred

def start(request):
    """Starts loading of model, processing of features and prediction."""
    logging.info(f"start: start")
    
    timestamp, vectorizer_fn, model_fn, test_text, month = parse_request(request)
    raw_data = load_test_data(month) if test_text is None else test_text
    fe = FeatureEngineering(raw_data, load_from_gcs(timestamp, vectorizer_fn))
    X_pred = fe.get_features()
    model = load_from_gcs(timestamp, model_fn)
    
    y_pred = predict(X_pred, model)
    # Prepare data for return
    predictions = []
    for description, pred_class in zip(raw_data['description'], y_pred):
        pred_label=fe.label_decoder[pred_class]
        logging.info(f"Description: '{description}' predicted Label: {pred_label}")    
        predictions.append({
            "Description": description,
            "Predicted Label": pred_label
        })
    return {"predictions": predictions}, 200

def main(request):
    try:
        return start(request)
    except Exception:
        logging.error(traceback.format_exc(), extra={"labels": {"version": __version__ }})
        raise RuntimeError
