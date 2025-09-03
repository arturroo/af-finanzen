from kfp.v2.dsl import component, Output, Dataset

@component(
    base_image='us-docker.pkg.dev/deeplearning-platform-release/gcr.io/tf2-cpu.2-17.py310',
)
def get_prediction_data_op(
    prediction_data: Output[Dataset],
    project_id: str,
    month: int,
    query: str,
):
    """
    A component that executes a query for a given month and saves the result to a GCS path.
    """
    import pandas as pd
    from google.cloud import bigquery

    final_query = query.format(month_placeholder=month)

    bq_client = bigquery.Client(project=project_id)
    print(f"Running query: {final_query}")
    df = bq_client.query(final_query).to_dataframe()

    print(f"Saving prediction data to {prediction_data.path}")
    df.to_csv(prediction_data.path, index=False)
