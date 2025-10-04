import os
import sys
import time
from typing import Optional
from kfp import dsl, compiler
from google.cloud import aiplatform
from pipelines.components.prediction_config_generator import prediction_config_generator_op
from pipelines.components.get_prediction_data import get_prediction_data_op
from pipelines.components.get_production_model import get_production_model_op
from pipelines.components.batch_predict import batch_predict_op
from pipelines.components.save_predictions import save_predictions_op
from src.common.base_sql import predict_data_query


# Define Your Pipeline Configuration
PROJECT_ID = os.getenv("VERTEX_PROJECT_ID")
REGION = os.getenv("VERTEX_REGION")
PIPELINE_BUCKET = os.getenv("VERTEX_BUCKET") # gcs bucket for pipeline artifacts
PIPELINE_NAME = os.getenv("PIPELINE_NAME", "transak-i1-predict")
SERVING_CONTAINER_IMAGE_URI = os.getenv("SERVING_CONTAINER_IMAGE_URI", "europe-docker.pkg.dev/vertex-ai-restricted/prediction/tf_opt-cpu.2-17:latest")
if not all([PROJECT_ID, REGION, PIPELINE_BUCKET]):
    raise ValueError(
        "The following environment variables must be set: VERTEX_PROJECT_ID, VERTEX_REGION, PIPELINE_BUCKET"
    )
PIPELINE_ROOT = f"{PIPELINE_BUCKET}/pipelines/{PIPELINE_NAME}"
EXPERIMENT_NAME = f"{PIPELINE_NAME}-experiment"
PIPELINE_JOB_NAME = f"{PIPELINE_NAME}-job"
DATASET = "transak"
TABLE_NAME = "i1_predictions"


# The @dsl.pipeline decorator defines this function as a pipeline blueprint.
@dsl.pipeline(
    name=PIPELINE_NAME,
    description="Artur's project Transak - Iteration 1 - An end-to-end pipeline " \
    "to get predictions from the transaction classifier.",
    pipeline_root=PIPELINE_ROOT, # type: ignore
)
def transak_i1_pipeline_predict(
    project_id: str = PROJECT_ID, # type: ignore
    region: str = REGION, # type: ignore
    model_name: str = "transak-i1-train-model",
    month: Optional[int] = None,
):
    # project_id = PROJECT_ID
    # model_name = "transak-i1-train-model"
    # month = "202508"
    print(f"Starting pipeline for month: {month}")
    """Defines the sequence of operations in the pipeline. Pipeline orchestrator will execute them."""
    # 1. Prediction Config Generator
    prediction_config = prediction_config_generator_op( # type: ignore
        prediction_month=month,
    )
    prediction_config.set_display_name("Generate Prediction Config")

    # 2. Get Prediction Data
    get_prediction_data = get_prediction_data_op( # type: ignore
        project_id=project_id,
        month=prediction_config.output,
        query=predict_data_query()
    )
    get_prediction_data.set_display_name("Get Prediction Data")

    # 3. Get Production Model
    get_prod_model = get_production_model_op( # type: ignore
        project=project_id,
        location=region,
        model_display_name=model_name
    )
    get_prod_model.set_display_name("Get Production Model")

    # Batch Prediction for Evaluation (Production Model)
    batch_predict_production = batch_predict_op( # type: ignore
        project=project_id,
        location=region,
        vertex_model=get_prod_model.outputs['production_model'],
        test_data=get_prediction_data.outputs['prediction_data'],
        experiment_name=""
    )
    batch_predict_production.set_display_name("Batch Predict: Production")

    # 5. Save Predictions
    save_predictions = save_predictions_op( # type: ignore
        project_id=project_id,
        region=region,
        predictions=batch_predict_production.outputs["predictions"],
        bigquery_prediction_table_fqtn=f"{project_id}.{DATASET}.{TABLE_NAME}",
        pipeline_run_id=dsl.PIPELINE_JOB_NAME_PLACEHOLDER,
    )
    save_predictions.set_display_name("Save Predictions")



# Compile and Run the Pipeline
if __name__ == "__main__":

    mode = sys.argv[1] if len(sys.argv) > 1 else "submit"
    package_path = f"{PIPELINE_NAME}.json"
    print(f"Executing pipeline script in '{mode}' mode.")

    # Get month from command line if provided
    month_arg = None
    if len(sys.argv) > 2:
        month_arg = sys.argv[2]

    # Compile the pipeline into a JSON (which is a form of YAML) file
    compiler.Compiler().compile(
        pipeline_func=transak_i1_pipeline_predict,
        package_path=f"{PIPELINE_NAME}.json",
    )
    print(f"Pipeline compiled successfully to {package_path}")

    if mode == "submit":
        aiplatform.init(project=PROJECT_ID, location=REGION)

        parameter_values={
            'project_id': PROJECT_ID,
            'region': REGION,
            'model_name': 'transak-i1-train-model'
        }
        parameter_values={}
        if month_arg:
            parameter_values['month'] = month_arg

        pipeline_job = aiplatform.PipelineJob(
            display_name=PIPELINE_JOB_NAME,
            template_path=package_path,
            parameter_values=parameter_values,
            enable_caching=False # Disable caching to ensure all new code runs
        )

        print(f"Submitting pipeline job '{PIPELINE_NAME}' to Vertex AI...")
        pipeline_job.submit()
