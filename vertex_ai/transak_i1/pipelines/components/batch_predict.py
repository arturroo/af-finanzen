
from kfp.v2.dsl import (
    component,
    Input,
    Output,
    Dataset,
    Artifact,
)
from google_cloud_pipeline_components.types.artifact_types import VertexModel

@component(
    base_image="python:3.9",
    packages_to_install=["google-cloud-aiplatform", "google-cloud-pipeline-components"],
)
def batch_predict_op(
    project: str,
    location: str,
    vertex_model: Input[VertexModel],
    test_data: Input[Dataset],
    predictions: Output[Artifact],
    experiment_name: str,
):
    """
    Component to run a batch prediction job on Vertex AI.
    """
    from google.cloud import aiplatform

    aiplatform.init(project=project, location=location, experiment=experiment_name)

    # The path attribute provides the local file path to the artifact's payload.
    print(f"Reading model resource name from local path: {vertex_model.path}")
    with open(vertex_model.path, 'r') as f:
        model_resource_name = f.read().strip()

    print(f"Retrieved model resource name: {model_resource_name}")

    # Get the model resource
    model_resource = aiplatform.Model(model_name=model_resource_name)

    # Create the batch prediction job
    batch_prediction_job = model_resource.batch_predict(
        job_display_name="batch_predict_job",
        gcs_source=test_data.uri,
        instances_format="csv",
        predictions_format="jsonl",
        gcs_destination_prefix=predictions.uri,
        machine_type="n1-standard-4",
    )

    # Wait for the job to complete
    batch_prediction_job.wait()

    # Set the output artifact path
    predictions.uri = batch_prediction_job.output_info.gcs_output_directory
