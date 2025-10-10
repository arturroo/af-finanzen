import unittest
from unittest.mock import patch, MagicMock
from main import main, start
from datetime import datetime, timedelta, timezone


class TestMain(unittest.TestCase):

    @patch('main.FileContent')
    @patch('main.google.cloud.logging.Client')
    def test_start_success(self, mock_logging_client, mock_file_content):
        event = {
            "attributes": {
                "bucketId": "test-bucket",
                "objectId": "test-object"
            }
        }
        context = MagicMock()
        start(event, context)
        mock_file_content.assert_called_once_with("af-finanzen-banks", "test-object")

    @patch('main.google.cloud.logging.Client')
    def test_start_no_attributes(self, mock_logging_client):
        event = {}
        context = MagicMock()
        with self.assertRaisesRegex(Exception, "start: File in notification not found: 'attributes'"):
            start(event, context)

    @patch('main.start')
    def test_main_success(self, mock_start):
        event = {}
        context = MagicMock()
        context.timestamp = datetime.now(timezone.utc).isoformat()
        main(event, context)
        mock_start.assert_called_once_with(event, context)

    @patch('main.start')
    def test_main_timeout(self, mock_start):
        event = {}
        context = MagicMock()
        context.timestamp = (datetime.now(timezone.utc) - timedelta(minutes=2)).isoformat()
        result = main(event, context)
        self.assertEqual(result, "Trigger timeout")
        mock_start.assert_not_called()

    @patch('main.start', side_effect=Exception("Test Exception"))
    def test_main_exception(self, mock_start):
        event = {}
        context = MagicMock()
        context.timestamp = datetime.now(timezone.utc).isoformat()
        with self.assertRaisesRegex(RuntimeError, "Cloud Function failed"):
            main(event, context)


if __name__ == "__main__":
    unittest.main()