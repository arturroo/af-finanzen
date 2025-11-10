from kfp.dsl import Dataset, Input, Model, component

@component(
    base_image="python:3.9",
    packages_to_install=[
        "google-cloud-aiplatform==1.56.0",
        "google-cloud-pipeline-components==2.20.1",
    ],
)
def setup_monitoring(
    project: str,
    location: str,
    model: Input[Model],
    baseline_dataset: Input[Dataset],
    notification_channel: str,
    user_emails: list[str],
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
        display_name (str): The display name for the ModelMonitor.
    """
    import logging
    from google.cloud import aiplatform
    from vertexai.resources.preview import ml_monitoring

    logging.basicConfig(level=logging.INFO)
    logging.info(f"Component setup_monitoring started.")
    logging.info(f"project: {project}")
    logging.info(f"location: {location}")
    logging.info(f"model.uri: {model.uri}")
    logging.info(f"baseline_dataset.uri: {baseline_dataset.uri}")
    logging.info(f"notification_channel: {notification_channel}")
    logging.info(f"user_emails: {user_emails}")
    logging.info(f"display_name: {display_name}")

    aiplatform.init(project=project, location=location)

    model_name = model.resource_name
    model_version_id = model.version_id

    # Define Monitoring Schema
    monitoring_schema = ml_monitoring.spec.ModelMonitoringSchema(
        feature_fields=[
            ml_monitoring.spec.FieldSchema(name="type", data_type="categorical"),
            ml_monitoring.spec.FieldSchema(name="description", data_type="categorical"),
        ],
    )

    # Define Training Dataset
    training_dataset = ml_monitoring.spec.MonitoringInput(
        gcs_uri=baseline_dataset.uri,
        data_format="csv",
    )

    # Define Data Drift Spec
    feature_drift_spec = ml_monitoring.spec.DataDriftSpec(
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
            display_name=f"{display_name_prefix}-v{model_version_id}",
            project=project,
            location=location,
            model_name=model_name,
            model_version_id=model_version_id,
            model_monitoring_schema=monitoring_schema,
            training_dataset=training_dataset,
            tabular_objective_spec=ml_monitoring.spec.TabularObjective(
                feature_drift_spec=feature_drift_spec
            ),
            notification_spec=notification_spec,
        )
        logging.info(f"ModelMonitor created: {model_monitor.resource_name}")
    except Exception as e:
        logging.error(f"Failed to create ModelMonitor: {e}")
        raise

    logging.info("Component setup_monitoring finished.")
