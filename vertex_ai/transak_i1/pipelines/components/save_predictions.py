from kfp.v2.dsl import component, Input, Output, Artifact
from google_cloud_pipeline_components.types.artifact_types import BQTable

@component(
    base_image='python:3.9',
    packages_to_install=["pandas==2.2.2", "google_cloud_pipeline_components==2.20.1", "db-dtypes", "pyarrow", "google-cloud-bigquery"],
)
def save_predictions_op(
    predictions: Input[Artifact],
    bigquery_prediction_table: Output[BQTable],
    project_id: str,
    region: str,
    bigquery_prediction_table_fqtn: str,
    pipeline_run_id: str,
    month: int,
):
    """
    A component that saves batch predictions to a BigQuery table.
    """
    import pandas as pd
    from google.cloud import bigquery
    import numpy as np
    from pathlib import Path
    import math

    # --- Helper Functions ---
    def softmax(x):
        """Compute softmax values for a single list of scores."""
        e_x = np.exp(x - np.max(x))
        return e_x / e_x.sum()

    def entropy(p):
        """Compute entropy for a single probability distribution."""
        return -sum([p_i * math.log(p_i) for p_i in p if p_i > 0])

    # Find the prediction file and read it directly into Pandas
    prediction_dir = Path(predictions.path)
    jsonl_file = next(
        (f for f in prediction_dir.iterdir() if "prediction.results-" in f.name),
        None,
    )
    if not jsonl_file:
        raise FileNotFoundError(f"No prediction results file found in {predictions.path}")

    print(f"Reading predictions from {jsonl_file} into DataFrame.")
    predictions_df = pd.read_json(jsonl_file, lines=True)

    # The 'instance' column is a dict, and the 'prediction' column is a list of scores (logits).
    # We want to flatten the instance and calculate our metrics.
    
    # Get the original data from the 'instance' column
    instance_df = pd.json_normalize(predictions_df['instance'])
    
    # Get the logits
    logits = list(predictions_df['prediction'])

    # --- Calculate Metrics ---
    predicted_class_ids = []
    probabilities_list = []
    confidence_msp_list = []
    confidence_margin_list = []
    confidence_entropy_list = []

    for logit_list in logits:
        # Probabilities
        probabilities = softmax(np.array(logit_list))
        probabilities_list.append(probabilities.tolist())
        
        # Predicted class
        predicted_class_ids.append(np.argmax(probabilities))
        
        # MSP
        confidence_msp_list.append(np.max(probabilities))
        
        # Margin
        sorted_probs = np.sort(probabilities)[::-1]
        margin = sorted_probs[0] - sorted_probs[1] if len(sorted_probs) > 1 else sorted_probs[0]
        confidence_margin_list.append(margin)
        
        # Entropy
        confidence_entropy_list.append(entropy(probabilities))

    # Create a new dataframe with the results
    results_df = pd.concat([
        instance_df,
        pd.DataFrame({
            'i1_pred_label_id': predicted_class_ids,
            'logits': logits,
            'probas': probabilities_list,
            'confidence_msp': confidence_msp_list,
            'confidence_margin': confidence_margin_list,
            'confidence_entropy': confidence_entropy_list
        })
    ], axis=1)

    # Add the pipeline run URL for traceability
    if "placeholder" in pipeline_run_id.lower():
        pipeline_run_url = "local_run"
    else:
        pipeline_run_url = f"https://console.cloud.google.com/vertex-ai/pipelines/locations/{region}/runs/{pipeline_run_id}?project={project_id}"
    results_df["pipeline_run_url"] = pipeline_run_url
    results_df["month"] = month

    # Save the predictions to BigQuery
    bq_client = bigquery.Client(project=project_id)
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",
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
