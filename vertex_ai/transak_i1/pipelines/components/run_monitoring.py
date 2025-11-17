# vertex_ai/transak_i1/pipelines/components/run_monitoring.py

import logging

from kfp.dsl import (Input, Output, Artifact, component)
from google_cloud_pipeline_components.types.artifact_types import VertexModel, BQTable

# Artur Fejklowicz
# 2025-11-17
# __author__ = "Artur Fejklowicz"
# __copyright__ = "Copyright 2025, The AF Finanzen Project"
# __credits__ = ["Artur Fejklowicz"]
# __license__ = "GPLv3"
# __version__ = "1.5.0"
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
    prediction_table: Input[BQTable],
    job_display_name: str,
    month: int,
    query_template: str,
    anomalies: Output[Artifact],
):
    """
    Initiates a model monitoring job and outputs the URI to the anomalies file.

    This component finds the ModelMonitor resource, triggers a monitoring job with a
    predictable output path, and after completion, provides the GCS path to the
    resulting anomalies.json file as an output artifact.
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

    # Construct the FQTN from the input artifact's metadata
    bq_project = prediction_table.metadata["projectId"]
    bq_dataset = prediction_table.metadata["datasetId"]
    bq_table = prediction_table.metadata["tableId"]
    bigquery_prediction_table_fqtn = f"{bq_project}.{bq_dataset}.{bq_table}"

    # Construct the BigQuery query for the specific month, performing the
    # date logic directly in SQL for easier testing.
    query = query_template.format(
        month_placeholder=month,
        table_placeholder=bigquery_prediction_table_fqtn
    )

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

    # Define a predictable output directory for the monitoring job.
    # TODO: Make the base URI a component input parameter for more flexibility.
    # monitoring_output_base_uri = "gs://af-finanzen-mlops/monitoring"
    # output_uri = f"{monitoring_output_base_uri}/{job_display_name}"
    # logging.info(f"Monitoring job output will be saved to: {output_uri}")
    # output_spec = ml_monitoring.spec.OutputSpec(gcs_base_dir=output_uri)
    output_spec = ml_monitoring.spec.OutputSpec(gcs_base_dir=anomalies.uri)

    logging.info(f"Starting monitoring job '{job_display_name}' for target data from BigQuery query.")

    # This is an async call
    monitoring_job = target_monitor.run(
        display_name=job_display_name,
        target_dataset=target_dataset,
        output_spec=output_spec,
    )
    monitoring_job.wait()

    logging.info(f"Successfully launched and completed monitoring job: {monitoring_job.resource_name}")

    # Extract the monitoring job ID from its resource name
    # Example: projects/123/locations/europe-west6/modelMonitors/456/modelMonitoringJobs/789
    monitoring_job_id = monitoring_job.resource_name.split('/')[-1]

    # The anomalies file will be created at a predictable path based on the output_spec.
    # The actual path includes the job ID and 'feature_drift' objective.
    logging.info(f"target_monitor vars: {vars(target_monitor)}")
    
    monitor_id = target_monitor.resource_name.split('/')[-1]
    logging.info(f"monitor_id: {monitor_id}")
    logging.info(f"monitoring_job_id: {monitoring_job_id}")

    anomalies_file_uri = f"{anomalies.uri}/{target_monitor.name}/model_monitoring/{monitor_id}/tabular/jobs/{monitoring_job_id}/feature_drift/anomalies.json"
    # anomalies.uri = anomalies_file_uri
    logging.info(f"Anomalies file URI: {anomalies_file_uri}")

    # The _dashboard_uri() attribute is not available. Constructing the URL manually.
    dashboard_uri = (
        f"https://console.cloud.google.com/vertex-ai/locations/{location}/"
        f"model-monitoring/{monitoring_job.resource_name}?project={project}"
    )
    logging.info(f"View job details in the console: {dashboard_uri}")