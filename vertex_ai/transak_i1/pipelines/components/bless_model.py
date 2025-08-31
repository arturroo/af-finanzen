from kfp.v2.dsl import component, Input, Output, Model, Metrics
from google_cloud_pipeline_components.types.artifact_types import VertexModel, ClassificationMetrics

@component(
    base_image="python:3.9",
    packages_to_install=["google-cloud-aiplatform", "google-cloud-pipeline-components"],
)
def bless_model_op(
    vertex_model: Input[VertexModel],
    project: str,
    location: str,
):
    """
    A component that blesses a new model by assigning it the 'production' alias
    in the Vertex AI Model Registry if its accuracy is better than the current production model's accuracy.
    """
    from google.cloud import aiplatform

    print(f"Initializing AI Platform for project {project} in {location}...")
    aiplatform.init(project=project, location=location)

    model_version_resource_name = vertex_model.metadata["resourceName"]
    print(f"Retrieved model from artifact with version resource name: {model_version_resource_name}")
    # Create a Model object for the specific model VERSION that was passed in.
    # We need this to get its version ID and parent model resource name.
    model_version = aiplatform.Model(model_name=model_version_resource_name)
    print(f"Got artifact model object with resourceName: {model_version.resource_name}")

    print(f"Adding 'production' alias to version {model_version.version_id} of model parent {model_version.resource_name} by calling the Vertex AI Model Registry representation.")
    model_version_registry = aiplatform.ModelRegistry(model_version.resource_name)
    model_version_registry.add_version_aliases(
        new_aliases=["production"], 
        version=model_version.version_id
    )

    print(f"Successfully blessed parent model version {model_version.resource_name} with 'production' alias.")
