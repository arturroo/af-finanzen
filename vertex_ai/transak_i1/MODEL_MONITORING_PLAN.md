# Production Monitoring Implementation Plan (Revised)

**Objective:** Implement a robust, event-driven, and automated data drift monitoring system for the `transak-i1` model.

This revised plan reflects new findings: the specific `ModelMonitor` resource is not supported by Terraform, and the retraining trigger must be event-driven. The new architecture uses a Python script for configuration and a Logging/Pub/Sub/Cloud Function chain for automation.

---

## 1. What: Configuration with a Python Script

Since Terraform does not support the `ModelMonitor` resource directly, we will adopt a "configuration-as-code" approach using a dedicated Python script and a JSON configuration file.

### `monitoring_config.json` (New File)
This file will store the monitoring parameters, making them easy to view and modify without changing code.

```json
{
  "project_id": "af-finanzen",
  "location": "europe-west6",
  "model_name": "transak-i1-train-model",
  "monitoring_job_display_name": "transak_i1_data_drift_monitor",
  "notification_channels": [],
  "drift_thresholds": {
    "description": 0.3,
    "type": 0.3
  },
  "log_anomalies": true
}
```

### `setup_monitoring.py` (New File)
This script will be created in `vertex_ai/transak_i1/` to create or update the monitoring job.

*   **Action:** Reads `monitoring_config.json` and uses the Python SDK (`aiplatform.ModelMonitor.create`) to configure the monitoring job.
*   **Key Logic:**
    *   It will set the drift thresholds for `description` and `type`.
    *   Crucially, it will enable anomaly logging (`log_anomalies: true`) to allow for event-driven triggers.
    *   It can also be configured to send direct email notifications in parallel to the logging.

---

## 2. How: Event-Driven Integration

We will create a fully event-driven workflow to connect the monitoring job to the training pipeline. This is robust and solves the issue of the prediction pipeline finishing before monitoring is complete.

### Step 2a: `run_monitoring_op` Component (in `pipeline-predict`)
The role of this component in `pipelines/components/run_monitoring.py` is now much simpler.

*   **Action:** At the end of the prediction pipeline, it asynchronously starts a monitoring run using the Python SDK.
*   **Logic:** It is now a "fire and forget" trigger. It does not wait or output results. The prediction pipeline can safely terminate after this step.

### Step 2b: Logging Sink and Pub/Sub Topic (in Terraform)
We will add these resources to our existing Terraform configuration (`terraform/main.tf`).

1.  **`google_pubsub_topic`:** Create a new topic named `ps-transak-i1-train-trigger`.
2.  **`google_logging_project_sink`:** Create a new sink that:
    *   **Filters:** Selects only the log entries from Vertex AI that correspond to our model's drift anomalies.
    *   **Destination:** Forwards these specific log entries as messages to `ps-transak-i1-train-trigger`.

### Step 2c: `cf-trigger-retraining` Cloud Function (in Terraform & `cloud_functions/`)
A new, small Cloud Function will be the final link in the chain.

*   **Trigger:** It will be event-driven, executing whenever a message arrives on `ps-transak-i1-train-trigger`.
*   **Source Code:** A new directory `cloud_functions/cf-transak-i1-train-trigger/` will be created.
*   **Logic:**
    1.  The function will parse the incoming Pub/Sub message (which contains the log data).
    2.  It will verify that the message indicates a true data drift has been detected.
    3.  If drift is confirmed, it will use the Vertex AI SDK to **launch a new run of the `pipeline-train` pipeline**.

---

## 3. Alerting: Dual-Channel Notifications

*   **Primary Alert (for Automation):** The Logging Sink -> Pub/Sub message is the primary "alert" that drives the automated retraining workflow.
*   **Secondary Alert (for Humans):** We can still configure the `ModelMonitor` (in `setup_monitoring.py`) to send a direct email notification to you. This provides a simple, human-readable alert that drift was detected and the automated retraining process has been initiated.

---

## 4. References

*   [Model Monitoring v2 Overview](https://docs.cloud.google.com/vertex-ai/docs/model-monitoring/overview#v2)
*   [Set up Model Monitoring v2](https://docs.cloud.google.com/vertex-ai/docs/model-monitoring/set-up-model-monitoring)
*   [Run a Model Monitoring v2 Job](https://docs.cloud.google.com/vertex-ai/docs/model-monitoring/run-monitoring-job)
*   [Example Notebook: Monitoring for Custom Model Batch Prediction](https://github.com/GoogleCloudPlatform/vertex-ai-samples/blob/main/notebooks/official/model_monitoring_v2/model_monitoring_for_custom_model_batch_prediction_job.ipynb)

---

## 5. Next Steps for Implementation

1.  **Create Configuration Files:**
    *   Create `vertex_ai/transak_i1/monitoring/config.json`.
    *   Create `vertex_ai/transak_i1/monitoring/setup.py` to provision the `ModelMonitor` resource.
2.  **Update Terraform for Eventing:**
    *   In `terraform/main.tf`, add a `google_pubsub_topic` resource for `ps-transak-i1-train-trigger`.
    *   In `terraform/main.tf`, add a `google_logging_project_sink` resource to route drift anomaly logs to the new Pub/Sub topic.
3.  **Implement Pipeline Changes:**
    *   Create the new KFP component `pipelines/components/run_monitoring.py`.
    *   Modify `pipelines/pipeline_predict.py` to use the new `run_monitoring_op` at the end of the pipeline.
4.  **Implement the Trigger Logic:**
    *   Create the directory and source code for the new Cloud Function: `cloud_functions/cf-transak-i1-train-trigger/main.py` and its `requirements.txt`.
    *   Add the Terraform definition for this new Cloud Function.
