import unittest
from unittest.mock import patch, MagicMock
from FileContent import FileContent


class TestFileContent(unittest.TestCase):

    def setUp(self):
        self.bucket_id = "af-finanzen-banks"
        self.object_id = "ubs/Monat=2023-01/ubs_2023-01_transactions.csv"
        self.mock_data = "Einkaufsdatum;Belegnummer;Buchungsdatum;Konto;IBAN;BIC;Betrag;Währung;Verwendungszweck\n01.01.2023;1234567890;01.01.2023;01.01.2023;DE89370400440532013000;INGDIBA;100,00;EUR;Test\n02.01.2023;9876543210;02.01.2023;02.01.2023;DE89370400440532013000;INGDIBA;-100,00;EUR;Test"

        # Create a mock for the storage client
        self.mock_storage_client = MagicMock()
        self.mock_bucket = MagicMock()
        self.mock_blob = MagicMock()
        self.mock_storage_client.bucket.return_value = self.mock_bucket
        self.mock_bucket.blob.return_value = self.mock_blob
        self.mock_blob.download_as_text.return_value = self.mock_data

        # Patch the storage and logging clients
        self.patcher_storage = patch('FileContent.storage.Client', return_value=self.mock_storage_client)
        self.patcher_logging = patch('google.cloud.logging.Client')
        self.mock_storage = self.patcher_storage.start()
        self.mock_logging = self.patcher_logging.start()

    def tearDown(self):
        self.patcher_storage.stop()
        self.patcher_logging.stop()

    def test_init(self):
        file_content = FileContent(self.bucket_id, self.object_id)
        self.assertEqual(file_content.bucket_id, self.bucket_id)
        self.assertEqual(file_content.object_id, self.object_id)
        self.assertEqual(file_content.content_raw, self.mock_data)
        self.assertEqual(file_content.year, "2023")
        self.assertEqual(file_content.month, "01")

    def test_transform_first_line(self):
        file_content = FileContent(self.bucket_id, self.object_id)
        file_content.transform(target="first_line")
        expected_content = ["01.01.2023;1234567890;01.01.2023;01.01.2023;DE89370400440532013000;INGDIBA;100,00;EUR;Test", "02.01.2023;9876543210;02.01.2023;02.01.2023;DE89370400440532013000;INGDIBA;-100,00;EUR;Test"]
        self.assertEqual(file_content.content, expected_content)

    def test_transform_end_of_file(self):
        file_content = FileContent(self.bucket_id, self.object_id)
        file_content.transform(target="end_of_file")
        expected_content = []
        self.assertEqual(file_content.content, expected_content)

    def test_transform_unknown(self):
        file_content = FileContent(self.bucket_id, self.object_id)
        with self.assertRaisesRegex(Exception, "transform: Unknown target unknown"):
            file_content.transform(target="unknown")

    def test_extract_date_no_date(self):
        self.mock_blob.download_as_text.return_value = "no_date_here"
        file_content = FileContent(self.bucket_id, self.object_id)
        self.assertEqual(file_content.year, "")
        self.assertEqual(file_content.month, "")

    def test_save_blob(self):
        file_content = FileContent(self.bucket_id, self.object_id)
        file_content.save_blob()
        self.mock_bucket.blob.assert_called_with("ubs/Monat=2023-01/ubs_2023-01_transactions.csv")
        self.mock_blob.upload_from_string.assert_called_with(file_content._get_content().encode('latin1'))


if __name__ == "__main__":
    unittest.main()