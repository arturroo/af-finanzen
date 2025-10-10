__author__ = "Artur Fejklowicz"
__copyright__ = "Copyright 2023, The AF Finanzen Project"
__credits__ = ["Artur Fejklowicz"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Artur Fejklowicz"
__status__ = "Production"

from google.cloud import storage
import google.cloud.logging
import logging
import backoff
from functools import singledispatch
from typing import overload


class FileContent:
    bucket: google.cloud.storage.Bucket
    bucket_id: str
    object_id: str
    object_id_transformed: str
    content_raw: str
    content: list
    year: str
    month: str

    def __init__(self, bucket_id, object_id):
        self.bucket_id = bucket_id
        self.object_id = object_id
        self.year = ""
        self.month = ""
        self._initialize_bucket()
        self._load_blob()
        self.content = self.content_raw.split("\n")
        self.extract_date()
        log_client = google.cloud.logging.Client()
        log_client.setup_logging()
        logging.getLogger("backoff").addHandler(logging.StreamHandler())
        logging.basicConfig(level=logging.INFO)


    def _get_content(self):
        return f"\n".join(self.content)

    def transform(self, target: str = None):
        """
        Transforms the file content
        :param target: type of transformation
        :return: self
        """
        logging.info(f"transform: start target {target}")
        print(f"transform: start target {target}")

        if target == "first_line":
            self.content = self.content[1:]
        elif target == "end_of_file":
            self.content = self.content[:-3]
        else:
            raise Exception(f"transform: Unknown target {target}")

        return self

    def extract_date(self):
        """
        Extracts the date from the file content
        :return: self
        """
        logging.info(f"extract_date: start")
        print(f"extract_date: start")

        if len(self.content) > 1:
            first_data_row = self.content[1]
            if len(first_data_row.split(";")) > 3:
                einkaufsdatum = first_data_row.split(";")[3]
                if len(einkaufsdatum.split(".")) > 2:
                    self.year = einkaufsdatum.split(".")[2]
                    self.month = einkaufsdatum.split(".")[1]
                    print(f"extract_date: year {self.year} month {self.month}")

        return self

    @backoff.on_exception(backoff.expo, Exception, max_time=60, max_tries=3)
    def _initialize_bucket(self):
        self.bucket = storage.Client().bucket(self.bucket_id)

    @backoff.on_exception(backoff.expo, Exception, max_time=60, max_tries=3)
    def _load_blob(self):
        """
        Loads the Blob from Google Storage
        :param bucket_id: ID of the bucket where the data is stored
        :param object_id: File name
        :return: File content as string
        """

        try:
            blob = self.bucket.blob(self.object_id)
            self.content_raw = blob.download_as_text(encoding="windows-1252")
        except Exception as e:
            logging.error(f"Could not load the Blob from Google Storage {self.object_id}: {e}")
            raise RuntimeError(f"Could not load the Blob from Google Storage {self.object_id}: {e}")

    @backoff.on_exception(backoff.expo, Exception, max_time=60, max_tries=3)
    def save_blob(self):
        """
        Saves the Blob to Google Storage to file name pattern:
        gs://af-finanzen-banks/ubs/Monat=YYYY-mm/ubs_YYYY-mm_transactions.csv
        :return: File content as string
        """
        self.object_id_transformed = f"ubs/Monat={self.year}-{self.month}/ubs_{self.year}-{self.month}_transactions.csv"
        try:
            blob = self.bucket.blob(self.object_id_transformed)
            blob.upload_from_string(self._get_content().encode('latin1'))
        except Exception as e:
            logging.error(f"Could not save the Blob to Google Storage {self.object_id_transformed}: {e}")
            raise RuntimeError(f"Could not save the Blob to Google Storage {self.object_id_transformed}: {e}")

        return self