# Project Backlog

## Automate Golden Data Creation from Private Google Sheet

**Issue:** The current process for creating the `revolut_abrechnung` table is manual. This is a workaround for an "Access Denied" (HTTP 403) error when BigQuery tries to query the external table/view `revolut_abrechnung_v`, which is based on a private Google Sheet.

**Context:**
- The manual process is error-prone and has introduced `NULL` values into the `i1_true_label` column, causing downstream pipeline failures.
- You have already attempted to grant full access rights for the Google Sheet to the BigQuery service account, but the 403 error persists.

**Goal:** Automate the creation of the training data source by successfully querying the private Google Sheet from BigQuery without making the sheet public.

**Next Steps (To Investigate Later):**
- Identify the exact service account BigQuery uses for external queries in this project context.
- Verify the exact scope of permissions granted on the Google Sheet (is it "Viewer" or "Editor"?).
- Investigate if there are any organization-level policies (VPC Service Controls, etc.) that might be blocking the access.
- Explore using a service account with domain-wide delegation if necessary.
- Consider alternative automation, such as a Cloud Function with Google Sheets API credentials that writes data into a native BigQuery table.

---

## Implement Data Validation and Alerting in Training Pipeline

**Issue:** The training pipeline can currently run with incomplete or incorrect labels (e.g., `NULL` values, or an unexpected number of classes). This can lead to silent failures or poorly trained models.

**Goal:** Implement a robust data validation step within the `data_splits` component that acts as a quality gate for the training pipeline.

**Requirements:**
1.  **Label Set Validation:** The component must verify that the incoming data contains exactly the 13 expected class labels, and no more or less.
2.  **Exception on Failure:** If the validation fails, the component must raise an exception, causing the pipeline to fail immediately and visibly.
3.  **GCP Alerting:** The pipeline failure should trigger a GCP Monitoring Alert.
4.  **Email Notification:** The alert should send a notification to your email.
5.  **Infrastructure as Code:** The entire alerting mechanism (e.g., Log-Based Metric for the pipeline failure, Monitoring Alert Policy, and Email Notification Channel) should be defined in a new Terraform module located at `terraform/modules/monitoring/alerting.tf`.

---

## HITL Orchestration Strategy

**Goal:** To create a robust, semi-automated Human-in-the-Loop (HITL) workflow that correctly uses manually verified data for retraining.

**Chosen Architecture:**
1.  **Manual Verification in Google Sheets:** Continue using Google Sheets as the UI for verifying monthly predictions.
2.  **Intelligent Trigger:** An Apps Script button ("Approve & Retrain") in the sheet will call a Cloud Function.
3.  **Stateful Check:** The Cloud Function will first query a state-tracking table in BigQuery to confirm that model monitoring has detected drift for the month in question.
4.  **Conditional Retraining:** The training pipeline will only be triggered if drift has been confirmed, preventing unnecessary runs.

---

## Model Evaluation Strategy

**Goal:** To evaluate models using a method that is both stable for long-term benchmarking and relevant for recent data drift.

**Chosen Strategy: "Simulated" Hybrid Test Sets**
1.  **Single Data Split:** The `data_splits` component will continue to produce one growing test set based on a deterministic random sample (`MOD(tid, 10)`).
2.  **In-Pipeline Division:** A new pipeline component will divide the test set into two in-memory artifacts:
    *   **Historical Test Set:** All test data *excluding* the most recent month. This serves as the stable benchmark.
    *   **Recent Test Set:** Data *only* from the most recent month that triggered the retraining. This serves as the drift check.
3.  **Dual Evaluation:** The champion and challenger models will be evaluated against both test sets in parallel.
4.  **Sophisticated Blessing Logic:** The `bless_or_not_to_bless` component will be updated to require a new model to perform well on *both* the historical set (to prove general improvement) and the recent set (to prove it has adapted to the drift).
