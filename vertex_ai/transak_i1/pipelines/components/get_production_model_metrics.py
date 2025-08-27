from kfp.dsl import component, Output
from google_cloud_pipeline_components.types.artifact_types import ClassificationMetrics

@component(
    base_image="python:3.9",
    packages_to_install=["google-cloud-aiplatform"],
)
def get_production_model_metrics_op(
    project: str,
    location: str,
    model_display_name: str,
    production_evaluation: Output[ClassificationMetrics],
):
    """
    A component that retrieves the evaluation artifact of the model
    currently aliased as 'production' in the Vertex AI Model Registry.
    """
    from google.cloud import aiplatform

    print(f"Initializing AI Platform for project {project} in {location}...")
    aiplatform.init(project=project, location=location)

    all_models = aiplatform.Model.list(filter=f'display_name="{model_display_name}"')

    production_model = None
    for model in all_models:
        if "production" in model.version_aliases:
            production_model = model
            break

    if production_model:
        print(f"Found production model: {production_model.resource_name}")
        evaluations = production_model.list_model_evaluations()
        if evaluations:
            latest_evaluation = evaluations[0]
            print(f"Found evaluation: {latest_evaluation.resource_name}")
            # Simply pass the URI of the latest evaluation artifact
            production_evaluation.uri = latest_evaluation.uri
            print(f"Set production evaluation URI to: {production_evaluation.uri}")
        else:
            print("No evaluations found for the production model.")
            # Create an empty artifact if no evaluation exists
            production_evaluation.uri = "gcs://dummy/uri"
    else:
        print("No model with 'production' alias found.")
        # Create an empty artifact if no production model exists
        production_evaluation.uri = "gcs://dummy/uri"