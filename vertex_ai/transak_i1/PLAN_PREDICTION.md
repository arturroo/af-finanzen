# Plan for `pipeline_predict.py`

This document outlines the sequence of operations for the prediction and monitoring pipeline.

The pipeline will orchestrate the following components in sequence:

1.  **Get Production Model:**
    *   Retrieves the model currently aliased as "production" from the Vertex AI Model Registry.
    *   Extracts the model's creation timestamp to identify the corresponding "golden source" data.

2.  **Fetch Prediction Data:**
    *   Queries the "golden source" BigQuery table.
    *   Selects only recent transactions (e.g., last 30 days) that have not yet been labeled (`i1_true_label_id IS NULL`).

3.  **Run Batch Prediction:**
    *   Uses the retrieved production model to run a batch prediction job on the new data.

4.  **Save Predictions to BigQuery:**
    *   Takes the output from the batch prediction job.
    *   Flattens the results and saves them to a dedicated predictions table in BigQuery for analysis and use.

5.  **Perform Drift Detection:**
    *   Retrieves the GCS URI of the original training data from the production model's description field.
    *   Compares the statistical properties (e.g., feature distributions, means) of the new prediction data against the original training data.
    *   Outputs a boolean flag indicating if significant drift is detected.

6.  **Trigger Retraining (Conditional):**
    *   This step runs only if the drift detection step outputs `true`.
    *   It will automatically submit a new run of the `pipeline_train` pipeline to retrain the model on fresh data.
