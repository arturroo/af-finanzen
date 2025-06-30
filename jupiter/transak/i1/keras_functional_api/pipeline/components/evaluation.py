from kfp.dsl import container_component, ContainerSpec, Input, Output, Model, Dataset, Metrics, HTML

TRAINING_CONTAINER_IMAGE_URI = "europe-west6-docker.pkg.dev/af-finanzen/af-finanzen-mlops/i1-transaction-trainer:latest"

@container_component
def evaluate_model_op(
    model: Input[Model],
    test_data: Input[Dataset],
    metrics: Output[Metrics],
    confusion_matrix: Output[HTML],
    project_id: str,
    region: str
):
    """
    A containerized component that runs the model evaluation task.
    It takes a trained model and a test set, and produces evaluation
    metrics and a confusion matrix visualization.
    """
    return ContainerSpec(
        image=TRAINING_CONTAINER_IMAGE_URI,
        command=[
            "python",
            "-m", "tasks.evaluation.task",
            "--model-path", model.path,
            "--test-data-uri", test_data.uri,
            "--metrics-path", metrics.path,
            "--confusion-matrix-path", confusion_matrix.path,
            "--project-id", project_id,
            "--region", region
        ]
    )
