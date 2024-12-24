__author__ = "artur.fejklowicz@gmail.com"
__version__ = '0.2.0'
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
import os
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_vertexai import ChatVertexAI


# setup logging
log_client = google.cloud.logging.Client()
log_client.setup_logging()
logging.basicConfig(level=logging.INFO)
logging.getLogger('backoff').addHandler(logging.StreamHandler())

def parse_request(request) -> str:
    logging.info(f"parse_request: start")
    try:
        request_json = request.get_json()
        gs_path = request_json['gs_path']
    except Exception as e:
        logging.error(f"Error parsing request: {str(e)}")
        raise ValueError(f"Error parsing request: {str(e)}")
    logging.info(f"parse_request: gs_path: {gs_path}" )
    return gs_path


def start(request):
    """Starts loading of model, processing of features and prediction."""
    logging.info(f"start: start")
    
    # Parse request
    gs_path = parse_request(request)

    llm = ChatVertexAI(
        model="gemini-1.5-pro-001",
        temperature=0,
        max_tokens=8192,
        timeout=None,
        max_retries=2,
    )

    system_msg = """You are helpful assistant and you do exactly what you were requested to.
You do not make up any information. 
If you can not do something or you do not know, you simply says that you can not or you do not know."""
    
    system_msg = SystemMessage(content=system_msg)

    pdf_message = {
        "type": "image_url",
        "image_url": {"url": gs_path},
    }

    text_message = {
        "type": "text",
        "text": """Extract bank transactions from this file. Output transactions format: CSV.
Remember that Saldovortrag is not part of the data and should be excluded from CSV

CSV Format:
- Floats without high commas between thausands
- Buchungsnr. as separat column
- \"Artur ... CH\" as separate column named \"Empfanger\"
- Text stays in CSV but cuted from Empfanger
- Date format %Y-%m-%d""",
    }

    message = HumanMessage(content=[text_message, pdf_message])
    
    logging.info(f"Prompt: {message}")

    ai_msg = llm.invoke([message])
    logging.info(f"Response from Gemini: {ai_msg}")

    return "OK", 200


def main(request):
    try:
        return start(request)
    except Exception:
        logging.error(traceback.format_exc(), extra={"labels": {"version": __version__ }})
        raise RuntimeError
