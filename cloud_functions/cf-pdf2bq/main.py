__author__ = "artur.fejklowicz@gmail.com"
__version__ = '0.2.0'
__doc__ = """
CF pdf2bq cooperate to extract table with bank transactions from PDF File.
In Bank ZAK (Cler) the only way to get the transactions is to download PDF for particular month from mobile app. This pdf has many various informations, including list of transactions. Tasks for Minions:
- Extract transactions to CSV Format - format will be specified in prompt
- Check if exported data are really CSV
- Check if integers do not have thousand high commas
"""

import os
import json
import logging
import traceback
import backoff
import google.cloud.logging
from google.cloud import storage
from google.cloud import bigquery
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_vertexai import ChatVertexAI

USER_MESSAGE = """Extract bank transactions from this file and put then in csv format please.
Your response must be only the raw CSV content, without any markdown, formatting, or explanations. Start directly with the header row.

Remember that Saldovortrag is not part of the data and should not by in CSV
CSV Format:
- Floats without high commas between thausands
- Buchungsnr. as separat column
- "Artur UBS Ida-Sträuli-Strasse 41 8404 Winterthur CH" as separate column named "Empfanger"
- Text stays in CSV but cuted from Empfanger
- Date format %Y-%m-%d

CSV schema in format column_name:data_type: 
buchungsnr:int,datum:date,valuta:date,empfanger:str,belastung:float,gutschrift:float,saldo:float,text:str

Here is an example of the required format:
buchungsnr,datum,valuta,empfanger,belastung,gutschrift,saldo,text
12345,2025-01-01,2025-01-01,"Example Recipient",50.25,0.00,1000.00,"Example text"
"""
TEMPERATURE = 0.0
TOP_P = 0.1


# setup logging
log_client = google.cloud.logging.Client()
log_client.setup_logging()
logging.basicConfig(level=logging.INFO)
logging.getLogger('backoff').addHandler(logging.StreamHandler())

def parse_request(request) -> tuple[str, str, float, float]:
    logging.info(f"parse_request: start")
    try:
        request_json = request.get_json()
        pdf_uri = str(request_json['pdf_uri'])
    except Exception as e:
        logging.error(f"Error parsing request: {str(e)}")
        raise ValueError(f"Error parsing request: {str(e)}")
    logging.info(f"parse_request: pdf_uri: {pdf_uri}" )

    user_message = str(request_json.get('user_message', USER_MESSAGE))
    temperatur = float(request_json.get('temperature', TEMPERATURE))
    top_p = float(request_json.get('top_p', TOP_P))
    logging.info(f"parse_request: temperatur: {temperatur}" )
    logging.info(f"parse_request: user_message: {user_message}" )
    logging.info(f"parse_request: top_p: {top_p}" )

    return (pdf_uri, user_message, temperatur, top_p)


def load_csv_to_bq(bucket_name, blob_name):
    """Loads a CSV file from Google Cloud Storage to a BigQuery table."""
    logging.info(f"load_csv_to_bq: start, bucket_name: {bucket_name}, blob_name: {blob_name}")
    
    bq = bigquery.Client()
    dataset_id = "banks"
    table_id = "zak"
    table_ref = bq.dataset(dataset_id).table(table_id)
    
    schema_path = os.path.join(os.path.dirname(__file__), 'banks.zak.json')
    with open(schema_path) as f:
        schema_json = f.read()
    schema = [bigquery.SchemaField.from_api_repr(field) for field in json.loads(schema_json)]

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    uri = f"gs://{bucket_name}/{blob_name}"
    load_job = bq.load_table_from_uri(
        uri,
        table_ref,
        job_config=job_config
    )
    load_job.result()
    logging.info(f"Loaded {load_job.output_rows} rows into {dataset_id}:{table_id} from {uri}")

def save_to_gcs(content, blob_name):
    """Saves content to a file in Google Cloud Storage."""
    logging.info(f"save_to_gcs: start, blob_name: {blob_name}")
    gs = storage.Client()
    bucket_name = os.environ.get("BUCKET_NAME", "af-finanzen")
    bucket = gs.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(content, content_type="text/csv")
    logging.info(f"CSV file uploaded to gs://{bucket_name}/{blob_name}")
    logging.info(f"save_to_gcs: end, bucket_name: {bucket_name}")
    return bucket_name

def start(request):
    """Starts loading of model, processing of features and prediction."""
    logging.info(f"start: start")
    
    # Parse request
    pdf_uri, user_message, temperatur, top_p = parse_request(request)

    gemini = ChatVertexAI(
        model="gemini-2.0-flash-exp",
        temperature=temperatur,
        max_tokens=8192,
        timeout=None,
        max_retries=2,
        top_p=top_p,
    )

    system_msg = """You are helpful assistant and you do exactly what you were requested to.
You do not make up any information. 
If you can not do something or you do not know, you simply says that you can not or you do not know."""
    
    system_msg = SystemMessage(content=system_msg)

    pdf_message = {
        "type": "image_url",
        "image_url": {"url": pdf_uri},
    }

    text_message = {
        "type": "text",
        "text": user_message,
    }

    message = HumanMessage(content=[text_message, pdf_message])
    logging.info(f"Prompt: {message}")

    gemini_msg = gemini.invoke([message])
    
    blob_name = f"cf-pdf2bq/bank_zak_transactions_{gemini_msg.id}.csv"
    bucket_name = save_to_gcs(gemini_msg.content, blob_name)

    load_csv_to_bq(bucket_name, blob_name)

    return "OK", 200


def main(request):
    try:
        return start(request)
    except Exception:
        logging.error(traceback.format_exc(), extra={"labels": {"version": __version__ }})
        raise RuntimeError
