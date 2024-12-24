## Example call:
Using gcloud functions call (CLI):
```Bash
gcloud functions call cf-pdfminions \
  --project=af-finanzen \
  --region=europe-west6 \
  --data='{"gs_path": "gs://af-finanzen-banks/raw/zak/Kontoauszug Nov. 2024.pdf"}'
```