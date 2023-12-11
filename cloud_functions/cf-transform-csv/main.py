__author__ = "Artur Fejklowicz"
__copyright__ = "Copyright 2023, The AF Finanzen Project"
__credits__ = ["Artur Fejklowicz"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Artur Fejklowicz"
__status__ = "Production"

import google.cloud.logging
import logging
import traceback
import backoff
from dateutil import parser
from datetime import datetime, timezone
from FileContent import FileContent


# Cloud logger
log_client = google.cloud.logging.Client()
log_client.setup_logging()

# Get logger
logging.getLogger("backoff").addHandler(logging.StreamHandler())
logging.basicConfig(level=logging.INFO)

BUCKET_ID = "af-finanzen-banks"


def start(event, context):
    try:
        attributes = event["attributes"]
        bucket_id = attributes["bucketId"]
        object_id = attributes["objectId"]
    except KeyError as e:
        logging.error(f"start: File details in notification not found: {e}")
        raise Exception(f"start: File in notification not found: {e}")

    logging.info(f"start: File gs://{bucket_id}/{object_id} triggered", extra={"labels": {"dst": "USER"}})
    file_content = FileContent(BUCKET_ID, object_id)
    file_content \
        .transform(target="first_line")\
        .transform(target="end_of_file")\
        .extract_date()\
        .save_blob()

    logging.info(f"start: file {object_id} transformed and saved")
    print(f"start: file {object_id} transformed and saved")


def main(event, context):
    """to avoid infinite retry loops, timeout set to 60s
    """
    timestamp = context.timestamp
    event_time = parser.parse(timestamp)
    event_age = (datetime.now(timezone.utc) - event_time).total_seconds()
    event_age_ms = event_age * 1000

    # Ignore events that are too old
    max_age_ms = 60 * 1000
    if event_age_ms > max_age_ms:
        logging.info(f"Clould not trigger Cloud Function for last 1 minute. Stopping retry. "
                     f"Dropped {context.event_id} with age {event_age_ms}ms",
                     extra={"labels": {"dst": "USER"}}
                     )
        return "Trigger timeout"

    try:
        start(event, context)
    except Exception:
        logging.error(traceback.format_exc())
        raise RuntimeError("Cloud Function failed")
