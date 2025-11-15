# Production Monitoring Implementation Plan (Final)

**Objective:** Implement a robust, event-driven, and automated data drift monitoring system for the `transak-i1` model, with monitor creation integrated directly into the training pipeline.

This plan shifts the `ModelMonitor` resource creation into the `pipeline-train`. The monitor is intrinsically tied to a model version, so it will be created only when a new "champion" model is blessed. This ensures each champion has its own version-aware monitor.

---

## 1. How: In-Pipeline Configuration & Event-Driven Triggers

The architecture combines in-pipeline components for setup with an event-driven workflow for execution and automated retraining. The setup components run conditionally to optimize resource usage.

### Step 1a: The Blessing Gate (Conditional Step in `pipeline-train`)
The core of the new design is a conditional gate that executes only if the `bless_or_not_to_bless_op` component decides to promote the challenger model. All monitoring setup steps will be placed inside this condition.

### Step 1b: `create_monitoring_baseline_op` Component (New, in `pipeline-train`)
This component runs *after* a model is blessed. It creates the "golden" baseline dataset required by the `ModelMonitor`.

*   **Action:**
    1.  Takes the newly blessed `champion_model` and the original `train_dataset` as input.
    2.  Runs a **batch prediction job** using the champion model on the training data.
    3.  Outputs a new `monitoring_baseline.csv` artifact. This dataset contains the original features, the ground-truth labels, and the model's own predictions on the training data.
*   **Purpose:** This baseline is crucial for monitoring both **feature drift** and **prediction drift**. Running it conditionally saves costs by not generating baselines for models that are not promoted.

### Step 1c: `setup_monitoring_op` Component (New, in `pipeline-train`)
This component runs immediately after the baseline is created, inside the same conditional block.

*   **Inputs:** The blessed `champion_model` artifact, the `baseline_dataset` artifact, and the resource name of the `NotificationChannel` for the trigger.
*   **Action:** Uses the Python SDK (`vertexai.resources.preview.ml_monitoring.ModelMonitor.create`) to create and configure a new `ModelMonitor` resource specifically for the new model version.
*   **Key Logic:**
    *   Sets drift thresholds for features like `description` and `type`.
    *   Configures the comprehensive `NotificationSpec` to use all three mechanisms:
        *   `notification_channels`: The list of channel resource names that point to the `ps-i1-train` Pub/Sub topic. This is the primary trigger.
        *   `user_emails`: A list of emails for direct human-readable alerts.
        *   `enable_cloud_logging`: Set to `True` to ensure a persistent audit trail of all anomalies is written to Cloud Logging for debugging and historical analysis.

### Step 1d: `run_monitoring_op` Component (in `pipeline-predict`)
This component remains at the end of the prediction pipeline. Its role is to trigger a monitoring job against the newly generated predictions.

*   **Action:** Asynchronously starts a monitoring run for the current production model version.
*   **Logic:** It's a "fire and forget" trigger. It provides the `prediction_dataset` (which contains only features, no ground truth) to the monitoring service and completes. The monitoring job runs separately.

### Step 1e: The Automated Retraining Loop (Direct Notification)
This is the core of the trigger mechanism.

1.  **Notification Channel:** A `google_monitoring_notification_channel` (defined in Terraform) is configured to publish messages to our `ps-i1-train` Pub/Sub topic.
2.  **Pub/Sub Topic:** Receives the anomaly event directly from the `ModelMonitor` via the notification channel.
3.  **Cloud Function:** The `cf-i1-train` function is subscribed to the topic. When it receives the event, it uses the Vertex AI SDK to **launch a new run of the `pipeline-train` pipeline**, closing the loop.

---

## 2. Alerting: A Multi-Layered Strategy

*   **Primary Trigger (for Automation):** The message sent via the `NotificationChannel` to Pub/Sub is the primary event that drives the automated retraining workflow.
*   **Secondary Alert (for Humans):** The `user_emails` parameter provides a direct, human-readable email alert that drift was detected.
*   **Tertiary Record (for Auditing):** `enable_cloud_logging=True` ensures a permanent, queryable log of every anomaly is stored in Cloud Logging for debugging and long-term analysis.

---

## 3. References

*   [Model Monitoring v2 Overview](https://docs.cloud.google.com/vertex-ai/docs/model-monitoring/overview#v2)
*   [Set up Model Monitoring v2](https://docs.cloud.google.com/vertex-ai/docs/model-monitoring/set-up-model-monitoring)
*   [Run a Model Monitoring v2 Job](https://docs.cloud.google.com/vertex-ai/docs/model-monitoring/run-monitoring-job)
*   [Example Notebook: Monitoring for Custom Model Batch Prediction](https://github.com/GoogleCloudPlatform/vertex-ai-samples/blob/main/notebooks/official/model_monitoring_v2/model_monitoring_for_custom_model_batch_prediction_job.ipynb)
*   [SDK Reference: `NotificationSpec`](https://docs.cloud.google.com/python/docs/reference/vertexai/latest/vertexai.resources.preview.ml_monitoring.spec.NotificationSpec)
*   Reference Exampe Model Monitor Configuratioin using Python SDK:
```Python
from vertexai.resources.preview import ml_monitoring
from google.cloud.aiplatform_v1beta1.types import ExplanationSpec, ExplanationParameters, ExplanationMetadata

# Define Monitoring Schema. For AutoML models, this is optional if the schema information is available.
MONITORING_SCHEMA=ml_monitoring.spec.ModelMonitoringSchema(
  feature_fields=[
      ml_monitoring.spec.FieldSchema(
          name="sepal_length_cm",
          data_type="float"
      ),
      ml_monitoring.spec.FieldSchema(
          name="sepal_width_cm",
          data_type="float"
      ),
      ml_monitoring.spec.FieldSchema(
          name="petal_length_cm",
          data_type="float"
      ),
      ml_monitoring.spec.FieldSchema(
          name="petal_width_cm",
          data_type="float"
      )
  ],
  prediction_fields = [
      ml_monitoring.spec.FieldSchema(
          name="predicted_species",
          data_type="categorical"
      )
  ]
)

TRAINING_DATASET = ml_monitoring.spec.MonitoringInput(
  gcs_uri=GCS_INPUT_URI,
  data_format=DATA_FORMAT,
)

DEFAULT_FEATURE_DRIFT_SPEC=ml_monitoring.spec.DataDriftSpec(
  categorical_metric_type="l_infinity",
  numeric_metric_type="jensen_shannon_divergence",
  default_categorical_alert_threshold=0.1,
  default_numeric_alert_threshold=0.1,
)

DEFAULT_PREDICTION_OUTPUT_DRIFT_SPEC=ml_monitoring.spec.DataDriftSpec(
  categorical_metric_type="l_infinity",
  numeric_metric_type="jensen_shannon_divergence",
  default_categorical_alert_threshold=0.1,
  default_numeric_alert_threshold=0.1,
)

DEFAULT_FEATURE_ATTRIBUTION_SPEC=ml_monitoring.spec.FeatureAttributionSpec(
  default_alert_threshold=0.0003,
  feature_alert_thresholds={"sepal_length_cm":0.0001},
)

EXPLANATION_SPEC=ExplanationSpec(
  parameters=ExplanationParameters(
      {"sampled_shapley_attribution": {"path_count": 2}}
  ),
  metadata=ExplanationMetadata(
      inputs={
          "sepal_length_cm": ExplanationMetadata.InputMetadata({
              "input_tensor_name": "sepal_length_cm",
              "encoding": "IDENTITY",
              "modality": "numeric",
          }),
          ...
      },
      ...
  )
)

DEFAULT_OUTPUT_SPEC = ml_monitoring.spec.output.OutputSpec(
  gcs_base_dir=GCS_OUTPUT_BASE_DIR
)

DEFAULT_NOTIFICATION_SPEC = ml_monitoring.spec.NotificationSpec(
  user_emails=['email@example.com']
)

my_model_monitor = ml_monitoring.ModelMonitor.create(
  display_name=MONITORING_JOB_DISPLAY_NAME,
  model_name=MODEL_RESOURCE_NAME,
  model_version_id=MODEL_VERSION_ID,
  model_monitoring_schema=MONITORING_SCHEMA,
  # The following fields are optional for creating the model monitor.
  training_dataset=TRAINING_DATASET,
  tabular_objective_spec=ml_monitoring.spec.TabularObjective(
      feature_drift_spec=DEFAULT_FEATURE_DRIFT_SPEC,
      prediction_output_drift_spec=DEFAULT_PREDICTION_OUTPUT_DRIFT_SPEC,
      feature_attribution_spec=DEFAULT_FEATURE_ATTRIBUTION_SPEC,
  ),
  explanation_spec=DEFAULT_FEATURE_ATTRIBUTION_SPEC,
  output_spec=DEFAULT_OUTPUT_SPEC,
  notification_spec=DEFAULT_NOTIFICATION_SPEC
)
```

*   Reference example configuration of monitoring run using Python SDK
```Python
from vertexai.resources.preview import ml_monitoring

TARGET_DATASET=ml_monitoring.spec.MonitoringInput(
  table_uri=BIGQUERY_URI
)

model_monitoring_job=my_model_monitor.run(
  display_name=JOB_DISPLAY_NAME,
  target_dataset=TARGET_DATASET,
)
```

*   Google Notification Channel Terraform documentation: https://registry.terraform.io/providers/hashicorp/google/4.51.0/docs/resources/monitoring_notification_channel.html
    *   **Type:** `pubsub`
    *   **Topic:** You must provide the topic's full resource ID in the `labels` map. The easiest way to do this is by referencing the `.id` attribute of the topic resource itself.

        **Terraform Example:**
        ```terraform
        # 1. Define the Pub/Sub topic that will receive notifications.
        resource "google_pubsub_topic" "ps_transak_i1_train_trigger" {
          project = var.project_id
          name    = "ps-transak-i1-train-trigger"
        }

        # 2. Define the Notification Channel that points to the Pub/Sub topic.
        resource "google_monitoring_notification_channel" "drift_retraining_channel" {
          project      = var.project_id
          display_name = "Pub/Sub Channel for Model Drift Retraining"
          type         = "pubsub"
        
          labels = {
            topic = google_pubsub_topic.ps_transak_i1_train_trigger.id
          }
        }
        ```




---

## 4. Next Steps for Implementation

1.  **Implement New Training Pipeline Components:**
    *   Create the KFP component `pipelines/components/create_monitoring_baseline.py`.
    *   Create the KFP component `pipelines/components/setup_monitoring.py`.
2.  **Update `pipeline-train`:**
    *   Add a `dsl.Condition` that runs after the `bless_or_not_to_bless_op`.
    *   Inside the condition, chain the following operations: `bless_model_op` -> `create_monitoring_baseline_op` -> `setup_monitoring_op`.
3.  **Update Terraform for Eventing:**
    *   Define the `google_pubsub_topic` for `ps-i1-train`.
    *   Define a `google_monitoring_notification_channel` that points to the Pub/Sub topic.
4.  **Implement `run_monitoring_op` and Trigger Logic:**
    *   Create the `pipelines/components/run_monitoring.py` component.
    *   Modify `pipelines/pipeline_predict.py` to use `run_monitoring_op` at the end.
    *   Create the `cloud_functions/cf-i1-train/` directory and code.
    *   Add the Terraform definition for the trigger Cloud Function.

---

## 5. Future Work (Out of Scope for Now)

*   **Pipeline Observability:** Implement a `google_logging_metric` to count the executions of the `pipeline-train`. Create a `google_monitoring_alert_policy` to trigger a notification if the pipeline hasn't run in an expected timeframe (e.g., more than 3 months), which could indicate a silent failure in the trigger mechanism. This metric can also be used on a Cloud Monitoring Dashboard to visualize pipeline activity.
