from kfp.dsl import container_component, ContainerSpec, Input, Output, Model, Dataset, Artifact
from google_cloud_pipeline_components.types.artifact_types import VertexModel

# This is best practice to define pushed container's image URI as a constant at the top.
BATCH_PREDICT_CONTAINER_IMAGE_URI = "europe-west6-docker.pkg.dev/af-finanzen/af-finanzen-mlops/transak-i1-train-predict:latest"

@container_component
def batch_predict_op(
    project: str,
    location: str,
    vertex_model: Input[VertexModel],
    test_data: Input[Dataset],
    #predictions: Output[Artifact],
    predictions: Output[Artifact],
    experiment_name: str,
):
    """
    A custom component to perform batch predictions using a trained TensorFlow model
    retrieved from the Vertex AI Model Registry.
    """
    return ContainerSpec(
        image=BATCH_PREDICT_CONTAINER_IMAGE_URI,
        command=[
            "python",
            "-m", "src.components.batch_predict.task",
            "--project", project,
            "--location", location,
            "--vertex-model-path", vertex_model.path,
            "--test-data-uri", test_data.uri,
            "--predictions-path", predictions.path,
            "--experiment-name", experiment_name,
        ]
    )
