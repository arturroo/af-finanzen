from kfp.v2.dsl import component, Input, Output, Model, Metrics
from google.cloud import aiplatform
from google_cloud_pipeline_components.types.artifact_types import VertexModel, ClassificationMetrics

@component(
    base_image="python:3.9",
    packages_to_install=["google-cloud-aiplatform"],
)
def bless_model_op(
    vertex_model: Input[VertexModel],
    metrics: Input[ClassificationMetrics],
    accuracy_threshold: float,
    project: str,
    location: str,
):
    """
    A component that blesses a new model by assigning it the 'production' alias
    in the Vertex AI Model Registry if its accuracy meets the threshold.
    """
    print(f"Initializing AI Platform for project {project} in {location}...")
    aiplatform.init(project=project, location=location)

    # Get the model resource name from the input artifact
    with open(vertex_model.path, 'r') as f:
        model_resource_name = f.read().strip()
    print(f"Retrieved model resource name: {model_resource_name}")

    # Get the accuracy from the metrics artifact
    with open(metrics.path, 'r') as f:
        evaluation_metrics = f.read()
    metrics_dict = json.loads(evaluation_metrics)
    accuracy = metrics_dict['accuracy']
    print(f"Model accuracy: {accuracy}, Threshold: {accuracy_threshold}")

    if accuracy >= accuracy_threshold:
        print(f"Accuracy {accuracy} meets threshold {accuracy_threshold}. Blessing model...")
        model_registry_object = aiplatform.Model(model_name=model_resource_name)

        # Remove 'production' alias from any existing model versions
        # This is a more robust way to ensure only one model has the alias
        for version in model_registry_object.version_aliases.get('production', []):
            print(f"Removing 'production' alias from version: {version}")
            model_registry_object.remove_version_aliases(['production'], version=version)

        # Assign 'production' alias to the new model version
        model_registry_object.set_version_aliases(['production'])
        print(f"Model {model_resource_name} blessed with 'production' alias.")
    else:
        print(f"Accuracy {accuracy} does not meet threshold {accuracy_threshold}. Model not blessed.")
