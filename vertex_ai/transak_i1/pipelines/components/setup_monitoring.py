from kfp.dsl import Dataset, Input, component
from google_cloud_pipeline_components.types.artifact_types import VertexModel
from typing import List

@component(
    base_image="python:3.9",
    packages_to_install=[
        "google-cloud-aiplatform==1.56.0",
        "google-cloud-pipeline-components==2.20.1",
    ],
)
def setup_monitoring_op(
    project: str,
    location: str,
    vertex_model: Input[VertexModel],
    baseline_dataset: Input[Dataset],
    notification_channel: str,
    user_emails: List[str],
    display_name_prefix: str,
):
    """
    Creates a ModelMonitor resource for a given model version.

    Args:
        project (str): The GCP project ID.
        location (str): The GCP region.
        model (Input[Model]): The model artifact to be monitored.
        baseline_dataset (Input[Dataset]): The dataset to be used as a baseline for monitoring.
        notification_channel (str): The resource name of the notification channel.
        user_emails (list[str]): A list of user emails for notifications.
        display_name_prefix (str): The display name prefix for the ModelMonitor.
    """
    import logging
    from google.cloud import aiplatform
    from vertexai.resources.preview import ml_monitoring

    logging.basicConfig(level=logging.INFO)
    logging.info(f"Component setup_monitoring started.")
    logging.info(f"project: {project}")
    logging.info(f"location: {location}")
    logging.info(f"model.uri: {vertex_model.uri}")
    logging.info(f"baseline_dataset.uri: {baseline_dataset.uri}")
    logging.info(f"notification_channel: {notification_channel}")
    logging.info(f"user_emails: {user_emails}")
    logging.info(f"display_name_prefix: {display_name_prefix}")

    aiplatform.init(project=project, location=location)

    model_resource_name_with_version = vertex_model.metadata["resourceName"]
    logging.info(f"Got model resource name with version: {model_resource_name_with_version}")

    model = aiplatform.Model(model_name=model_resource_name_with_version)
    # model_version_id = model_obj.version_id
    logging.info(f"Model resource name: {model.resource_name}")
    logging.info(f"Model version id: {model.version_id}")


    # Define Monitoring Schema
    monitoring_schema = ml_monitoring.spec.ModelMonitoringSchema(
        feature_fields=[
            # ml_monitoring.spec.FieldSchema(name="tid", data_type="numerical"),
            ml_monitoring.spec.FieldSchema(name="type", data_type="categorical"),
            # ml_monitoring.spec.FieldSchema(name="started_year", data_type="integer"),
            # ml_monitoring.spec.FieldSchema(name="started_month", data_type="integer"),
            # ml_monitoring.spec.FieldSchema(name="started_day", data_type="integer"),
            ml_monitoring.spec.FieldSchema(name="started_weekday", data_type="categorical"),
            # ml_monitoring.spec.FieldSchema(name="first_started_year", data_type="integer"),
            # ml_monitoring.spec.FieldSchema(name="first_started_month", data_type="integer"),
            # ml_monitoring.spec.FieldSchema(name="first_started_day", data_type="integer"),
            # ml_monitoring.spec.FieldSchema(name="first_started_weekday", data_type="integer"),
            ml_monitoring.spec.FieldSchema(name="description", data_type="categorical"),
            ml_monitoring.spec.FieldSchema(name="amount", data_type="float"),
            # ml_monitoring.spec.FieldSchema(name="currency", data_type="categorical"),
        ],
        prediction_fields=[
            ml_monitoring.spec.FieldSchema(name="i1_pred_label", data_type="categorical")
        ],
        ground_truth_fields=[
            ml_monitoring.spec.FieldSchema(name="i1_true_label", data_type="categorical")
        ]
    )

    # Define Training Dataset
    training_dataset = ml_monitoring.spec.MonitoringInput(
        gcs_uri=baseline_dataset.uri,
        data_format="csv",
    )

    # Define Data Drift Spec for features
    feature_drift_spec = ml_monitoring.spec.DataDriftSpec(
        categorical_metric_type="l_infinity",
        numeric_metric_type="jensen_shannon_divergence",
        default_categorical_alert_threshold=0.3,
        default_numeric_alert_threshold=0.3,
    )

    # Define Data Drift Spec for predictions
    prediction_output_drift_spec = ml_monitoring.spec.DataDriftSpec(
        categorical_metric_type="l_infinity",
        default_categorical_alert_threshold=0.3,
    )

    # Define Notification Spec
    notification_spec = ml_monitoring.spec.NotificationSpec(
        user_emails=user_emails,
        notification_channels=[notification_channel],
        enable_cloud_logging=True,
    )

    # Create Model Monitor
    try:
        model_monitor = ml_monitoring.ModelMonitor.create(
            display_name=f"{display_name_prefix}-v{model.version_id}",
            project=project,
            location=location,
            model_name=model.resource_name,
            model_version_id=model.version_id,
            model_monitoring_schema=monitoring_schema,
            training_dataset=training_dataset,
            tabular_objective_spec=ml_monitoring.spec.TabularObjective(
                feature_drift_spec=feature_drift_spec,
                prediction_output_drift_spec=prediction_output_drift_spec,
            ),
            notification_spec=notification_spec,
        )
        logging.info(f"ModelMonitor created: {model_monitor.resource_name}")
    except Exception as e:
        logging.error(f"Failed to create ModelMonitor: {e}")
        raise

    logging.info("Component setup_monitoring finished.")
