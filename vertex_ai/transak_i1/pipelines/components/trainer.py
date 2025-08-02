from kfp.dsl import container_component, ContainerSpec, Input, Output, Model, Dataset
from google_cloud_pipeline_components.types.artifact_types import VertexModel

# This is best practice to define pushed container's image URI as a constant at the top.
TRAIN_PREDICT_CONTAINER_IMAGE_URI = "europe-west6-docker.pkg.dev/af-finanzen/af-finanzen-mlops/transak-i1-train-predict:latest"

@container_component
def train_model_op(
    # Component Inputs & Outputs
    train_data: Input[Dataset],
    val_data: Input[Dataset],
    output_model: Output[Model],
    vertex_model: Output[VertexModel],
    num_epochs: int,
    learning_rate: float,
    batch_size: int,
    num_classes: int,
    tensorboard_resource_name: str,
    project_id: str,
    region: str,
    experiment_name: str,
    # run_name: str,
    model_display_name: str = "",
    serving_container_image_uri: str = ""
):
    """
    A containerized component that runs the model training task.
    It launches our pre-built custom container and passes parameters
    as command-line arguments to the trainer/task.py script inside it.
    """
    # The ContainerSpec defines the container image to run and the command to execute inside it.
    return ContainerSpec(
        image=TRAIN_PREDICT_CONTAINER_IMAGE_URI,
        command=[
            "python",
            "-m", "src.components.trainer.task", # I run own task script as a module
            # pass all inputs and hyperparameters as command-line arguments
            "--train-data-uri", train_data.uri,
            "--val-data-uri", val_data.uri,
            "--output-model-path", output_model.path,
            "--vertex-model-path", vertex_model.path,
            "--num-epochs", str(num_epochs),
            "--learning-rate", str(learning_rate),
            "--batch-size", str(batch_size),
            "--num-classes", str(num_classes),
            "--tensorboard-resource-name", str(tensorboard_resource_name),
            "--project-id", str(project_id),
            "--region", str(region),
            "--experiment-name", str(experiment_name),
            # "--run-name", str(run_name),
            "--model-display-name", model_display_name,
            "--serving-container-image-uri", serving_container_image_uri
        ]
    )
