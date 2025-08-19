from kfp.v2.dsl import component, Input, Output, Metrics
from google_cloud_pipeline_components.types.artifact_types import ClassificationMetrics
import json

@component(
    base_image="python:3.9",
    packages_to_install=[],
)
def get_accuracy_from_metrics_op(
    metrics: Input[ClassificationMetrics],
) -> Output[float]:
    """
    A component that extracts the accuracy from a ClassificationMetrics artifact.
    """
    with open(metrics.path, 'r') as f:
        evaluation_metrics = f.read()
    metrics_dict = json.loads(evaluation_metrics)
    accuracy = metrics_dict['accuracy']
    print(f"Extracted accuracy: {accuracy}")

    with open(Output[float].path, "w") as f:
        f.write(str(accuracy))
    return accuracy
