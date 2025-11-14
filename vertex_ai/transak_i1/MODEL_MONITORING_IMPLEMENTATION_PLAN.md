# Model Monitoring Implementation Plan

### **1. Proposed Strategic Approach**

The implementation will be organized into three distinct epics, each with user stories and specific, actionable tasks.

---

#### **Epic 1: Enhance Training Pipeline with Monitoring Setup**
*This epic focuses on integrating the monitor creation and configuration directly into the training pipeline.*

*   **User Story 1.1:** As an MLOps Engineer, I want a component that can process batch prediction results into a monitoring baseline dataset.
    *   **Task 1.1.1:** Create the KFP component file: `vertex_ai/transak_i1/pipelines/components/create_monitoring_baseline.py`.
    *   **Task 1.1.2:** Implement the component's Python logic to accept a batch prediction artifact as input. The logic will parse the prediction results (which include the original features), calculate the predicted class, and output a final `monitoring_baseline.csv` file.
    *   **Note:** This component does not run the batch prediction job itself. It processes the results from a separate `batch_predict_op` call that will be added to the main pipeline.

*   **User Story 1.2:** As an MLOps Engineer, I want to programmatically create a `ModelMonitor` resource for each new champion model so that every production model version is actively monitored.
    *   **Task 1.2.1:** Create the KFP component file: `vertex_ai/transak_i1/pipelines/components/setup_monitoring.py`.
    *   **Task 1.2.2:** Implement the component's Python logic to accept a model artifact, a baseline dataset artifact, and a notification channel resource name.
    *   **Task 1.2.3:** The component logic must use the Vertex AI SDK to create a `ModelMonitor`, configuring its `NotificationSpec` with `user_emails`, `notification_channels`, and `enable_cloud_logging=True`.

*   **User Story 1.3:** As an MLOps Engineer, I want to orchestrate the new monitoring components within the training pipeline so that the setup is fully automated and conditional.
    *   **Task 1.3.1:** Modify `vertex_ai/transak_i1/pipelines/pipeline_train.py` to import the `create_monitoring_baseline_op` and `setup_monitoring_op`.
    *   **Task 1.3.2:** In the pipeline definition, add a `dsl.Condition` that executes only if the model is blessed.
    *   **Task 1.3.3:** Within this condition, chain the component calls: `bless_model_op` -> `create_monitoring_baseline_op` -> `setup_monitoring_op`, ensuring outputs are correctly passed as inputs.

---

#### **Epic 2: Implement the Automated Retraining Trigger Infrastructure**
*This epic focuses on provisioning the cloud resources required for the event-driven trigger.*

*   **User Story 2.1:** As an MLOps Engineer, I want to provision the necessary cloud infrastructure for an event-driven trigger so that drift detection events can be reliably routed.
    *   **Task 2.1.1:** In a suitable Terraform file (e.g., `terraform/main.tf`), define a `google_pubsub_topic` resource named `ps-i1-train`.
    *   **Task 2.1.2:** In the same file, define a `google_monitoring_notification_channel` resource that is configured to publish to the new Pub/Sub topic.

*   **User Story 2.2:** As an MLOps Engineer, I want a serverless function that triggers a new training pipeline run in response to a drift event.
    *   **Task 2.2.1:** Create the directory `cloud_functions/cf-i1-train/` containing `main.py` and `requirements.txt`.
    *   **Task 2.2.2:** Implement the Python logic in `main.py` to parse the incoming Pub/Sub message and use the Vertex AI SDK to launch a new run of the training pipeline.
    *   **Task 2.2.3:** In Terraform, add a module call to deploy the `cf-i1-train` function, configuring its event trigger to be the `ps-i1-train` topic.

---

#### **Epic 3: Enable Monitoring Execution in the Prediction Pipeline**
*This epic focuses on triggering the monitoring job after new predictions are made.*

*   **User Story 3.1:** As an MLOps Engineer, I want to initiate a model monitoring job after each prediction run so that new data is actively checked for drift.
    *   **Task 3.1.1:** Create the KFP component file: `vertex_ai/transak_i1/pipelines/components/run_monitoring.py`.
    *   **Task 3.1.2:** Implement the component's Python logic to start a monitoring job asynchronously.
    *   **Task 3.1.3:** Modify `vertex_ai/transak_i1/pipelines/pipeline_predict.py` to import and call the `run_monitoring_op` as the final step in the pipeline.

### **2. Verification Strategy**

The success of this implementation will be verified through a full end-to-end test:
1.  **Pipeline Execution:** Successfully execute the modified `pipeline-train`. Verify that a new `ModelMonitor` resource is created in the GCP console, visible under Vertex AI Model Monitoring.
2.  **Monitoring Job Trigger:** Successfully execute the modified `pipeline-predict`. Verify that a new monitoring job is listed in the console and runs to completion.
3.  **End-to-End Trigger:**
    a. Prepare a prediction dataset with artificially induced drift.
    b. Execute the `pipeline-predict` with this dataset.
    c. **Observe:** The monitoring job should detect the drift and send an anomaly alert.
    d. **Verify:** The `cf-i1-train` Cloud Function should execute (visible in its logs).
    e. **Confirm:** A new run of the `pipeline-train` must appear automatically in the Vertex AI Pipelines UI.

### **3. Anticipated Challenges & Considerations**

*   **IAM Permissions:** The primary challenge will be identifying and granting the correct IAM permissions. The service accounts used by KFP components and the Cloud Function will require roles such as `Vertex AI User`, `Pub/Sub Publisher`, and `Service Account User` to create monitors and trigger pipelines. These are critical and must be precise.
*   **Event Schema:** The exact JSON schema of the anomaly payload sent from the `ModelMonitor` to the Pub/Sub topic is not fully documented. The parsing logic in the `cf-i1-train` function may require adjustments after inspecting the first real event.
*   **Asynchronous Debugging:** The system is highly asynchronous. Debugging a failure in the trigger chain (from monitor detection to pipeline start) will require careful inspection of logs from multiple services: Model Monitoring, Pub/Sub, and the Cloud Function.
*   **Resource Naming:** The resource name of the `google_monitoring_notification_channel` must be passed from Terraform into the KFP pipeline at runtime. A robust mechanism for this (e.g., via pipeline parameters) must be established.
