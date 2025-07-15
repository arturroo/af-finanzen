from kfp.dsl import container_component, ContainerSpec, Input, Output, Model, Dataset

# We use the exact same container image as our training component.
TRAINING_CONTAINER_IMAGE_URI = "europe-west6-docker.pkg.dev/af-finanzen/af-finanzen-mlops/transak-i1-train:latest"

@container_component
def data_prep_op(
    train_data_path: Output[Dataset],
    val_data_path: Output[Dataset],
    test_data_path: Output[Dataset],
    tensorboard_resource_name: str,
    project_id: str,
    region: str,
    experiment_name: str = "experiment_name",
    run_name: str = "run_name",
):
    """
    A containerized component that runs the data preparation task.
    It launches our pre-built custom container and passes parameters
    to the data_prep/task.py script inside it.
    """
    return ContainerSpec(
        image=TRAINING_CONTAINER_IMAGE_URI,
        command=[
            "python",
            "-m", "src.components.data_prep.task",
            # Pass only the arguments that data_prep/task.py actually needs
            "--project-id", project_id,
            "--train-data-path", train_data_path.path,
            "--val-data-path", val_data_path.path,
            "--test-data-path", test_data_path.path,
            "--tensorboard-resource-name", str(tensorboard_resource_name),
            "--project-id", str(project_id),
            "--region", str(region),
            "--experiment-name", experiment_name,
            "--run-name", run_name
        ]
    )
