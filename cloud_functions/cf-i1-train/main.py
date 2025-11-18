# __author__ = "Artur Fejklowicz"
# __copyright__ = "Copyright 2025, The AF Finanzen Project"
# __credits__ = ["Artur Fejklowicz", "Joi"]
# __license__ = "GPLv3"
# __version__ = "2.1.0"
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
from vertexai.resources.preview import ml_monitoring

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

    if "attributes" in event:
        logging.info("Message attributes: %s", json.dumps(event["attributes"], indent=2))
    else:
        logging.info("No attributes found in message.")

    message_data = base64.b64decode(event['data']).decode('utf-8')
    logging.info(f"Raw message data: {message_data}")
    message_json = json.loads(message_data)
    logging.info("Message received:")
    logging.info(json.dumps(message_json, indent=2))

    # The message from Cloud Monitoring log-based alert
    if "jsonPayload" in message_json and "anomalyGcsFolder" in message_json["jsonPayload"]:
        anomaly_gcs_folder = message_json["jsonPayload"]["anomalyGcsFolder"]
        anomalies_gcs_path = f"{anomaly_gcs_folder}/anomalies.json"
        return {"type": "gcs", "path": anomalies_gcs_path}
    
    # The message from Model Monitoring email/pubsub notification
    elif "details" in message_json and "model_monitoring_job_name" in message_json["details"]:
        job_name = message_json["details"]["model_monitoring_job_name"]
        return {"type": "api", "job_name": job_name}
    
    else:
        raise ValueError("Pub/Sub message has an unrecognized format.")


def check_for_drift_from_gcs(anomalies_gcs_path: str) -> bool:
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
    
    if "featureAnomalies" not in anomalies_data:
        logging.info("No 'featureAnomalies' found in anomalies.json. No drift detected.")
        return False

    for feature_anomaly in anomalies_data["featureAnomalies"]:
        feature_name = feature_anomaly.get("featureDisplayName")
        deviation = feature_anomaly.get("deviation")
        threshold = feature_anomaly.get("threshold")

        if deviation is not None and threshold is not None:
            if deviation > threshold:
                logging.warning(
                    f"Drift detected! Feature '{feature_name}' has a deviation of {deviation}, "
                    f"which is above its threshold of {threshold}."
                )
                return True
        else:
            logging.warning(f"Drift measurement for feature '{feature_name}' missing 'deviation' or 'threshold': {feature_anomaly}")
            
    logging.info("No feature drift detected above the calculated thresholds.")
    return False


def check_for_drift_from_api(model_monitoring_job_name: str) -> bool:
    """
    Checks for drift by searching for alerts from a specific model monitoring job.

    Args:
        model_monitoring_job_name: The resource name of the model monitoring job.

    Returns:
        True if drift is detected, False otherwise.
    """
    logging.info(f"Checking for drift for job '{model_monitoring_job_name}' using search_alerts...")
    
    # projects/{p}/locations/{l}/modelMonitors/{m}/modelMonitoringJobs/{j}
    parts = model_monitoring_job_name.split('/')
    if len(parts) != 8 or parts[4] != "modelMonitors":
        raise ValueError(f"Invalid model_monitoring_job_name format: {model_monitoring_job_name}")
    
    project_id = parts[1]
    location = parts[3]
    monitor_id = parts[5]

    aiplatform.init(project=project_id, location=location)
    monitor = ml_monitoring.ModelMonitor(monitor_id)
    
    alerts = monitor.search_alerts(
        model_monitoring_job_name=model_monitoring_job_name,
        objective_type='raw-feature-drift'
    )

    logging.info(f"search_alerts returned: {alerts}")
    logging.info(f"Type of search_alerts return: {type(alerts)}")

    # The search_alerts method returns a dictionary where the alert objects
    # are in the 'model_monitoring_alerts' key.
    if not alerts or "model_monitoring_alerts" not in alerts or not alerts["model_monitoring_alerts"]:
        logging.info("No alerts found for this monitoring job. No significant drift detected.")
        return False

    drift_found = False
    for alert in alerts["model_monitoring_alerts"]:
        try:
            feature_name = alert.stats_name
            deviation = alert.anomaly.tabular_anomaly.anomaly.number_value
            threshold = alert.anomaly.tabular_anomaly.condition.threshold

            logging.info(f"Checking feature '{feature_name}': Deviation={deviation}, Threshold={threshold}")
            if deviation > threshold:
                logging.warning(
                    f"Drift detected! Feature '{feature_name}' has a deviation of {deviation}, "
                    f"which is above its threshold of {threshold}."
                )
                drift_found = True

        except AttributeError as e:
            logging.warning(f"Could not parse alert structure. Error: {e}. Alert object: {alert}")
            continue

    if not drift_found:
        logging.info("No feature drift detected above thresholds in the found alerts.")
        
    return drift_found


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
    - Parses Pub/Sub message.
    - Checks for model drift using the Vertex AI API or GCS.
    - Triggers a new training pipeline run if drift is detected.
    """
    logging.info(f"start: EventID: {context.event_id}, EventType: {context.event_type}")

    try:
        # 1. Parse and Validate Input
        message = parse_pubsub_message(event)
        
        drift_detected = False
        if message["type"] == "api":
            drift_detected = check_for_drift_from_api(message["job_name"])
        elif message["type"] == "gcs":
            drift_detected = check_for_drift_from_gcs(message["path"])
        else:
            raise ValueError(f"Unknown message type from parser: {message.get('type')}")

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
