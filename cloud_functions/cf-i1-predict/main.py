# __author__ = "Artur Fejklowicz"
# __copyright__ = "Copyright 2025, The AF Finanzen Project"
# __credits__ = ["Artur Fejklowicz", "Joi"]
# __license__ = "GPLv3"
# __version__ = "1.0.0"
# __maintainer__ = "Artur Fejklowicz"
# __status__ = "Production"

import base64
import json
import os
import re
import traceback
from datetime import datetime, timezone

import google.cloud.logging
import logging
from dateutil import parser
import logging
import traceback

import google.cloud.logging
from google.cloud import aiplatform
from google.cloud import storage

# --- Constants ---
PROJECT_ID = os.environ.get("GCP_PROJECT", "af-finanzen")
REGION = os.environ.get("GCP_REGION", "europe-west6")
PIPELINE_NAME = os.getenv("PIPELINE_NAME", "transak-i1-predict")
PIPELINE_BUCKET = os.getenv("PIPELINE_BUCKET", "gs://af-finanzen-mlops")
PIPELINE_ROOT = f"{PIPELINE_BUCKET}/pipelines/{PIPELINE_NAME}"
PIPELINE_TEMPLATE_GCS_PATH = f"{PIPELINE_ROOT}/{PIPELINE_NAME}.json"


# --- Logging ---
log_client = google.cloud.logging.Client()
log_client.setup_logging()
logging.basicConfig(level=logging.INFO)


def start(event, context):
    """
    Main logic for the Cloud Function.
    Parses the Pub/Sub message and triggers the Vertex AI prediction pipeline.
    """
    logging.info(f"start: EventID: {context.event_id}, EventType: {context.event_type}")

    # 1. Parse the Pub/Sub message to get the GCS file path
    try:
        # The actual notification data is base64-encoded in the 'data' field.
        message_data = base64.b64decode(event['data']).decode('utf-8')
        message_json = json.loads(message_data)
        bucket_name = message_json['bucket']
        file_path = message_json['name']
        logging.info(f"{message_json}")
        logging.info(f"Triggering file path: {file_path}")

        # 2. Read the content of the _SUCCESS file to get the prediction month and optional region
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_path)
        content = blob.download_as_text().strip().splitlines()
        
        if not content:
             raise ValueError("The _SUCCESS file is empty.")

        month = content[0].strip()
        
        if not re.match(r'^\d{6}$', month):
            raise ValueError(f"Invalid prediction month format in _SUCCESS file: {month}")

        logging.info(f"Extracted prediction month: {month}")

        # Determine region and resource limits
        # Default to environment variable if not specified in file
        region_to_use = REGION
        cpu_limit = "4"
        memory_limit = "15G"

        if len(content) > 1 and content[1].strip():
            line2 = content[1].strip()
            # Check if line2 is in key=value format (e.g. region=europe-west6,cpu=4,mem=15G)
            if "=" in line2:
                try:
                    # Parse comma-separated key=value pairs
                    settings = dict(item.split("=") for item in line2.split(","))
                    settings = {k.strip(): v.strip() for k, v in settings.items()}
                    
                    if "region" in settings:
                        region_to_use = settings["region"]
                    if "cpu_limit" in settings:
                        cpu_limit = settings["cpu_limit"]
                    if "memory_limit" in settings:
                        memory_limit = settings["memory_limit"]
                    
                    logging.info(f"Parsed configuration from _SUCCESS: region={region_to_use}, cpu_limit={cpu_limit}, memory_limit={memory_limit}")
                except Exception as e:
                    logging.warning(f"Failed to parse configuration line '{line2}': {e}. Using defaults.")
            else:
                # Legacy behavior: treat entire line as region
                region_to_use = line2
                logging.info(f"Found legacy region override in _SUCCESS file: {region_to_use}")
        
    except (KeyError, TypeError, ValueError) as e:
        logging.error(f"Error parsing event data or reading _SUCCESS file: {e}")
        raise
    
    # 3. Initialize the Vertex AI client
    logging.info(f"Initializing Vertex AI with region: {region_to_use}")
    aiplatform.init(project=PROJECT_ID, location=region_to_use)

    # 4. Define the pipeline job
    pipeline = aiplatform.PipelineJob(
        display_name=f"{PIPELINE_NAME}-{month}",
        template_path=PIPELINE_TEMPLATE_GCS_PATH,
        pipeline_root=PIPELINE_ROOT,
        parameter_values={
            "month": month,
            "region": region_to_use,
            "cpu_limit": cpu_limit,
            "memory_limit": memory_limit
        },
        enable_caching=False
    )

    # 5. Submit the pipeline job for execution
    logging.info(f"Submitting pipeline job for month {month}...")
    pipeline.submit()
    logging.info("Pipeline job submitted successfully.")


def main(event, context):
    """
    Cloud Function entry point with timeout/retry logic.
    """
    
    try:
        timestamp = context.timestamp
        event_time = parser.parse(timestamp)
        event_age_seconds = (datetime.now(timezone.utc) - event_time).total_seconds()
        
        # Ignore events that are too old
        max_age_seconds = 60
        if event_age_seconds > max_age_seconds:
            logging.warning(
                f"Dropped event {context.event_id} with age {event_age_seconds}s. Exceeds max age of {max_age_seconds}s."
            )
            return "Trigger timeout"

        start(event, context)
        return "Pipeline triggered."

    except Exception:
        logging.error(traceback.format_exc())
        raise RuntimeError("Cloud Function failed")
