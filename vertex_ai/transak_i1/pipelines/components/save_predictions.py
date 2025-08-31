from kfp.v2.dsl import component, Input, Output, Artifact
from google_cloud_pipeline_components.types.artifact_types import BQTable

@component(
    base_image='python:3.9',
    packages_to_install=["pandas", "google-cloud-bigquery", "google-cloud-storage", "db-dtypes", "pyarrow", "fsspec", "gcsfs"],
)
def save_predictions_op(
    predictions_gcs_dir: Input[Artifact],
    bigquery_prediction_table: Output[BQTable],
    project_id: str,
    bigquery_prediction_table_fqtn: str,
):
    """
    A component that saves batch predictions to a BigQuery table.
    """
    import pandas as pd
    from google.cloud import bigquery
    import json
    import numpy as np

    # The predictions_gcs_dir.path is a directory. The batch prediction job
    # creates one or more jsonl files in it.
    # We need to read all of them.
    gcs_path = predictions_gcs_dir.path
    
    # Read all jsonl files in the directory
    # To read from GCS, pandas needs gcsfs
    df = pd.read_json(f"{gcs_path}/prediction.results-00000-of-00001", lines=True)

    # The 'instance' column is a dict, and the 'prediction' column is a list of scores.
    # We want to flatten the instance and get the predicted class from the scores.
    
    # Get the original data from the 'instance' column
    instance_df = pd.json_normalize(df['instance'])
    
    # Get the predicted class id by finding the index of the max score
    predicted_class_id = [np.argmax(p) for p in df['prediction']]
    
    # Get the scores
    scores = list(df['prediction'])
    
    # Create a new dataframe with the results
    results_df = pd.concat([
        instance_df,
        pd.DataFrame({'predicted_i1_true_label_id': predicted_class_id, 'prediction_scores': scores})
    ], axis=1)

    # Save the predictions to BigQuery
    bq_client = bigquery.Client(project=project_id)
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",
    )

    print(f"Saving predictions to {bigquery_prediction_table_fqtn}")
    job = bq_client.load_table_from_dataframe(
        results_df, bigquery_prediction_table_fqtn, job_config=job_config
    )
    job.result()

    # Update the output artifact
    table = bq_client.get_table(bigquery_prediction_table_fqtn)
    bigquery_prediction_table.metadata["tableId"] = table.table_id
    bigquery_prediction_table.metadata["datasetId"] = table.dataset_id
    bigquery_prediction_table.metadata["projectId"] = table.project
    bigquery_prediction_table.uri = f"https://console.cloud.google.com/bigquery?project={table.project}&ws=!1m5!1m4!4m3!1s{table.project}!2s{table.dataset_id}!3s{table.table_id}"
