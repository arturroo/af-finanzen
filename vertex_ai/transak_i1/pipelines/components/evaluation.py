from kfp import dsl
from kfp.dsl import (
    Artifact,
    Input,
    Output,
)
from google_cloud_pipeline_components.types.artifact_types import ClassificationMetrics

CONTAINER_IMAGE_URI = "europe-west6-docker.pkg.dev/af-finanzen/af-finanzen-mlops/transak-i1-evaluation:latest"

@dsl.container_component
def model_evaluation_op(
    model: Input[Artifact],
    test_data: Input[Artifact],
    predictions: Input[Artifact],
    class_labels: Input[Artifact],
    evaluation_metrics: Output[ClassificationMetrics],
    target_column: str = 'i1_true_label_id',
):
    """Perform model evaluation using TensorFlow Model Analysis (TFMA)."""
    return dsl.ContainerSpec(
        image=CONTAINER_IMAGE_URI,
        command=[
            "python",
            "/app/src/components/evaluation/task.py"
        ],
        args=[
            "--model_path", model.uri,
            "--test_data_uri", test_data.uri,
            "--predictions_uri", predictions.uri,
            "--class_labels_uri", class_labels.uri,
            "--output_path", evaluation_metrics.path,
            "--target_column", target_column,
        ]
    )
