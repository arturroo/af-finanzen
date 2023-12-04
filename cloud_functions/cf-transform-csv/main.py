__author__ = "Artur Fejklowicz"
__copyright__ = "Copyright 2023, The AF Finanzen Project"
__credits__ = ["Artur Fejklowicz"]
__license__ = "GPLv3"
__version__ = "0.0.1"
__maintainer__ = "Artur Fejklowicz"
__status__ = "Production"

import logging
import traceback
import backoff

import google.cloud.logging
from google.cloud import storage
from google.cloud import logging
from dateutil import parser
from datetime import datetime, timezone


# Cloud logger
log_client = google.cloud.logging.Client()
log_client.setup_logging()

# Get logger
logging.getLogger("backoff").addHandler(logging.StreamHandler())
logging.basicConfig(level=logging.INFO)


def start(event, context):


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
        logging.info(f"Clould not trigger Cloud Function for last 1 minute. Stopping retry. Dropped {context.event_id} "
                     f"with age {event_age_ms}ms", extra={"labels": {"dst": "USER"}}
                     )
        return "Trigger timeout"

    try:
        start(event, context)
    except Exception:
        logging.error(traceback.format_exc())
        raise RuntimeError("Cloud Function failed")
