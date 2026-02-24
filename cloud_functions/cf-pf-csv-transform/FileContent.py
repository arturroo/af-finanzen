__author__ = "Artur Fejklowicz"
__copyright__ = "Copyright 2026, The AF Finanzen Project"
__credits__ = ["Artur Fejklowicz"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Artur Fejklowicz"
__status__ = "Production"

from google.cloud import storage
import google.cloud.logging
import logging
import backoff
import re

# Cloud logger
log_client = google.cloud.logging.Client()
log_client.setup_logging()

# Get logger
logging.getLogger("backoff").addHandler(logging.StreamHandler())
logging.basicConfig(level=logging.INFO)


class FileContent:
    bucket: google.cloud.storage.Bucket
    bucket_id: str
    object_id: str
    object_id_transformed: str
    content_raw: str
    content: list
    year: str
    month: str
    account: str

    def __init__(self, bucket_id, object_id):
        self.bucket_id = bucket_id
        self.object_id = object_id
        self._initialize_bucket()
        self._load_blob()
        # PostFinance CSVs are often iso-8859-1 or windows-1252 encoded
        # We will split by new lines.
        self.content = self.content_raw.splitlines()
        self.account = "unknown"

    def _get_content(self):
        return "\n".join(self.content)

    def transform(self, target: str = None):
        """
        Transforms the file content
        :param target: type of transformation
        :return: self
        """
        logging.info(f"transform: start target {target}")
        
        if target == "pf_header_strip":
            # Extract account from metadata before stripping (usually line 4)
            # Konto:;="CHCC090000001612XXXXC" (No spaces in source)
            for line in self.content[:6]:
                if line.startswith("Konto:"):
                    match = re.search(r'="(.+?)"', line)
                    if match:
                        # Keep full IBAN exactly as source (Upper Case) for copy-paste friendliness
                        self.account = match.group(1)
                        logging.info(f"transform: Identified full IBAN account as {self.account}")

            # Skip the first 6 lines (metadata)
            # Line 7 is usually the header row for the data
            if len(self.content) > 6:
                self.content = self.content[6:]
            else:
                 logging.warning("File has fewer than 6 lines, cannot strip header correctly.")

            # Filter out any completely empty lines to avoid parsing errors
            self.content = [line for line in self.content if line.strip() != ""]

        elif target == "pf_footer_strip":
            # Remove "Disclaimer", "Der Dokumentinhalt", and empty lines at the end
            while self.content and (self.content[-1].strip() == "" or self.content[-1].startswith("Disclaimer") or self.content[-1].startswith("Der Dokumentinhalt")):
                self.content.pop()
                
        else:
            raise Exception(f"transform: Unknown target {target}")

        return self

    def extract_date(self):
        """
        Extracts the date from the file content.
        Assumes the file has been stripped of the 6 metadata lines.
        So self.content[0] is the header, self.content[1] is the first transaction.
        
        PostFinance format usually has the date in the first few columns.
        E.g., Buchungsdatum;Valuta;Text;Gutschrift;Lastschrift;Saldo
        2023-01-31;...
        
        We need to identify the column index for the date.
        """
        logging.info("extract_date: start")

        if len(self.content) < 2:
             raise Exception("File content is too short to extract date.")

        # Let's inspect the header to find the date column if possible, or assume column 0
        header_row = self.content[0]
        # Detect delimiter
        delimiter = ";" if ";" in header_row else ","
        
        # We check the first data row
        first_data_row = self.content[1]
        columns = first_data_row.split(delimiter)
        
        # Usually 'Buchungsdatum' is the first column (index 0) or 'Valuta' (index 1)
        # We will try to parse the first column
        date_str = columns[0].replace('"', '') # Clean quotes if present
        
        try:
            # format often YYYY-MM-DD or DD.MM.YYYY
            # We treat it as YYYY-MM-DD based on typical exports, or use dateutil to be safe?
            # Creating a robust parser for YYYY-MM-DD or DD.MM.YYYY
            if "-" in date_str:
                # YYYY-MM-DD
                parts = date_str.split("-")
                self.year = parts[0]
                self.month = parts[1]
            elif "." in date_str:
                # DD.MM.YYYY
                parts = date_str.split(".")
                self.year = parts[2]
                self.month = parts[1]
            else:
                 raise ValueError(f"Unknown date format: {date_str}")
                 
        except Exception as e:
             logging.error(f"Could not extract date from row: {first_data_row}. Error: {e}")
             raise

        logging.info(f"extract_date: year {self.year} month {self.month}")
        return self

    @backoff.on_exception(backoff.expo, Exception, max_time=60, max_tries=3)
    def _initialize_bucket(self):
        self.bucket = storage.Client().bucket(self.bucket_id)

    @backoff.on_exception(backoff.expo, Exception, max_time=60, max_tries=3)
    def _load_blob(self):
        """
        Loads the Blob from Google Storage
        :return: File content as string
        """
        try:
            blob = self.bucket.blob(self.object_id)
            # Try decoding with common encodings
            content_bytes = blob.download_as_bytes()
            try:
                self.content_raw = content_bytes.decode('utf-8')
            except UnicodeDecodeError:
                self.content_raw = content_bytes.decode('windows-1252')
                
        except Exception as e:
            logging.error(f"Could not load the Blob from Google Storage {self.object_id}: {e}")
            raise RuntimeError(f"Could not load the Blob from Google Storage {self.object_id}: {e}")

    @backoff.on_exception(backoff.expo, Exception, max_time=60, max_tries=3)
    def save_blob(self):
        """
        Saves the Blob to Google Storage to file name pattern:
        gs://af-finanzen-banks/postfinance/month=YYYYMM/account=chxxx/pf_YYYYMM_chxxx.csv
        """
        if not self.year or not self.month:
            raise ValueError("Year or Month not set. Cannot save.")
            
        month_str = f"{self.year}{self.month}" # YYYYMM format
        self.object_id_transformed = f"postfinance/month={month_str}/account={self.account}/pf_{month_str}_{self.account}.csv"
        
        try:
            blob = self.bucket.blob(self.object_id_transformed)
            blob.upload_from_string(self._get_content().encode('utf-8')) # Save as UTF-8
        except Exception as e:
            logging.error(f"Could not save the Blob to Google Storage {self.object_id_transformed}: {e}")
            raise RuntimeError(f"Could not save the Blob to Google Storage {self.object_id_transformed}: {e}")

        return self
