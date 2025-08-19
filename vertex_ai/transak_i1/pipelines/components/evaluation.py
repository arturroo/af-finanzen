from kfp.dsl import Input, Model, Artifact, Dataset
from google_cloud_pipeline_components.v1.model_evaluation import ModelEvaluationClassificationOp

def evaluate_model_op(
    project: str,
    location: str,
    target_field_name: str,
    model: Input[Model],
    predictions: Input[Dataset],
    ground_truth: Input[Dataset],
    class_labels: list,
):
    """
    Factory function for a ModelEvaluationClassificationOp task.

    This function creates and configures a ModelEvaluationClassificationOp task.
    It is not a component itself, but it helps to encapsulate the evaluation
    logic and keep the main pipeline file cleaner.
    """
    return ModelEvaluationClassificationOp(
        project=project,
        location=location,
        target_field_name=target_field_name,
        model=model,
        predictions_format='jsonl',
        predictions_gcs_source=predictions.uri,
        ground_truth_format='csv',
        ground_truth_gcs_source=[ground_truth.uri],
        class_labels=class_labels,
    )