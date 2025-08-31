from kfp.v2.dsl import component, Output, Dataset

@component(
    base_image='python:3.9',
    packages_to_install=["pandas", "google-cloud-bigquery", "db-dtypes"],
)
def get_prediction_data_op(
    prediction_data: Output[Dataset],
    project_id: str,
    region: str,
    golden_sources_table_name: str,
    pipeline_timestamp: str,
):
    """
    A component that reads golden data from the last month
    that do not have i1_true_label_id (IS NULL).
    """
    import pandas as pd
    from google.cloud import bigquery

    # Construct the Fully Qualified Table Name (FQTN)
    fqtn = f"{project_id}.{golden_sources_table_name}.golden_source_{pipeline_timestamp}"

    query = f"""
    SELECT
      *
    FROM `{fqtn}`
    WHERE i1_true_label_id IS NULL
    AND date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
    """
    bq_client = bigquery.Client(project=project_id)
    print(f"Running query: {query}")
    df = bq_client.query(query).to_dataframe()

    print(f"Saving prediction data to {prediction_data.path}")
    df.to_csv(prediction_data.path, index=False)
