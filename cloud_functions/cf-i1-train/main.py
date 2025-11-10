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
import logging
import traceback
from datetime import datetime

import google.cloud.logging
from google.cloud import aiplatform

# --- Constants ---
PROJECT_ID = os.environ.get("PROJECT_ID", "af-finanzen")
REGION = os.environ.get("REGION", "europe-west6")
PIPELINE_NAME = os.getenv("PIPELINE_NAME", "transak-i1-train")
PIPELINE_BUCKET = os.getenv("PIPELINE_BUCKET", "gs://af-finanzen-mlops")
PIPELINE_ROOT = f"{PIPELINE_BUCKET}/pipelines/{PIPELINE_NAME}"
PIPELINE_TEMPLATE_GCS_PATH = f"{PIPELINE_ROOT}/{PIPELINE_NAME}.json"


# --- Logging ---
log_client = google.cloud.logging.Client()
log_client.setup_logging()
logging.basicConfig(level=logging.INFO)


def main(event, context):
    """
    Cloud Function entry point.
    - Parses the Pub/Sub message from the Model Monitor.
    - Triggers a new run of the Vertex AI training pipeline.
    """
    logging.info(f"start: EventID: {context.event_id}, EventType: {context.event_type}")

    try:
        # 1. Parse and log the Pub/Sub message
        message_data = base64.b64decode(event['data']).decode('utf-8')
        message_json = json.loads(message_data)
        logging.info("Drift detection notification received:")
        logging.info(json.dumps(message_json, indent=2))

        # 2. Initialize the Vertex AI client
        aiplatform.init(project=PROJECT_ID, location=REGION)

        # 3. Define the pipeline job
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        pipeline = aiplatform.PipelineJob(
            display_name=f"{PIPELINE_NAME}-triggered-{timestamp}",
            template_path=PIPELINE_TEMPLATE_GCS_PATH,
            pipeline_root=PIPELINE_ROOT,
            parameter_values={},
            enable_caching=False  # Always run fresh for retraining
        )

        # 4. Submit the pipeline job for execution
        logging.info("Submitting new training pipeline job...")
        pipeline.submit()
        logging.info("Pipeline job submitted successfully.")
        return "Training pipeline triggered."

    except Exception:
        logging.error("Function failed:")
        logging.error(traceback.format_exc())
        raise RuntimeError("Cloud Function failed to trigger training pipeline")
