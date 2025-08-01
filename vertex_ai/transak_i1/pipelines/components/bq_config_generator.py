from kfp import dsl
import json

@dsl.component(
    base_image='python:3.9',
)
def bq_config_generator_op(
    project_id: str,
    pipeline_job_name: str,
    dataset_id: str,
    table_name_prefix: str,
) -> dict:
    """Extracts the timestamp from the pipeline job name and constructs a BigQuery job configuration."""

    # The pipeline_job_name from KFP for a scheduled run looks like:
    # e.g., 'transak-i1-train-20250801000003'
    # We split the string by '-' and take the last element.
    timestamp = pipeline_job_name.split('-')[-1]

    table_id = f"{table_name_prefix}_{timestamp}"

    # Construct the configuration dictionary
    job_config = {
        "useQueryCache": "False",
        "createDisposition": "CREATE_IF_NEEDED",
        "writeDisposition": "WRITE_TRUNCATE",
        "destinationTable": {
            "projectId": project_id,
            "datasetId": dataset_id,
            "tableId": table_id
        }
    }
    
    return job_config
