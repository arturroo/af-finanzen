from kfp.dsl import container_component, ContainerSpec, Input, Output, Model, Dataset

# This is best practice to define pushed container's image URI as a constant at the top.
TRAINING_CONTAINER_IMAGE_URI = "europe-west6-docker.pkg.dev/af-finanzen/af-finanzen-mlops/transak-i1-train:latest"

@container_component
def train_model_op(
    # Component Inputs & Outputs
    train_data_path: Input[Dataset],
    val_data_path: Input[Dataset],
    output_model_path: Output[Model],
    num_epochs: int,
    learning_rate: float,
    batch_size: int,
    num_classes: int,
    tensorboard_resource_name: str,
    project_id: str,
    region: str,
    experiment_name: str = "experiment_name",
    run_name: str = "run_name"
):
    """
    A containerized component that runs the model training task.
    It launches our pre-built custom container and passes parameters
    as command-line arguments to the trainer/task.py script inside it.
    """
    # The ContainerSpec defines the container image to run and the command to execute inside it.
    return ContainerSpec(
        image=TRAINING_CONTAINER_IMAGE_URI,
        command=[
            "python",
            "-m", "src.components.trainer.task", # I run own task script as a module
            # pass all inputs and hyperparameters as command-line arguments
            "--train-data-path", train_data_path.uri,
            "--val-data-path", val_data_path.uri,
            "--output-model-path", output_model_path.path,
            "--num-epochs", str(num_epochs),
            "--learning-rate", str(learning_rate),
            "--batch-size", str(batch_size),
            "--num-classes", str(num_classes),
            "--tensorboard-resource-name", str(tensorboard_resource_name),
            "--project-id", str(project_id),
            "--region", str(region),
            "--experiment-name", experiment_name,
            "--run-name", run_name
        ]
    )
