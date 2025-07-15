import os
import sys
import time
from kfp import dsl,compiler
from google.cloud import aiplatform
from pipelines.components.data_prep import data_prep_op
from google_cloud_pipeline_components.v1.batch_predict_job import ModelBatchPredictOp
from google_cloud_pipeline_components.v1.bigquery import BigQueryQueryJobOp


# Define Your Pipeline Configuration
PROJECT_ID = os.getenv("VERTEX_PROJECT_ID")
REGION = os.getenv("VERTEX_REGION")
PIPELINE_BUCKET = os.getenv("VERTEX_BUCKET") # gcs bucket for pipeline artifacts
TENSORBOARD_RESOURCE_NAME = os.getenv("TENSORBOARD_RESOURCE_NAME")
PIPELINE_NAME = os.getenv("PIPELINE_NAME", "transak-i1-predict")
SERVING_CONTAINER_IMAGE_URI = os.getenv("SERVING_CONTAINER_IMAGE_URI", "europe-docker.pkg.dev/vertex-ai-restricted/prediction/tf_opt-cpu.2-17:latest")
if not all([PROJECT_ID, REGION, PIPELINE_BUCKET, TENSORBOARD_RESOURCE_NAME]):
    raise ValueError(
        "The following environment variables must be set: VERTEX_PROJECT_ID, VERTEX_REGION, PIPELINE_BUCKET, TENSORBOARD_RESOURCE_NAME"
    )
PIPELINE_ROOT = f"{PIPELINE_BUCKET}/pipelines/{PIPELINE_NAME}"
EXPERIMENT_NAME = f"{PIPELINE_NAME}-experiment"
PIPELINE_JOB_NAME = f"{PIPELINE_NAME}-job"
PREDICTIONS_TABLE = "predictions"


# The @dsl.pipeline decorator defines this function as a pipeline blueprint.
@dsl.pipeline(
    name=PIPELINE_NAME,
    description="Artur's project Transak - Iteration 1 - An end-to-end pipeline " \
    "to get predictions from the transaction classifier.",
    pipeline_root=PIPELINE_ROOT, # type: ignore
)
def transaction_classifier_predict_pipeline(
    project_id: str = PROJECT_ID, # type: ignore
    model_name: str = "transak-i1-train-model",
    experiment_name: str = EXPERIMENT_NAME, # type: ignore
    run_name: str = PIPELINE_JOB_NAME, # type: ignore
):
    """Defines the sequence of operations in the pipeline. Pipeline orchestrator will execute them."""
    # 1. Data Preparation
    data_prep_task = data_prep_op( # type: ignore
        tensorboard_resource_name=TENSORBOARD_RESOURCE_NAME,
        project_id=project_id,
        region=REGION,
        experiment_name=experiment_name,
        run_name=run_name,
        prediction=True
    )

    # 2. Get the model
    model_importer = dsl.importer(
        artifact_uri=f"https://{REGION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{REGION}/models/{model_name}",
        artifact_class=dsl.Artifact,
        reimport=True,
    )

    # 3. Batch Prediction
    batch_predict_op = ModelBatchPredictOp(
        project=project_id,
        job_display_name="batch_predict_job",
        model=model_importer.outputs["artifact"],
        gcs_source_uris=data_prep_task.outputs["predict_data_path"],
        bigquery_destination_output_uri=f"bq://{PROJECT_ID}.{PIPELINE_NAME}.{PREDICTIONS_TABLE}",
        instances_format="csv",
        predictions_format="bigquery",
        # machine_type="n1-standard-2",
    )


# Compile and Run the Pipeline
if __name__ == "__main__":

    mode = sys.argv[1] if len(sys.argv) > 1 else "submit"
    package_path = f"{PIPELINE_NAME}.json"
    experiment_name = EXPERIMENT_NAME
    local_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
    run_name = f"run-{local_time}"
    print(f"Executing pipeline script in \'{mode}\' mode.")

    # Compile the pipeline into a JSON (which is a form of YAML) file
    compiler.Compiler().compile(
        pipeline_func=transaction_classifier_predict_pipeline, # type: ignore
        package_path=f"{PIPELINE_NAME}.json",
    )
    print(f"Pipeline compiled successfully to {package_path}")

    if mode == "submit":
        aiplatform.init(project=PROJECT_ID,
                        location=REGION,
                        experiment=EXPERIMENT_NAME,
                        experiment_tensorboard=TENSORBOARD_RESOURCE_NAME,
                        )
        aiplatform.autolog()

        experiment =aiplatform.Experiment.get_or_create(
            experiment_name=EXPERIMENT_NAME,
            description="Tracking experiments for the Transak Iteration 1 Vertex AI Prediction Pipeline."
        )

        tb = aiplatform.Tensorboard(TENSORBOARD_RESOURCE_NAME) # type: ignore
        experiment.assign_backing_tensorboard(tb)
        print(f"Tensorboard resource name: {tb.resource_name}")

        print(f"Experiment name: \'{EXPERIMENT_NAME}\'")
        print(f"Experiment run name: \'{run_name}\'")
        with aiplatform.start_run(run=run_name, tensorboard=TENSORBOARD_RESOURCE_NAME) as experiment_run:
            print(f"Started experiment run \'{run_name}\' in experiment \'{EXPERIMENT_NAME}\'")
            pipeline_job = aiplatform.PipelineJob(
                display_name=PIPELINE_JOB_NAME,
                template_path=package_path,
                parameter_values={
                    'experiment_name': EXPERIMENT_NAME,
                    'run_name': run_name,
                },
                enable_caching=False # Disable caching to ensure all new code runs
            )

            print(f"Submitting pipeline job \'{PIPELINE_NAME}\' to Vertex AI...")
            pipeline_job.submit(experiment=experiment)