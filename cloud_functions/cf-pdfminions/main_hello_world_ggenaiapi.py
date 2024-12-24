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
# from google.cloud import storage
# from google.cloud import bigquery
import os
import getpass
# from flask import escape
from langchain_google_genai import ChatGoogleGenerativeAI

# from langchain_google_vertexai import ChatVertexAI
# from langchain import Langchain
# from langchain.llms import VertexAI  # Or your preferred LLM (e.g., VertexAI)
# from langchain.chains import LLMChain
# from langchain.prompts import PromptTemplate
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
    # name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    name = f"projects/819397114258/secrets/AISTUDIO_GEMINI_API_KEY/versions/{version_id}"
    logging.info(f"access_secret_version: {name}" )
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


def start(request):
    """Starts loading of model, processing of features and prediction."""
    logging.info(f"start: start")
    
    # tech_info = parse_request(request)

    # Get the API key from Secret Manager
    try:
        gemini_api_key = access_secret_version(GCP_PROJECT, "AISTUDIO_GEMINI_API_KEY")  # Replace "MY_API_KEY" with your secret's name
        # lc = Langchain(api_key=gemini_api_key)
        # status = lc.check_connection()
        # logging.info(f"Connection to Gemini: {status}")
    except Exception as e:
        logging.error(f"Error accessing secret or Gemini API: {e}")
    
    # if "GOOGLE_API_KEY" not in os.environ:
    #     os.environ["GOOGLE_API_KEY"] = getpass.getpass(gemini_api_key)

    os.environ["GOOGLE_API_KEY"] = gemini_api_key

    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        temperature=0,
        max_tokens=8192,
        timeout=None,
        max_retries=2,
        # other params...
    )

    translate_request = parse_request(request)
    text_to_translate = translate_request if translate_request is not None else "I love programming."
    system_msg = ("system", "You are helpful assistant and you do exactly what you were requested to. You do not make up any information. If you can not do something or you do not know, you simply says that you can not or you do not know.")
    human_msg = ("human", text_to_translate)
    ai_msg = llm.invoke([system_msg, human_msg])

    messages = [
        (
            "system",
            "You are a helpful assistant that translates English to German. Translate the user sentence.",
        ),
        ("human", text_to_translate),
    ]
    ai_msg = llm.invoke(messages)

    # structured_prompt = """
    # # Task
    # Provide an overview of natural language processing (NLP).
    # 
    # # Requirements
    # - Use bullet points.
    # - Keep it concise (no more than five points).
    # - Use a professional tone.
    # """
    # 
    # prompt_request = parse_request(request)
    # prompt = prompt_request if prompt_request is not None else structured_prompt
    # 
    # response = lc.generate(prompt)
    
    logging.info(f"Response from Gemini: {ai_msg}")


    return "OK", 200


def main(request):
    try:
        return start(request)
    except Exception:
        logging.error(traceback.format_exc(), extra={"labels": {"version": __version__ }})
        raise RuntimeError
