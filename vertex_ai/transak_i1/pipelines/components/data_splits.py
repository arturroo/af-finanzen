from kfp.dsl import container_component, ContainerSpec, Input, Output, Dataset
from google_cloud_pipeline_components.types.artifact_types import BQTable

# We use the exact same container image as our training component.
TRAIN_PREDICT_CONTAINER_IMAGE_URI = "europe-west6-docker.pkg.dev/af-finanzen/af-finanzen-mlops/transak-i1-train-predict:latest"

@container_component
def data_splits_op(
    golden_data_table: Input[BQTable],
    train_data: Output[Dataset],
    val_data: Output[Dataset],
    test_data: Output[Dataset],
    tensorboard_resource_name: str,
    project_id: str,
    region: str,
    experiment_name: str = "experiment_name",
    run_name: str = "run_name",
):
    """
    A containerized component that runs the create training splits task.
    It launches our pre-built custom container and passes parameters
    to the create_training_splits/task.py script inside it.
    """
    return ContainerSpec(
        image=TRAIN_PREDICT_CONTAINER_IMAGE_URI,
        command=[
            "python",
            "-m", "src.components.data_splits.task",
            # Pass the FQTN components instead of the URI
            "--bq-project-id", golden_data_table.metadata['projectId'],
            "--bq-dataset-id", golden_data_table.metadata['datasetId'],
            "--bq-table-id", golden_data_table.metadata['tableId'],
            "--train-data-path", train_data.path,
            "--val-data-path", val_data.path,
            "--test-data-path", test_data.path,
            "--tensorboard-resource-name", str(tensorboard_resource_name),
            "--project-id", project_id,
            "--region", str(region),
            "--experiment-name", experiment_name,
            "--run-name", run_name
        ]
    )
