from kfp.dsl import component, Output
from google_cloud_pipeline_components.types.artifact_types import VertexModel

@component(
    base_image="python:3.9",
    packages_to_install=["google-cloud-aiplatform", "google-cloud-pipeline-components"],
)
def get_production_model_op(
    production_model: Output[VertexModel],
    project: str,
    location: str,
    model_display_name: str,
):
    """
    A component that retrieves the Vertex AI Model artifact
    currently aliased as 'production' in the Vertex AI Model Registry.
    """
    from google.cloud import aiplatform

    print(f"Initializing AI Platform for project {project} in {location}...")
    aiplatform.init(project=project, location=location)

    # Get the model resource (parent model) by display name
    # models_with_display_name = aiplatform.Model.list(filter=f'display_name="{model_display_name}"')
    # model_versions = aiplatform.Model.listVersions(name=model_display_name)
    # model_registry = aiplatform.models.ModelRegistry(model=model_id)
    production_model_version = aiplatform.Model(model_name="projects/819397114258/locations/europe-west6/models/5048491201817214976", version="production")


    if not production_model_version:
        print(f"No model found with display name: {model_display_name}")
        raise ValueError("No model found with the specified display name.")
    else:
        print(f"Found model with display_name: {production_model_version.display_name}")

    print(f"Model: {production_model_version}")

    prod_model_resource_name = production_model_version.name

    if prod_model_resource_name:
        print(f"Found production model: {prod_model_resource_name}")
        production_model.metadata["resourceName"] = f"{production_model_version.resource_name}@{production_model_version.version_id}"
        production_model.uri = production_model_version.uri
        print(f"Set production model resourceName to: {production_model.metadata['resourceName']}")
        print(f"Set production model URI to: {production_model.uri}")
    else:
        print("No model with 'production' alias found among versions.")
        raise ValueError("No production model found.")
