import argparse
import json
from google.cloud import aiplatform

def _parse_args():
    """Parses command-line arguments for the model registration task."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--metrics-path', required=True, type=str)
    parser.add_argument('--project-id', required=True, type=str)
    parser.add_argument('--region', required=True, type=str)
    parser.add_argument('--model-path', required=True, type=str)
    parser.add_argument('--model-display-name', required=True, type=str)
    parser.add_argument('--container-image-uri', required=True, type=str)
    parser.add_argument('--accuracy-threshold', default=0.88, type=float)
    return parser.parse_args()

def main():
    """Main entrypoint for the model registration task."""
    args = _parse_args()

    # 1. Load and check the evaluation metrics
    print(f"Loading metrics from: {args.metrics_path}")
    with open(args.metrics_path, 'r') as f:
        metrics_data = json.load(f)
    
    # KFP v2 metrics are stored in a specific format
    accuracy = metrics_data['metrics'][0]['numberValue']
    print(f"Model accuracy from evaluation: {accuracy:.4f}")

    # 2. Conditional check: only upload if the model is good enough
    if accuracy >= args.accuracy_threshold:
        print(f"Accuracy ({accuracy:.4f}) is above threshold ({args.accuracy_threshold:.4f}). Uploading model to registry...")

        # 3. Initialize the Vertex AI SDK
        aiplatform.init(project=args.project_id, location=args.region)

        # 4. Upload the model
        model = aiplatform.Model.upload(
            display_name=args.model_display_name,
            artifact_uri=args.model_path,
            serving_container_image_uri=args.container_image_uri,
            description="Wide & Deep transaction classifier trained via a Vertex AI Pipeline.",
            sync=True # Waits for the upload to complete
        )
        print(f"Model uploaded successfully. Model resource name: {model.resource_name}")

    else:
        print(f"Accuracy ({accuracy:.4f}) is below threshold ({args.accuracy_threshold:.4f}). Skipping model upload.")


if __name__ == '__main__':
    main()
