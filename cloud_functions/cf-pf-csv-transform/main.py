__author__ = "Artur Fejklowicz"
__copyright__ = "Copyright 2026, The AF Finanzen Project"
__credits__ = ["Artur Fejklowicz"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Artur Fejklowicz"
__status__ = "Production"

import google.cloud.logging
import logging
import traceback
import functions_framework
import google.cloud.logging
import logging
import traceback
import base64
import json
from FileContent import FileContent

# Cloud logger
log_client = google.cloud.logging.Client()
log_client.setup_logging()

# Get logger
logging.getLogger("backoff").addHandler(logging.StreamHandler())
logging.basicConfig(level=logging.INFO)

BUCKET_ID = "af-finanzen-banks"


def process_file(bucket_id, object_id):
    logging.info(f"process_file: File gs://{bucket_id}/{object_id} triggered", extra={"labels": {"dst": "USER"}})
    
    # We only want to process files in the raw/postfinance/ directory
    if "raw/postfinance/" not in object_id:
        logging.info(f"process_file: Skipping file {object_id} as it is not in raw/postfinance/", extra={"labels": {"dst": "USER"}})
        return

    file_content = FileContent(bucket_id, object_id)
    file_content \
        .transform(target="pf_header_strip")\
        .transform(target="pf_footer_strip")\
        .extract_date()\
        .save_blob()

    logging.info(f"process_file: file {object_id} transformed and saved")


@functions_framework.cloud_event
def main(cloud_event):
    """
    Cloud Function entry point for Gen 2 (CloudEvent).
    """
    try:
        # Gen 2 / CloudRun Pub/Sub events wrap the message in the data field
        # The data field matches the PubsubMessage format: https://cloud.google.com/pubsub/docs/reference/rest/v1/PubsubMessage
        
        event_data = cloud_event.data
        
        # Validation checks
        if "message" not in event_data:
             logging.warning("No 'message' field in CloudEvent data.")
             # In some direct invocation cases or different event types, structure might vary. 
             # For Pub/Sub trigger, it should be there.
             # If strictly Pub/Sub, we might expect 'message'.
             
        # The Pub/Sub message data is base64 encoded
        if "message" in event_data and "data" in event_data["message"]:
             pubsub_message = base64.b64decode(event_data["message"]["data"]).decode('utf-8')
             # The GCS notification sends a JSON payload in the Pub/Sub message
             # Structure: { "bucket": "...", "name": "..." }
             msg_json = json.loads(pubsub_message)
             bucket_id = msg_json.get("bucket")
             object_id = msg_json.get("name")
             
             if not bucket_id or not object_id:
                  raise ValueError("Bucket or object ID missing in Pub/Sub message payload")
                  
             process_file(bucket_id, object_id)

    except Exception:
        logging.error(traceback.format_exc())
        raise RuntimeError("Cloud Function failed")
