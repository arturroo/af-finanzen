from kfp.dsl import container_component, ContainerSpec, Input, Output, Model, Metrics

# We use the exact same container image as our other components.
TRAINING_CONTAINER_IMAGE_URI = "europe-west6-docker.pkg.dev/af-finanzen/af-finanzen-mlops/i1-transaction-trainer:latest"

@container_component
def register_model_op(
    # --- Component Inputs ---
    metrics: Input[Metrics],
    model: Input[Model],
    model_display_name: str,
    container_image_uri: str,
    accuracy_threshold: float,
    tensorboard_resource_name: str,
    project_id: str,
    region: str,
    experiment_name: str = "experiment_name",
    run_name: str = "run_name",
):
    """
    A containerized component that conditionally uploads a model to the Vertex AI Model Registry if it meets the accuracy threshold.
    """
    return ContainerSpec(
        image=TRAINING_CONTAINER_IMAGE_URI,
        command=[
            "python",
            "-m", "tasks.register.task",
            "--metrics-path", metrics.path,
            "--model-path", model.uri,
            "--model-display-name", model_display_name,
            "--container-image-uri", container_image_uri,
            "--accuracy-threshold", str(accuracy_threshold),
            "--tensorboard-resource-name", str(tensorboard_resource_name),
            "--project-id", project_id,
            "--region", region,
            "--experiment-name", experiment_name,
            "--run-name", run_name
        ]
    )
