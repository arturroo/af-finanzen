# vertex_ai/transak_i1/pipelines/components/run_monitoring.py

import logging

from kfp.dsl import (Input, component)
from google_cloud_pipeline_components.types.artifact_types import VertexModel, BQTable

# Artur Fejklowicz
# 2025-11-15
# __author__ = "Artur Fejklowicz"
# __copyright__ = "Copyright 2025, The AF Finanzen Project"
# __credits__ = ["Artur Fejklowicz"]
# __license__ = "GPLv3"
# __version__ = "1.3.0"
# __maintainer__ = "Artur Fejklowicz"
# __status__ = "Production"


@component(
    base_image="python:3.9",
    packages_to_install=["google-cloud-aiplatform", "google-cloud-pipeline-components"],
)
def run_monitoring_op(
    project: str,
    location: str,
    vertex_model: Input[VertexModel],
    # prediction_table: Input[BQTable],
    job_display_name: str,
    month: int,
    query_template: str,
):
    """
    Initiates a model monitoring job using a BigQuery query as the target dataset.

    This component finds the ModelMonitor resource associated with the specific
    production model version and triggers an asynchronous monitoring job to check
    for data drift against the data for a specific month from the predictions table.
    """
    import logging
    from google.cloud import aiplatform
    from vertexai.resources.preview import ml_monitoring

    logging.getLogger().setLevel(logging.INFO)
    aiplatform.init(project=project, location=location)

    model_resource_name_with_version = vertex_model.metadata["resourceName"]
    logging.info(f"Got model resource name: {model_resource_name_with_version}")

    model = aiplatform.Model(model_name=model_resource_name_with_version)
    logging.info(f"Model resource name: {model.resource_name}")
    logging.info(f"Model version id: {model.version_id}")

    # The API does not support filtering by model resource name directly.
    # We must list all monitors and filter them client-side.
    monitors = ml_monitoring.ModelMonitor.list()
    
    found_monitors = []
    for monitor in monitors:
        # The monitor's target model resource name (without version)
        monitor_model_resource_name = monitor._gca_resource.model_monitoring_target.vertex_model.model
        monitor_model_version_id = monitor._gca_resource.model_monitoring_target.vertex_model.model_version_id

        if model.resource_name == monitor_model_resource_name and model.version_id == monitor_model_version_id:
            found_monitors.append(monitor)
            logging.info(f"Found matching monitor: {monitor.resource_name}")

    if not found_monitors:
        logging.warning(f"No model monitor found for model '{model_resource_name_with_version}'. Skipping monitoring job.")
        return

    if len(found_monitors) > 1:
        raise ValueError(f"Found {len(found_monitors)} monitors for model version {model_resource_name_with_version}. Expected only 1.")

    target_monitor = found_monitors[0]
    logging.info(f"Found model monitor: {target_monitor.resource_name}")

    # # Construct the FQTN from the input artifact's metadata
    # bq_project = prediction_table.metadata["projectId"]
    # bq_dataset = prediction_table.metadata["datasetId"]
    # bq_table = prediction_table.metadata["tableId"]
    # bigquery_prediction_table_fqtn = f"{bq_project}.{bq_dataset}.{bq_table}"

    # Construct the BigQuery query for the specific month, performing the
    # date logic directly in SQL for easier testing.
    query = query_template.format(month_placeholder=month)

    # query = f"""
    # SELECT *
    # FROM `{bigquery_prediction_table_fqtn}`
    # WHERE 
    #     started_year = DIV({month}, 100) 
    #     AND started_month = MOD({month}, 100)
    # """
    logging.info(f"Using BigQuery query for monitoring: {query}")

    target_dataset = ml_monitoring.spec.MonitoringInput(
        query=query,
        data_format="bigquery",
    )

    logging.info(f"Starting monitoring job '{job_display_name}' for target data from BigQuery query.")

    # This is an async call
    monitoring_job = target_monitor.run(
        display_name=job_display_name,
        target_dataset=target_dataset,
    )
    monitoring_job.wait()

    logging.info(f"Successfully launched monitoring job: {monitoring_job.resource_name}")
    # The _dashboard_uri() attribute is not available. Constructing the URL manually.
    dashboard_uri = (
        f"https://console.cloud.google.com/vertex-ai/locations/{location}/"
        f"model-monitoring/{monitoring_job.resource_name}?project={project}"
    )
    logging.info(f"View job details in the console: {dashboard_uri}")