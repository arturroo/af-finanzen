# vertex_ai/transak_i1/pipelines/components/run_monitoring.py

import logging

from kfp.dsl import (Input, Artifact, component)
from google_cloud_pipeline_components.types.artifact_types import VertexModel

# Artur Fejklowicz
# 2025-11-11
# __author__ = "Artur Fejklowicz"
# __copyright__ = "Copyright 2025, The AF Finanzen Project"
# __credits__ = ["Artur Fejklowicz"]
# __license__ = "GPLv3"
# __version__ = "1.0.0"
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
    predictions: Input[Artifact],
    prediction_results_format: str,
    job_display_name: str,
):
    """
    Initiates a model monitoring job for a given model version and prediction dataset.

    This component finds the ModelMonitor resource associated with the specific
    production model version and triggers an asynchronous monitoring job to check
    for data drift in the new prediction data from GCS.
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

    # # List all monitors and filter for the one matching our model
    # monitors = ml_monitoring.ModelMonitor.list()
    # 
    # target_monitor = None
    # # model_resource_name_no_version = model.resource_name.split("@")[0]
    # for monitor in monitors:
    #     # The monitor's target model resource name (without version)
    #     logging.info(f"Monitor vars: {vars(monitor)}")
    #     logging.info(f"Checking monitor: {monitor.resource_name}")
    #     monitor_model_resource_name = monitor._gca_resource.model_monitoring_target.vertex_model.model
    #     monitor_model_version_id = monitor._gca_resource.model_monitoring_target.vertex_model.model_version_id
    #     logging.info(f"Monitor model resource name: {monitor_model_resource_name}")
    #     logging.info(f"Monitor model version id: {monitor_model_version_id}")

    #     if model.resource_name == monitor_model_resource_name and model.version_id == monitor_model_version_id:
    #         target_monitor = monitor
    #         logging.info(f"Found matching monitor: {target_monitor.resource_name}")
    #         break

    # if not target_monitor:
    #     logging.warning(f"No model monitor found for model '{model_resource_name_with_version}'. Skipping monitoring job.")
    #     return

    # Build a filter to find the specific monitor
    filter_str = (
        f'model_monitoring_target.vertex_model.model="{model.resource_name}" AND '
        f'model_monitoring_target.vertex_model.model_version_id="{model.version_id}"'
    )
    logging.info(f"Using filter to find monitor: {filter_str}")
    monitors = ml_monitoring.ModelMonitor.list(filter=filter_str)

    if not monitors:
        logging.warning(f"No model monitor found for model '{model_resource_name_with_version}'. Skipping monitoring job.")
        return
    
    if len(monitors) > 1:
        raise ValueError(f"Found {len(monitors)} monitors for model version {model_resource_name_with_version}. Expected only 1.")

    target_monitor = monitors[0]

    logging.info(f"Found model monitor: {target_monitor.resource_name}")

    target_dataset = ml_monitoring.spec.MonitoringInput(
        gcs_uri=predictions.uri,
        data_format=prediction_results_format,
    )

    logging.info(f"Starting monitoring job '{job_display_name}' for target data: {predictions.uri}")

    # This is an async call
    monitoring_job = target_monitor.run(
        display_name=job_display_name,
        target_dataset=target_dataset,
    )

    logging.info(f"Successfully launched monitoring job: {monitoring_job.resource_name}")
    logging.info(f"View job details in the console: {monitoring_job._dashboard_uri()}")