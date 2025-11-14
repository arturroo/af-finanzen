# vertex_ai/transak_i1/pipelines/components/run_monitoring.py

import logging

from kfp.dsl import (Input, component)
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
    model: Input[VertexModel],
    prediction_results_gcs_uri: str,
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

    model_resource_name = model.metadata["resourceName"]
    logging.info(f"Got model resource name: {model_resource_name}")

    model_obj = aiplatform.Model(model_name=model_resource_name)
    model_version_id = model_obj.version_id
    logging.info(f"Model version ID: {model_version_id}")

    # List all monitors and filter for the one matching our model and version
    monitors = ml_monitoring.ModelMonitor.list()
    
    target_monitor = None
    for monitor in monitors:
        logging.info(f"Checking monitor: {monitor.resource_name}")
        logging.info(f"Monitor model name: {monitor.model_name}")
        logging.info(f"Monitor model version ID: {monitor.model_version_id}")
        logging.info(f"Monitor vars: {vars(monitor)}")

        if monitor.model_name.endswith(model_obj.resource_name) and monitor.model_version_id == model_version_id:
            target_monitor = monitor
            break

    if not target_monitor:
        logging.warning(
            f"No model monitor found for model '{model_resource_name}' "
            f"with version '{model_version_id}'. Skipping monitoring job."
        )
        return

    logging.info(f"Found model monitor: {target_monitor.resource_name}")

    target_dataset = ml_monitoring.spec.MonitoringInput(
        gcs_uri=prediction_results_gcs_uri,
        data_format=prediction_results_format,
    )

    logging.info(f"Starting monitoring job '{job_display_name}' for target data: {prediction_results_gcs_uri}")

    # This is an async call
    monitoring_job = target_monitor.run(
        display_name=job_display_name,
        target_dataset=target_dataset,
    )

    logging.info(f"Successfully launched monitoring job: {monitoring_job.resource_name}")
    logging.info(f"View job details in the console: {monitoring_job._dashboard_uri()}")