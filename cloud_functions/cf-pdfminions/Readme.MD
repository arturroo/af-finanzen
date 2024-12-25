## Example call:
Using gcloud functions call (CLI):
```Bash
gcloud functions call cf-pdfminions \
  --project=af-finanzen \
  --region=europe-west6 \
  --data='{"gs_path": "gs://{bucket_name}/{pdf_file_object_name.pdf"}'
```