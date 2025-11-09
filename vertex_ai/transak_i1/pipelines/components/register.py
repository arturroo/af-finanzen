from kfp.dsl import component, Output, Input, Model, Dataset
from google_cloud_pipeline_components.types.artifact_types import VertexModel
from google.cloud import aiplatform

@component(
    base_image="python:3.9",
    packages_to_install=["google-cloud-aiplatform", "google-cloud-pipeline-components"],
)
def register_model_op(
    # --- Component Inputs ---
    model: Input[Model],
    train_data_uri: str,
    candidate_model: Output[VertexModel],
    model_display_name: str,
    serving_container_image_uri: str,
    project_id: str,
    region: str,
    experiment_name: str,
    disable_cache2: bool = False,
):
    from google.cloud import aiplatform
    print(f"Initializing AI Platform for project {project_id} in {region}...")
    aiplatform.init(project=project_id, location=region, experiment=experiment_name)

    # Look for an existing model with the same display name to set as parent
    print(f"Searching for parent model with display name: {model_display_name}")
    parent_model_resource_name = None
    models = aiplatform.Model.list(
        filter=f'display_name="{model_display_name}"',
        project=project_id,
        location=region,
    )
    if models:
        parent_model_resource_name = models[0].resource_name
        print(f"Found parent model: {parent_model_resource_name}")
    else:
        print("No parent model found. A new model entry will be created.")

    description = (
        "Wide & Deep transaction classifier trained via a Vertex AI Pipeline.\n"
        f"Training data URI: {train_data_uri}"
    )

    # Upload the model to Vertex AI Model Registry
    print(f"Uploading model to Vertex AI Model Registry: {model_display_name}")
    vertex_model = aiplatform.Model.upload(
        display_name=model_display_name,
        parent_model=parent_model_resource_name,
        artifact_uri=model.uri,
        serving_container_image_uri=serving_container_image_uri,
        description=description,
        sync=True # Waits for the upload to complete
    )
    print(f"Model uploaded to registry resource_name: {vertex_model.resource_name}")
    print(f"Model uploaded to registry version_id: {vertex_model.version_id}")

    import json
    from pathlib import Path

    full_resource_name = f"{vertex_model.resource_name}@{vertex_model.version_id}"
    candidate_model.metadata["resourceName"] = full_resource_name
    candidate_model.uri = vertex_model.uri
    print(f"Set candidate model resourceName to: {candidate_model.metadata['resourceName']}")
    print(f"Set candidate model URI to: {candidate_model.uri}")

    # Save the resource name to a file within the artifact directory for downstream components
    metadata_file_path = Path(candidate_model.path) / "vertex_model_metadata.json"
    with open(metadata_file_path, 'w') as f:
        json.dump({"resourceName": full_resource_name}, f)
    print(f"Saved model metadata with resource name to {metadata_file_path}")
