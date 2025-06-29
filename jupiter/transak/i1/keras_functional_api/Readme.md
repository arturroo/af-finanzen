gcloud services enable artifactregistry.googleapis.com
gcloud artifacts repositories create af-finanzen-mlops \
  --repository-format=docker \
  --location=europe-west6 \
  --description="Docker repository for AF Finanzen MLOps projects"

gcloud builds submit --region="europe-west1" --tag="europe-west6-docker.pkg.dev/af-finanzen/af-finanzen-mlops/i1-transaction-trainer:latest" .