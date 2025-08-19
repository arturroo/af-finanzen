from kfp.dsl import container_component, ContainerSpec, Input, Output, Model
from google_cloud_pipeline_components.types.artifact_types import VertexModel

TRAIN_PREDICT_CONTAINER_IMAGE_URI = "europe-west6-docker.pkg.dev/af-finanzen/af-finanzen-mlops/transak-i1-train-predict:latest"

@container_component
def get_model_resource_name_op(
    vertex_model: Input[VertexModel],
    model_resource_name: Output[str],
):
    """
    A containerized component that extracts the resourceName from a VertexModel artifact.
    """
    return ContainerSpec(
        image=TRAIN_PREDICT_CONTAINER_IMAGE_URI,
        command=[
            "python",
            "-m", "src.components.get_model_resource_name.task",
            "--vertex-model-path", vertex_model.path,
            "--model-resource-name-path", model_resource_name.path,
        ]
    )
