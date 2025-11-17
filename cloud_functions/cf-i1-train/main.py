# __author__ = "Artur Fejklowicz"
# __copyright__ = "Copyright 2025, The AF Finanzen Project"
# __credits__ = ["Artur Fejklowicz", "Joi"]
# __license__ = "GPLv3"
# __version__ = "2.0.0"
# __maintainer__ = "Artur Fejklowicz"
# __status__ = "Production"

import base64
import json
import os
import logging
import traceback
from datetime import datetime

import google.cloud.logging
from google.cloud import aiplatform, storage

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


def parse_pubsub_message(event: dict) -> dict:
    """Parses the Pub/Sub message to extract the data payload."""
    logging.info("Parsing Pub/Sub message...")
    message_data = base64.b64decode(event['data']).decode('utf-8')
    message_json = json.loads(message_data)
    logging.info("Message received:")
    logging.info(json.dumps(message_json, indent=2))
    
    if "anomalies" not in message_json:
        raise ValueError("Pub/Sub message is missing the 'anomalies' key.")
        
    return message_json


def check_for_drift(anomalies_gcs_path: str) -> bool:
    """
    Downloads anomalies.json from GCS and checks for drift against its internal thresholds.

    Args:
        anomalies_gcs_path: The GCS path to the anomalies.json file.

    Returns:
        True if drift is detected, False otherwise.
    """
    logging.info(f"Checking for drift in '{anomalies_gcs_path}'...")
    storage_client = storage.Client()
    
    # GCS path format: gs://<bucket>/<blob>
    bucket_name, blob_name = anomalies_gcs_path.replace("gs://", "").split("/", 1)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    
    if not blob.exists():
        raise FileNotFoundError(f"GCS object not found: {anomalies_gcs_path}")

    anomalies_data = json.loads(blob.download_as_string())
    
    # The anomalies.json contains a 'driftSkewInfo' list
    if "driftSkewInfo" not in anomalies_data:
        logging.info("No 'driftSkewInfo' found in anomalies.json. No drift detected.")
        return False

    for feature_info in anomalies_data["driftSkewInfo"]:
        feature_name = feature_info["path"]["step"][0] # e.g., "description" or "type"
        
        for measurement in feature_info["driftMeasurements"]:
            drift_value = measurement.get("value")
            drift_threshold = measurement.get("threshold")

            if drift_value is not None and drift_threshold is not None:
                if drift_value > drift_threshold:
                    logging.warning(
                        f"Drift detected! Feature '{feature_name}' has a drift value of {drift_value}, "
                        f"which is above its calculated threshold of {drift_threshold}."
                    )
                    return True
            else:
                logging.warning(f"Drift measurement for feature '{feature_name}' missing 'value' or 'threshold': {measurement}")
            
    logging.info("No feature drift detected above the calculated thresholds.")
    return False


def trigger_training_pipeline():
    """Initializes and submits the Vertex AI training pipeline."""
    logging.info("Initializing Vertex AI client...")
    aiplatform.init(project=PROJECT_ID, location=REGION)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    pipeline = aiplatform.PipelineJob(
        display_name=f"{PIPELINE_NAME}-triggered-{timestamp}",
        template_path=PIPELINE_TEMPLATE_GCS_PATH,
        pipeline_root=PIPELINE_ROOT,
        parameter_values={},
        enable_caching=False  # Always run fresh for retraining
    )

    logging.info("Submitting new training pipeline job...")
    pipeline.submit()
    logging.info("Pipeline job submitted successfully.")


def main(event, context):
    """
    Cloud Function entry point.
    - Parses Pub/Sub message for anomalies.json path.
    - Checks for model drift.
    - Triggers a new training pipeline run if drift is detected.
    """
    logging.info(f"start: EventID: {context.event_id}, EventType: {context.event_type}")

    try:
        # 1. Parse and Validate Input
        message = parse_pubsub_message(event)
        anomalies_path = message["anomalies"]

        # 2. Business Logic: Check for Drift
        drift_detected = check_for_drift(anomalies_path)

        # 3. Conditional Action: Trigger Pipeline
        if drift_detected:
            trigger_training_pipeline()
            return "Drift detected. Training pipeline triggered."
        else:
            logging.info("No significant drift detected. No action taken.")
            return "No drift detected. No action taken."

    except Exception:
        logging.error("Function failed:")
        logging.error(traceback.format_exc())
        raise RuntimeError("Cloud Function failed during execution")
