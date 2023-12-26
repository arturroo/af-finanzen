import FileContent
import unittest

#from FileContent import FileContent


class TestFileContent(unittest.TestCase):

    def __init__(self):
        super().__init__()
        self.maxDiff = None



    def test_init(self):
        bucket_id = "af-finanzen-banks"
        object_id = "ubs/Monat=2023-01/ubs_2023-01_transactions.csv"
        file_content = FileContent(bucket_id, object_id)

        self.assertEqual(file_content.bucket_id, bucket_id)
        self.assertEqual(file_content.object_id, object_id)
        self.assertEqual(file_content.content_raw, "")
        self.assertEqual(file_content.content, [])
        self.assertEqual(file_content.year, "")
        self.assertEqual(file_content.month, "")

    def test_load_blob(self):
        bucket_id = "af-finanzen-banks"
        object_id = "ubs/Monat=2023-01/ubs_2023-01_transactions.csv"
        file_content = FileContent(bucket_id, object_id)
        file_content._load_blob()

        self.assertEqual(file_content.content_raw, "Einkaufsdatum;Belegnummer;Buchungsdatum;Konto;IBAN;BIC;Betrag;Währung;Verwendungszweck\n01.01.2023;1234567890;01.01.2023;12345678901234567890;DE89370400440532013000;INGDIBA;100,00;EUR;Test\n02.01.2023;9876543210;02.01.2023;98765432109876543210;DE89370400440532013000;INGDIBA;-100,00;EUR;Test")
        self.assertEqual(file_content.content, ["Einkaufsdatum;Belegnummer;Buchungsdatum;Konto;IBAN;BIC;Betrag;Währung;Verwendungszweck", "01.01.2023;1234567890;01.01.2023;12345678901234567890;DE89370400440532013000;INGDIBA;100,00;EUR;Test", "02.01.2023;9876543210;02.01.2023;98765432109876543210;DE89370400440532013000;INGDIBA;-100,00;EUR;Test"])
        self.assertEqual(file_content.year, "2023")
        self.assertEqual(file_content.month, "01")

    def test_transform(self):
        bucket_id = "af-finanzen-banks"
        object_id = "ubs/Monat=2023-01/ubs_2023-01_transactions.csv"
        file_content = FileContent(bucket_id, object_id)
        file_content._load_blob()
        file_content.transform("first_line")

        self.assertEqual(file_content.content, ["Buchungsdatum;Konto;IBAN;BIC;Betrag;Währung;Verwendungszweck"])

    def test_extract_date(self):
        bucket_id = "af-finanzen-banks"
        object_id = "ubs/Monat=2023-01/ubs_2023-01_transactions.csv"
        file_content = FileContent(bucket_id, object_id)
        file_content._load_blob()
        file_content.extract_date()

        self.assertEqual(file_content.year, "2023")
        self.assertEqual(file_content.month, "01")

    def test_save_blob(self):
        bucket_id = "af-finanzen-banks"
        object_id = "ubs/Monat=2023-01/ubs_2023-01_transactions.csv"
        file_content = FileContent(bucket_id, object_id)
        file_content._load_blob()
        file_content.transform("first_line")
        file_content.extract_date()
        file_content.save_blob()

        blob = file_content.bucket.blob(file_content.object_id_transformed)
        content = blob.download_as_text(encoding="windows-1252")

        self.assertEqual(content, "Buchungsdatum;Konto;IBAN;BIC;Betrag;Währung;Verwendungszweck")

if __name__ == "__main__":
    unittest.main()