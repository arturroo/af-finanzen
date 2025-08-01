# Project Context
This is a financial services application with strict security requirements.
The model is used to classify Artur's Revolut transactions.

# MLOps Architecture: An Automated Transaction Classifier

## Overview

This document outlines a professional, end-to-end MLOps system for training, evaluating, deploying, and monitoring a transaction classification model on Google Cloud.

The architecture is built on a **two-pipeline system** to cleanly separate the concerns of model development from production prediction:
1.  Pipeline train **Training & Blessing Pipeline** responsible for creating and validating a new "champion" model.
2.  Pipeline predict **Prediction & Monitoring Pipeline** responsible for generating monthly predictions and automatically triggering retraining when data drift is detected.

A core principle of this design is the creation of a **"golden source" data table** by an initial pipeline step, ensuring that both training and prediction pipelines draw from the exact same, versioned raw data.
The entire system is orchestrated by **Vertex AI Pipelines**, with each step running as a version-controlled, **custom Docker container**.

---

## 1. Pipeline Train: The Training & Promotion Pipeline

**Goal:** To train a new model, evaluate it against the current production model, and if it proves superior, "bless" it by promoting it to become the new production champion.

**Trigger:** Can be run manually or automatically by the monitoring pipeline when data drift is detected.

### Component Workflow:

1.  **`bq_config_generator_op`**
    * **Action:** Formats the pipeline job name to extract a timestamp and constructs a BigQuery job configuration dictionary, including the fully qualified table name for the golden source data.
    * **Output:** A dictionary containing the BigQuery job configuration.

2.  **`get_golden_data_op`** (using `BigQueryQueryJobOp`)
    * **Input:** The BigQuery job configuration from `bq_config_generator_op`.
    * **Action:** This pre-built Google component executes the base SQL query to get all historical transaction data and writes it to a new, versioned "golden source" table in BigQuery.
    * **Output:** A `google.BQTable` artifact pointing to the newly created "golden source" table for this run.

3.  **`data_splits_op`**
    * **Input:** The `google.BQTable` artifact from `get_golden_data_op`.
    * **Action:** Reads from the golden source table, adds integer labels, splits the data into `train`, `val`, and `test` sets, and saves these as CSVs to Cloud Storage. The `tid` column is retained in the CSVs for traceability but is dropped before model training.
    * **Output:** `train`, `val`, and `test` `Dataset` artifacts.

4.  **`train_model_op`**
    * **Input:** `train` and `val` `Dataset` artifacts from `data_splits_op`.
    * **Action:** Trains our custom Wide & Deep Keras model on the `train` and `val` datasets, logging all metrics in real-time to **Vertex AI TensorBoard**. The `tid` column is dropped from the dataframes before being fed to the model.
    * **Output:** A trained `Model` artifact in the TensorFlow SavedModel format.

5.  **`model_evaluation_op`** (using `ModelEvaluationOp`)
    * **Input:** The trained `Model` artifact from `train_model_op` and the `test` `Dataset` artifact from `data_splits_op`.
    * **Action:** This is a pre-built Google Cloud Pipeline Component. It takes the trained model, the `test` dataset, and the original training data statistics. It automatically calculates a rich set of classification metrics and generates interactive visualizations (like a **confusion matrix** and **ROC curve**) directly in the Vertex AI UI.
    * **Output:** Evaluation metrics and visualizations.

6.  **`bless_model_op` (Conditional Step)**
    * **Action:** This is our final quality gate, implemented as a `dsl.Condition`. It runs **only if** the new `candidate` model's accuracy is greater than our 88% threshold.
    * If the condition is met, this component uses the Vertex AI SDK to **update the model's aliases** in the Model Registry. It removes the `production` alias from the old model version and assigns it to our new, superior `candidate` version. The new model is now officially "blessed".

---

## 2. Pipeline Predict: The Prediction & Monitoring Pipeline

**Goal:** To generate monthly predictions using the best available model and to continuously monitor for data drift.

**Trigger:** Scheduled to run automatically using **Cloud Scheduler**.

### Component Workflow:

1.  **`get_prediction_data_op`**
    * **Action:** Queries BigQuery for only the most recent data (e.g., last 30 days).
    * **Output:** A `prediction_input.csv` artifact.

2.  **`batch_predict_op`**
    * **Action:** This component fetches the model currently aliased as **`production`** from the Model Registry. It then triggers a **Vertex AI Batch Prediction Job** using this model and the new prediction data.
    * **Output:** Saves predictions to a result table in BigQuery.

3.  **`monitoring_op`**
    * **Action:** Triggers a **Vertex AI Model Monitoring** job, comparing the statistics of the prediction data against the original training data to detect feature drift and training-serving skew (continuous evaluation).

4.  **`trigger_retraining_op` (Conditional Step)**
    * **Action:** A `dsl.Condition` that checks `if drift_detected`.
    * If true, this component makes an API call to **trigger a new run of our Training & Promotion Pipeline**, creating a fully automated, closed-loop MLOps system.

---

## 3. System Interaction Diagram

```ascii
                                                     +-----------------------------+
                                                     |                             |
                                        (if drift >  |  Training & Promotion       |
                                        threshold)   |       Pipeline              |
                                           +---------|                             |
                                           |         +-----------------------------+
                                           |                       |
                                           | (creates new          |
                                           | 'production' model)   V
[GCS ObjectFinalize Trigger] -> [Prediction & Monitoring Pipeline] -> [Model Registry] -> [Batch Prediction] -> [Results in BQ]
                               |                                  ^
                               | (uses 'production' model)        |
                               +----------------------------------+

```