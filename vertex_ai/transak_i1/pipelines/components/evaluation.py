from kfp import dsl
from kfp.dsl import (
    Artifact,
    Input,
    Output,
)
from google_cloud_pipeline_components.types.artifact_types import ClassificationMetrics

TRAIN_PREDICT_CONTAINER_IMAGE_URI = "europe-west6-docker.pkg.dev/af-finanzen/af-finanzen-mlops/transak-i1-train-predict:latest"

@dsl.container_component
def model_evaluation_op(
    predictions: Input[Artifact],
    class_labels: Input[Artifact],
    evaluation_metrics: Output[ClassificationMetrics],
    target_column: str = 'i1_true_label_id',
):
    """Perform model evaluation using TensorFlow Model Analysis (TFMA)."""
    return dsl.ContainerSpec(
        image=TRAIN_PREDICT_CONTAINER_IMAGE_URI,
        command=[
            "python",
            "/app/src/components/evaluation/task.py"
        ],
        args=[
            "--predictions_uri", predictions.uri,
            "--class_labels_uri", class_labels.uri,
            "--output_path", evaluation_metrics.path,
            "--target_column", target_column,
        ]
    )
