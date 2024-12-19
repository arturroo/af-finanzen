__author__ = "artur.fejklowicz@gmail.com"
__version__ = '0.1.0'
__doc__ = """
Minions are AI Agents, that cooperate to extract table with bank transactions from PDF File.
In Bank ZAK (Cler) the only way to get the transactions is to download PDF for particular month from mobile app. This pdf has many various informations, including list of transactions. Tasks for Minions:
- Extract transactions to CSV Format - format will be specified in prompt
- Check if exported data are really CSV
- Check if integers do not have thousand high commas
"""

import logging
import traceback
import backoff
import google.cloud.logging
from google.cloud import storage
from google.cloud import bigquery
import os
from flask import escape
from langchain import Langchain
from langchain.llms import VertexAI  # Or your preferred LLM (e.g., VertexAI)
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from google.cloud import secretmanager
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
from dataclasses import dataclass

GCP_PROJECT = os.environ.get("GCP_PROJECT")

# setup logging
log_client = google.cloud.logging.Client()
log_client.setup_logging()
logging.basicConfig(level=logging.INFO)
logging.getLogger('backoff').addHandler(logging.StreamHandler())

def access_secret_version(project_id, secret_id, version_id="latest"):
    """
    Accesses the payload for the given secret version if it exists.
    """
    sm = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    response = sm.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

@dataclass
class TechInfo:
    bucket: str
    blob_name: str
    gs_path: str
    

def parse_request(request) -> TechInfo:
    logging.info(f"parse_request: start")
    # try:
    #     request_json = request.get_json()
    #     gs_path = request_json['gs_path']
    # except Exception as e:
    #     logging.error(f"Error parsing request: {str(e)}")
    #     raise ValueError(f"Error parsing request: {str(e)}")
    # 
    # bucket = gs_path.split('/')[2]
    # blob_name = '/'.join(gs_path.split('/')[3:])
    # tech_info = TechInfo(bucket=bucket, blob_name=blob_name, gs_path=gs_path)
    # 
    # logging.info(f"parse_request: tech_info: {tech_info}" )

    # return tech_info
    request_json = request.get_json()
    prompt = request_json['prompt'] if 'prompt' in request_json else None
    logging.info(f"parse_request: prompt: {prompt}" )
    return prompt

# @backoff.on_exception(backoff.expo, Exception, max_tries=5)
# def load_from_gcs(tech_info: TechInfo):
#     """Loads the model or vectorizer from Google Cloud Storage."""
# 
# 
#     try:
#         gs = storage.Client()
#         bucket = gs.bucket(tech_info.bucket)
#         blob = bucket.blob(tech_info.blob_name)
#         file_path = Path("/tmp") / tech_info.blob_name.split('/')[-1]
#         blob.download_to_filename(file_path)
#         # with open(file_path, 'rb') as f:
#         #     if method == "pkl":
#         #         python_object = pickle.load(f)
#         #     elif method == "joblib":
#         #         python_object = joblib.load(f)
#         #     else:
#         #         raise Exception(f"No such save method: {method}")
#         # print(f"Loaded object from gs://{bucket_name}/{blob_name}")
#     except Exception as e:
#         raise Exception(f"Error loading object from {tech_info.gs_path}: {str(e)}")
# 
#     # return python_object
#     return True

def start(request):
    """Starts loading of model, processing of features and prediction."""
    logging.info(f"start: start")
    
    # tech_info = parse_request(request)

    # Get the API key from Secret Manager
    try:
        gemini_api_key = access_secret_version(GCP_PROJECT, "API_KEY")  # Replace "MY_API_KEY" with your secret's name
        lc = Langchain(api_key=gemini_api_key)
        status = lc.check_connection()
        logging.info(f"Connection to Gemini: {status}")
    except Exception as e:
        logging.error(f"Error accessing secret or Gemini API: {e}")


    structured_prompt = """
    # Task
    Provide an overview of natural language processing (NLP).

    # Requirements
    - Use bullet points.
    - Keep it concise (no more than five points).
    - Use a professional tone.
    """

    prompt_request = parse_request(request)
    prompt = prompt_request if prompt_request is not None else structured_prompt

    response = lc.generate(prompt)
    logging.info(f"Response from Gemini: {response}")




    return "OK", 200


def main(request):
    try:
        return start(request)
    except Exception:
        logging.error(traceback.format_exc(), extra={"labels": {"version": __version__ }})
        raise RuntimeError
