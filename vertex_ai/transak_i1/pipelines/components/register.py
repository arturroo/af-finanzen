from kfp.dsl import container_component, ContainerSpec, Input, Output, Model
from google_cloud_pipeline_components.types.artifact_types import VertexModel

# We use the exact same container image as our other components.
TRAIN_PREDICT_CONTAINER_IMAGE_URI = "europe-west6-docker.pkg.dev/af-finanzen/af-finanzen-mlops/transak-i1-train-predict:latest"

@container_component
def register_model_op(
    # --- Component Inputs ---
    model: Input[Model],
    vertex_model: Output[VertexModel],
    model_display_name: str,
    serving_container_image_uri: str,
    project_id: str,
    region: str,
    experiment_name: str,
):
    """
    A containerized component that uploads a model to the Vertex AI Model Registry.
    """
    return ContainerSpec(
        image=TRAIN_PREDICT_CONTAINER_IMAGE_URI,
        command=[
            "python",
            "-m", "src.components.register.task",
            "--model-path", model.uri,
            "--vertex-model-path", vertex_model.path,
            "--model-display-name", model_display_name,
            "--serving-container-image-uri", serving_container_image_uri,
            "--project-id", project_id,
            "--region", region,
            "--experiment-name", experiment_name,
        ]
    )
