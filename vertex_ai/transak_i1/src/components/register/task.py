import argparse
import os
from google.cloud import aiplatform

def _parse_args():
    """Parses command-line arguments for the model registration task."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-path', required=True, type=str, help='GCS path to the saved model artifacts.')
    parser.add_argument('--vertex-model-path', required=True, type=str, help='Local path to write the Vertex AI Model resource name.')
    parser.add_argument('--model-display-name', required=True, type=str, help='Display name for the model in Vertex AI Model Registry.')
    parser.add_argument('--serving-container-image-uri', required=True, type=str, help='URI of the serving container image.')
    parser.add_argument('--project-id', required=True, type=str, help='GCP Project ID.')
    parser.add_argument('--region', required=True, type=str, help='GCP Region for Vertex AI resources.')
    parser.add_argument('--experiment-name', required=True, type=str, help='Name of the experiment for tracking.')
    return parser.parse_args()

def main():
    """Main entrypoint for the model registration task."""
    args = _parse_args()

    print(f"Initializing AI Platform for project {args.project_id} in {args.region}...")
    aiplatform.init(project=args.project_id, location=args.region, experiment=args.experiment_name)

    # Look for an existing model with the same display name to set as parent
    print(f"Searching for parent model with display name: {args.model_display_name}")
    parent_model_resource_name = None
    models = aiplatform.Model.list(
        filter=f'display_name="{args.model_display_name}"',
        project=args.project_id,
        location=args.region,
    )
    if models:
        parent_model_resource_name = models[0].resource_name
        print(f"Found parent model: {parent_model_resource_name}")
    else:
        print("No parent model found. A new model entry will be created.")

    # Upload the model to Vertex AI Model Registry
    print(f"Uploading model to Vertex AI Model Registry: {args.model_display_name}")
    vertex_model = aiplatform.Model.upload(
        display_name=args.model_display_name,
        parent_model=parent_model_resource_name,
        artifact_uri=args.model_path,
        serving_container_image_uri=args.serving_container_image_uri,
        description="Wide & Deep transaction classifier trained via a Vertex AI Pipeline.",
        sync=True # Waits for the upload to complete
    )
    print(f"Model uploaded to registry: {vertex_model.resource_name}")

    # Write the Vertex Model resource name to the specified path
    os.makedirs(os.path.dirname(args.vertex_model_path), exist_ok=True)
    with open(args.vertex_model_path, 'w') as f:
        f.write(vertex_model.resource_name)

if __name__ == '__main__':
    main()