__version__ = '0.1.0'

import logging
import traceback
import backoff
import google.cloud.logging
from google.cloud import storage
# from flask import jsonify, request
import pickle
import os

log_client = google.cloud.logging.Client()
log_client.setup_logging()
logging.basicConfig(level=logging.INFO)
logging.getLogger('backoff').addHandler(logging.StreamHandler())

# load sklearn logistic regression from file that is in google cloud storage


def parse_request(request):
    try:
        request_json = request.get_json()

        # Check if request_json is valid before accessing keys
        if request_json:
            fe_type = request_json.get('fe_type')
            model_path = request_json.get('model_path')
        else:
            # Handle the case where the request doesn't have valid JSON
            fe_type = None
            model_path = None
            # ... (You might want to return an error response here)

    except Exception as e:
        # Handle any other exceptions during JSON parsing
        # ... (Log the error, return an error response, etc.)

    text = request_json.get('text')


@backoff.on_exception(backoff.expo, Exception, max_tries=5)
def get_gs_client():
    return storage.Client()

def load_model(model_path):
    """Loads the model from Google Cloud Storage."""
    try:
        gs = get_gs_client()
        bucket = gs.bucket(BUCKET_NAME)
        blob = bucket.blob(model_path)
        blob.download_to_filename('/tmp/model.pkl')
        with open('/tmp/model.pkl', 'rb') as f:
            model = pickle.load(f)
        return model
    except Exception as e:
        raise Exception(f"Error loading model: {str(e)}")

def perform_feature_engineering(text, fe_type):
    """Performs feature engineering based on the selected method."""
    if fe_type == 'bow':
        return bow_vectorizer.transform([text])
    elif fe_type == 'tfidf':
        return tfidf_vectorizer.transform([text])
    elif fe_type == 'embeddings':
        # ... your embedding logic
    else:
        raise ValueError("Invalid fe_type") 

def predict(X_test) -> str:
    """Handles prediction requests."""
    try:
        request_data = request.get_json() if request.method == 'POST' else request.args
        text = request_data.get('text')
        model_path = request_data.get('model_path')
        fe_type = request_data.get('fe_type')

        if not all([text, model_path, fe_type]):
            return jsonify({'error': 'Missing required parameters.'}), 400

        model = load_model(model_path)
        features = perform_feature_engineering(text, fe_type)
        predictions = model.predict(features)

        return jsonify({'predictions': predictions.tolist()})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def start(request):
    """Starts loading of model, processing of features and prediction."""
    return predict(request)

def main(request):
    try:
        return start(request)
    except Exception:
        logging.error(traceback.format_exec(), extra={"labels": {"version": __version__ }})
        raise RuntimeError


# model_path = os.path.join(os.path.dirname(file), 'model.pkl')
# with open(model_path, 'rb') as f:
# model = pickle.load(f)
# 
# def predict(request):
#     predictions = model.predict(features)
# 
# return jsonify({'predictions': predictions.tolist()})
# else:
# return jsonify({'error': 'Missing "features" key in request body'}), 400
# except Exception as e:
# return jsonify({'error': str(e)}), 500
# else:
# return jsonify({'error': 'Invalid request method'}), 405