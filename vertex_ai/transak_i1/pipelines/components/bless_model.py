from kfp.v2.dsl import component, Input, Output, Model, Metrics
from google.cloud import aiplatform
from google_cloud_pipeline_components.types.artifact_types import VertexModel, ClassificationMetrics
import json # Import json module

@component(
    base_image="python:3.9",
    packages_to_install=["google-cloud-aiplatform"],
)
def bless_model_op(
    vertex_model: Input[VertexModel],
    metrics: Input[ClassificationMetrics],
    production_accuracy: float,
    project: str,
    location: str,
):
    """
    A component that blesses a new model by assigning it the 'production' alias
    in the Vertex AI Model Registry if its accuracy is better than the current production model's accuracy.
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
    print(f"Candidate model accuracy: {accuracy}, Production model accuracy: {production_accuracy}")

    if accuracy > production_accuracy:
        print(f"Candidate model accuracy {accuracy} is better than production model accuracy {production_accuracy}. Blessing model...")

        # Get the new model object
        new_model = aiplatform.Model(model_name=model_resource_name)

        # Find the current production model (if any)
        current_production_models = aiplatform.Model.list(filter='labels.aiplatform.googleapis.com/model_version_alias="production"')

        if current_production_models:
            for old_model in current_production_models:
                print(f"Removing 'production' alias from old model: {old_model.resource_name}")
                old_model.remove_version_aliases(aliases=['production'])

        # Assign 'production' alias to the new model
        new_model.set_version_aliases(aliases=['production'])
        print(f"Model {new_model.resource_name} blessed with 'production' alias.")
    else:
        print(f"Candidate model accuracy {accuracy} is not better than production model accuracy {production_accuracy}. Model not blessed.")
