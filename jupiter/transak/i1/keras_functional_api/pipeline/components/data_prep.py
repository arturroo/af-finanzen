from kfp.dsl import container_component, ContainerSpec, Input, Output, Model, Dataset

# We use the exact same container image as our training component.
TRAINING_CONTAINER_IMAGE_URI = "europe-west6-docker.pkg.dev/af-finanzen/af-finanzen-mlops/i1-transaction-trainer:latest"

@container_component
def data_prep_op(
    # Component Inputs
    # The data_prep component ONLY needs the project_id to run its query.
    project_id: str,
    # Component Outputs
    train_data_path: Output[Dataset],
    val_data_path: Output[Dataset],
    test_data_path: Output[Dataset]
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
            "-m", "data_prep.task",
            # Pass only the arguments that data_prep/task.py actually needs
            "--project-id", project_id,
            "--train-data-path", train_data_path.path,
            "--val-data-path", val_data_path.path,
            "--test-data-path", test_data_path.path,
        ]
    )
