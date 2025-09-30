# Project: AF Finanzen

## Project Overview

This repository, "AF Finanzen," is a comprehensive project for managing and analyzing personal financial data. The overall project flow begins with manual collecting data from various banks and eventually running small ETL processes with Google Cloud Functions. Next transactions are classified into personal budget categories.

For data from Revolut, this classification is handled automatically by a full, end-to-end MLOps system on Google Cloud. For other financial sources, transactions are classified manually. At the beginning of each month, these classifications are used to calculate and transfer the correct amount of money back to the main credit card.

Finally, all classifications (both automatic and manual) are fed into Looker Studio to produce a Sankey diagram that visualizes the month's expenses.

The core of the automated system is a transaction classification model for Revolut data, which uses a custom **Wide & Deep** model built with TensorFlow/Keras. The entire machine learning lifecycle—from data preparation and training to evaluation and deployment—is automated and orchestrated using **Vertex AI Pipelines**. The cloud infrastructure is managed declaratively using **Terraform**, ensuring that all resources are version-controlled and reproducible.

## Project Motivation (The "Why")

The primary motivation behind this project was to solve several key challenges in personal financial management:

1.  **Eliminate Tedious Manual Work:** Manually classifying hundreds of Revolut transactions each month was time-consuming and repetitive. The core goal was to automate this process with a reliable ML model.

2.  **Gain Financial Control and Insight:** To truly understand spending habits, a centralized and organized dataset is essential. By consolidating and classifying data in BigQuery, it becomes possible to gain deep insights that aren't available directly from bank statements.

3.  **Enable Powerful Analytics:** The transaction classification (both automatic for Revolut and manual for other banks) is the necessary first step to unlock meaningful analytics. The ultimate goal is to feed this clean, categorized data into Looker Studio to visualize monthly expenses and track budget adherence effectively.

In short, this project was built to save time, create order, and provide the data-driven tools needed for smarter financial management.

## Key Technologies

*   **ML Orchestration:** Vertex AI Pipelines (Kubeflow Pipelines/KFP)
*   **Model Framework:** TensorFlow / Keras
*   **Infrastructure as Code:** Terraform
*   **Data Storage & Warehousing:** Google BigQuery (external Hive ind internal Tables), Google Cloud Storage
*   **Compute:** Google Cloud Functions, Vertex AI Training & Prediction
*   **Experimentation:** Jupyter Notebooks, Vertex AI TensorBoard
*   **Human in the loop:** Google Sheets with BigQuery and own ActionScript

## Repository Structure

The project is organized into several distinct directories, each with a specific purpose:

*   `vertex_ai/transak_i1/`: The heart of the MLOps system. It contains the source code for the Vertex AI training and prediction pipelines, including all custom KFP components, the model definition (`model.py`), and the Dockerfile for creating custom container images.

*   `terraform/`: Contains all the Terraform code for provisioning the Google Cloud infrastructure. This includes definitions for BigQuery datasets and tables, Google Cloud Storage buckets, Cloud Functions, and IAM policies.

*   `cloud_functions/`: Source code for serverless functions used in the data lifecycle. For example, `cf-pdf2bq` likely handles the extraction of data from PDF bank statements and ingestion into BigQuery.

*   `jupiter/`: A collection of Jupyter notebooks used for data science tasks like Exploratory Data Analysis (EDA), model prototyping, and visualization.

*   `sql/`: Contains SQL scripts for creating and managing BigQuery views, which serve as the data source for the ML pipelines and analytics.

*   `python/`: Standalone Python scripts for various tasks, such as text classification experiments.

## MLOps Architecture

The project's MLOps architecture is built around two primary, interconnected Vertex AI Pipelines:

1.  **Training & Blessing Pipeline:**
    *   Responsible for training a new "challenger" model on the latest data.
    *   Evaluates the challenger against the current "champion" (production) model.
    *   If the new model is superior, it is "blessed" and promoted to production in the Vertex AI Model Registry.
    *   This entire process runs in custom containers defined by the `Dockerfile` in the `vertex_ai/transak_i1` directory.

2.  **Prediction & Monitoring Pipeline:**
    *   Runs on a schedule (e.g., monthly) to generate predictions using the current production model.
    *   Saves predictions back to a BigQuery table.
    *   Includes a (planned) model monitoring step to detect data drift, which can automatically trigger a new run of the Training Pipeline.

## How to Run the Main Pipeline

The primary workflow is the Vertex AI pipeline located in `vertex_ai/transak_i1`.

1.  **Prerequisites:**
    *   Google Cloud SDK installed and authenticated.
    *   A Python environment with dependencies from `vertex_ai/transak_i1/pyproject.toml` installed.

2.  **Build the Custom Container:**
    *   Navigate to the `vertex_ai/transak_i1` directory.
    *   Build and push the container to Google Artifact Registry:
        ```bash
        gcloud builds submit --region="europe-west1" --tag="europe-west6-docker.pkg.dev/af-finanzen/af-finanzen-mlops/transak-i1-train-predict:latest" .
        ```

3.  **Execute the Training Pipeline:**
    *   Set the necessary environment variables (`VERTEX_PROJECT_ID`, `VERTEX_REGION`, etc.).
    *   Run the pipeline submission script from the `vertex_ai/transak_i1` directory:
        ```python
        from pipelines import pipeline_train
        pipeline_train.main()
        ```
