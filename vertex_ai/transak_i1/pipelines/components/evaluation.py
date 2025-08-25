from kfp import dsl
from kfp.dsl import (
    Artifact,
    Input,
    Output,
)
from google_cloud_pipeline_components.types.artifact_types import ClassificationMetrics, VertexModel

TRAIN_PREDICT_CONTAINER_IMAGE_URI = "europe-west6-docker.pkg.dev/af-finanzen/af-finanzen-mlops/transak-i1-train-predict:latest"

@dsl.container_component
def model_evaluation_op(
    project: str,
    location: str,
    predictions: Input[Artifact],
    class_labels: Input[Artifact],
    vertex_model: Input[VertexModel],
    evaluation_metrics: Output[ClassificationMetrics],
    target_column: str = 'i1_true_label_id',
    evaluation_display_name: str = "production_evaluation",
    cache_trigger4: bool = False
):
    """Perform model evaluation and upload metrics."""
    return dsl.ContainerSpec(
        image=TRAIN_PREDICT_CONTAINER_IMAGE_URI,
        command=[
            "python",
            "/app/src/components/evaluation/task.py"
        ],
        args=[
            "--project", project,
            "--location", location,
            "--predictions_uri", predictions.uri,
            "--class_labels_uri", class_labels.uri,
            "--model_resource_path", vertex_model.path,
            "--output_path", evaluation_metrics.path,
            "--target_column", target_column,
            "--evaluation_display_name", evaluation_display_name,
        ]
    )
