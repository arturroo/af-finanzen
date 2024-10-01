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
import pickle
import os
from datetime import datetime
from FeatureEngineering import FeatureEngineering
import pandas as pd

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
        vectorizer = request_json['vectorizer']
        model_path = request_json['model_path']
    except Exception as e:
        logging.error(f"Error parsing request: {str(e)}")
        raise ValueError(f"Error parsing request: {str(e)}")

    test_text = None
    if request_json['test_text']:
        test_text = pd.DataFrame({'description': [request_json['test_text']]})

    month = request_json['month'] if 'month' in request_json else None

    return vectorizer, model_path, test_text, month

@backoff.on_exception(backoff.expo, Exception, max_tries=5)
def load_model(model_path: str = None):
    """Loads the model from Google Cloud Storage."""
    logging.info(f"load_model: Loading model from {model_path}")
    try:
        gs = storage.Client()
        bucket = gs.bucket(BUCKET_NAME)
        blob = bucket.blob(model_path)
        blob.download_to_filename('/tmp/model.pkl')
        with open('/tmp/model.pkl', 'rb') as f:
            model = pickle.load(f)
        return model
    except Exception as e:
        raise Exception(f"Error loading model: {str(e)}")

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

def feature_engineering(vectorizer, raw_data: pd.DataFrame = None):
    """Performs feature engineering based on the selected method."""
    fe = FeatureEngineering(vectorizer, raw_data)

    # if fe_type == 'bow':
    #     return bow_vectorizer.transform([text])
    # elif fe_type == 'tfidf':
    #     return tfidf_vectorizer.transform([text])
    # elif fe_type == 'embeddings':
    #     # ... your embedding logic
    # else:
    #     raise ValueError("Invalid fe_type") 

def predict(X_pred):
    """Handles prediction requests."""
    pass

def start(request):
    """Starts loading of model, processing of features and prediction."""
    logging.info(f"start: start")
    vectorizer, model_path, test_text, month = parse_request(request)
    raw_data = load_test_data(month) if not test_text else test_text
    X_pred = feature_engineering(raw_data, vectorizer)
    model = load_model(model_path)
    y_pred = predict(X_pred, model)
    logging.info(f"start: preds: {y_pred}")
    return y_pred, 200

def main(request):
    try:
        return start(request)
    except Exception:
        logging.error(traceback.format_exec(), extra={"labels": {"version": __version__ }})
        raise RuntimeError
