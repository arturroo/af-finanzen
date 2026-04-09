# Cloud Function: cf-i1-train

This Cloud Function is responsible for triggering the Vertex AI training pipeline (`transak-i1-train`) when data drift is detected either via GCS payloads or Vertex AI Model Monitoring.

## Manually Triggering the Training Pipeline

If you need to manually force the training pipeline to run by simulating a model monitoring alert, you can publish a message to the `ps-i1-train` Pub/Sub topic matching the API event structure.

The payload requires a valid `model_monitoring_job_name` from a prior pipeline execution that actually detected drift.

### 1. Finding the Anomaly Details
You can find the drift anomaly details at the output of the prediction pipeline (`transak-i1-predict`). Look for the **last artifact from the monitoring execution step**. It will be a file named something like `anomalies...json`.

From that file's name, you can extract the required IDs. For example, if your file is named:
`..._model_monitoring_3188830011155021824_tabular_jobs_2855985851194671104_feature_drift_anom.json`

The IDs are:
* **Model Monitor ID**: `3188830011155021824`
* **Model Monitoring Job ID**: `2855985851194671104`

### 2. Triggering via Bash (WSL, Linux, macOS)

Due to how Windows PowerShell handles string passing to external CLI programs, it strongly strips necessary JSON quotes from the payload. We highly recommend using a bash terminal (like WSL) instead.

Run the following simple command in your bash terminal to publish the message:

```bash
gcloud pubsub topics publish ps-i1-train \
  --message='{"subject":"Vertex AI Model Monitoring Job anomalies detected","details":{"model_monitoring_job_name":"projects/819397114258/locations/europe-west6/modelMonitors/3188830011155021824/modelMonitoringJobs/2855985851194671104"}}' \
  --project=af-finanzen
```
