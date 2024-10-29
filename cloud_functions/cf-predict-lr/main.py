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
from datetime import datetime,timezone
from FeatureEngineering import FeatureEngineering
from TechInfo import TechInfo
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
PRED_TABLE_NAME = os.environ.get('PRED_TABLE_NAME', 'banks.predictions')


def parse_request(request) -> TechInfo:
    logging.info(f"parse_request: start")
    try:
        request_json = request.get_json()
        training_dt = request_json['training_dt']
        vectorizer_fn = request_json['vectorizer_fn']
        model_fn = request_json['model_fn']
    except Exception as e:
        logging.error(f"Error parsing request: {str(e)}")
        raise ValueError(f"Error parsing request: {str(e)}")

    test_text = None
    if "test_text" in request_json:
        test_text = pd.DataFrame({'description': [request_json['test_text']]})
    month = request_json['month'] if 'month' in request_json else None
    ti = TechInfo({
        'training_dt': training_dt,
        'vectorizer_fn': vectorizer_fn,
        'model_fn': model_fn,
        'test_text': test_text,
        'month': month
    })
    logging.info(f"parse_request: tech_info: {ti.get_all()}" )

    return ti

@backoff.on_exception(backoff.expo, Exception, max_tries=5)
def load_from_gcs(training_dt: str = None, object_fn:str = None):
    """Loads the model or vectorizer from Google Cloud Storage."""
    bucket_name = "af-finanzen-banks"
    method = object_fn.split(".")[-1]
    blob_name = f"models/lr/{training_dt}/{object_fn}"

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
    return y_pred, y_pred_proba

def make_rows(label_decoder, raw_data, y_pred, y_pred_proba, tech_info):
    now_utc=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    logging.info(f"make_rows: now_utc {now_utc}")
    json_rows = []
    for i, row in raw_data.iterrows():
        json_rows.append({
            'bank': 'Revolut',
            'description': row['description'],
            'pred_label': label_decoder[y_pred[i]],
            'y_pred': y_pred[i].tolist(),
            'y_proba': y_pred_proba[i].tolist(),
            'training_dt': tech_info.training_dt,
            'vectorizer_fn': tech_info.vectorizer_fn,
            'model_fn': tech_info.model_fn,
            'month': tech_info.month,
            'cre_ts': "AUTO"
        })
    return json_rows

@backoff.on_exception(backoff.expo, Exception, max_tries=5)
def save2bq(label_decoder, raw_data, y_pred, y_pred_proba, tech_info):
    json_rows = make_rows(label_decoder, raw_data, y_pred, y_pred_proba, tech_info)
    bq = bigquery.Client()
    table = bq.get_table(PRED_TABLE_NAME)
    return bq.insert_rows_json(table, json_rows) #, ignore_unknown_values=True)

def start(request):
    """Starts loading of model, processing of features and prediction."""
    logging.info(f"start: start")
    
    ti = parse_request(request)
    raw_data = load_test_data(ti.month) if ti.test_text is None else ti.test_text
    fe = FeatureEngineering(raw_data, load_from_gcs(ti.training_dt, ti.vectorizer_fn))
    X_pred = fe.get_features()
    model = load_from_gcs(ti.training_dt, ti.model_fn)
    
    y_pred, y_pred_proba = predict(X_pred, model)
    errors = save2bq(fe.label_decoder, raw_data, y_pred, y_pred_proba, ti)

    # Prepare data for return
    predictions_txt = []
    for description, pred_class in zip(raw_data['description'], y_pred):
        pred_label=fe.label_decoder[pred_class]
        predictions_txt.append({
            "Description": description,
            "Predicted Label": pred_label
        })
    return {"predictions": predictions_txt, "errors": errors, "version": __version__}, 200

def main(request):
    try:
        return start(request)
    except Exception:
        logging.error(traceback.format_exc(), extra={"labels": {"version": __version__ }})
        raise RuntimeError
