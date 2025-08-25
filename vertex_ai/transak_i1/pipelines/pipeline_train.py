import os
import sys
import time
from kfp import dsl,compiler
from google.cloud import aiplatform
# from pipelines.components.data_prep import data_prep_op
from pipelines.components.data_splits import data_splits_op
from pipelines.components.trainer import train_model_op
from pipelines.components.register import register_model_op
from pipelines.components.bq_config_generator import bq_config_generator_op
from pipelines.components.bless_model import bless_model_op
from pipelines.components.evaluation import model_evaluation_op
from pipelines.components.get_production_model_metrics import get_production_model_metrics_op
from pipelines.components.utils import get_artifact_uri_list, read_json_labels_op
#from pipelines.components.batch_predict import batch_predict_op
from pipelines.components.batch_predict import batch_predict_op
from google_cloud_pipeline_components.v1.bigquery import BigqueryQueryJobOp
from google_cloud_pipeline_components.v1.model_evaluation import ModelEvaluationClassificationOp
from google_cloud_pipeline_components.preview.model_evaluation import ModelImportEvaluationOp
# from google_cloud_pipeline_components.v1.batch_predict_job import ModelBatchPredictOp
from src.common.base_sql import raw_data_query
# from google.cloud import bigquery


# Define Your Pipeline Configuration
PROJECT_ID = os.getenv("VERTEX_PROJECT_ID")
REGION = os.getenv("VERTEX_REGION")
PIPELINE_BUCKET = os.getenv("VERTEX_BUCKET") # gcs bucket for pipeline artifacts
TENSORBOARD_RESOURCE_NAME = os.getenv("TENSORBOARD_RESOURCE_NAME")
PIPELINE_NAME = os.getenv("PIPELINE_NAME", "transak-i1-train")
SERVING_CONTAINER_IMAGE_URI = os.getenv("SERVING_CONTAINER_IMAGE_URI", "europe-docker.pkg.dev/vertex-ai-restricted/prediction/tf_opt-cpu.2-17:latest")
if not all([PROJECT_ID, REGION, PIPELINE_BUCKET, TENSORBOARD_RESOURCE_NAME]):
    raise ValueError(
        "The following environment variables must be set: VERTEX_PROJECT_ID, VERTEX_REGION, PIPELINE_BUCKET, TENSORBOARD_RESOURCE_NAME"
    )
PIPELINE_ROOT = f"{PIPELINE_BUCKET}/pipelines/{PIPELINE_NAME}"
EXPERIMENT_NAME = f"{PIPELINE_NAME}-experiment"
PIPELINE_JOB_NAME = f"{PIPELINE_NAME}-job"


print(f"projec_id: {PROJECT_ID}")

# Define the Pipeline using the KFP DSL
# The @dsl.pipeline decorator defines this function as a pipeline blueprint.
@dsl.pipeline(
    name=PIPELINE_NAME,
    description="Artur's project Transak - Iteration 1 - An end-to-end pipeline " 
    "to train the transaction classifier. Framework TensorFlow Keras Functional API and Subclassing.",
    pipeline_root=PIPELINE_ROOT, # type: ignore
)
def transak_i1_pipeline_train(
    project_id: str,
    num_epochs: int = 100,
    learning_rate: float = 0.0002,
    batch_size: int = 16,
    num_classes: int = 13,
    target_column: str = "i1_true_label_id",
    tensorboard_resource_name: str = TENSORBOARD_RESOURCE_NAME, # type: ignore
    serving_container_image_uri: str = SERVING_CONTAINER_IMAGE_URI, # type: ignore
    experiment_name: str = EXPERIMENT_NAME, # type: ignore
    run_name: str = PIPELINE_JOB_NAME, # type: ignore
):
    """Defines the sequence of operations in the pipeline. Pipeline orchestrator will execute them."""
    # 1. Generate BigQuery job configuration
    bq_config_generator = bq_config_generator_op(
        project_id=project_id,
        pipeline_job_name=dsl.PIPELINE_JOB_NAME_PLACEHOLDER,
        dataset_id="vp_transak_i1_train",
        table_name_prefix="golden_data"
    )
    bq_config_generator.set_display_name("Generate BQ Config")

    # 2. Get Golden Data
    golden_data = BigqueryQueryJobOp(
        project=project_id,
        location=REGION,
        query=raw_data_query(),
        job_configuration_query=bq_config_generator.output
    )
    golden_data.set_display_name("Create Golden Data")

    # 2. Train, val, test split
    data_splits = data_splits_op( # type: ignore
        golden_data_table=golden_data.outputs['destination_table'],
        project_id=project_id,
        region=REGION,
        target_column=target_column,
    )
    data_splits.set_display_name("Create Data Splits")

    # 3. Model Training
    train_model = train_model_op( # type: ignore
        train_data=data_splits.outputs['train_data'],
        val_data=data_splits.outputs['val_data'],
        num_epochs=num_epochs,
        learning_rate=learning_rate,
        batch_size=batch_size,
        num_classes=num_classes,
        tensorboard_resource_name=tensorboard_resource_name,
        project_id=project_id,
        region=REGION,
        experiment_name=experiment_name,
    )
    train_model.set_display_name("Train Model")
    train_model.set_caching_options(False)

    # 4. Model Registration
    register_model = register_model_op( # type: ignore
        model=train_model.outputs['output_model'],
        model_display_name=f"{PIPELINE_NAME}-model",
        serving_container_image_uri=serving_container_image_uri,
        project_id=project_id,
        region=REGION,
        experiment_name=experiment_name,
    )
    register_model.set_display_name("Register Model")

    # 5. Batch Prediction for Evaluation
    batch_predict_for_evaluation = batch_predict_op(
        project=project_id,
        location=REGION,
        vertex_model=register_model.outputs['vertex_model'],
        test_data=data_splits.outputs['test_data'],
        experiment_name=experiment_name,
    )
    batch_predict_for_evaluation.set_display_name("Batch Predict")

    # 6. Model Evaluation (Custom)
    evaluation_task = model_evaluation_op(
        project=project_id,
        location=REGION,
        predictions=batch_predict_for_evaluation.outputs['predictions'],
        class_labels=data_splits.outputs['class_labels'],
        vertex_model=register_model.outputs['vertex_model'],
        cache_trigger5=True
    )
    evaluation_task.set_display_name("Evaluate Model (Custom)")

    # Get production model metrics
    get_prod_model_metrics = get_production_model_metrics_op(
        project=project_id,
        location=REGION,
        model_display_name=f"{PIPELINE_NAME}-model",
    )
    get_prod_model_metrics.set_display_name("Get Production Model Metrics")

    # # 8. Bless Model (Conditional Step)
    # with dsl.Condition(
    #     evaluate_model_task.outputs['evaluation_metrics'].accuracy >= get_prod_model_metrics.output, # type: ignore
    #     name="Bless Model Condition"
    # ):
    #     bless_model = bless_model_op(
    #         vertex_model=register_model.outputs['vertex_model'],
    #         metrics=evaluate_model_task.outputs['evaluation_metrics'],
    #         production_accuracy=get_prod_model_metrics.output,
    #         project=project_id,
    #         location=REGION,
    #     )
    #     bless_model.set_display_name("Bless Model")

    

# Compile and Run the Pipeline
if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "submit"
    package_path = f"{PIPELINE_NAME}.json"
    experiment_name = EXPERIMENT_NAME
    local_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
    run_name = f"run-{local_time}"
    print(f"Executing pipeline script in '{mode}' mode.")

    # Compile the pipeline into a JSON (which is a form of YAML) file
    compiler.Compiler().compile(
        pipeline_func=transak_i1_pipeline_train,  # type: ignore
        package_path=f"{PIPELINE_NAME}.json",
        pipeline_parameters={
            "project_id": PROJECT_ID,
            "target_column": "i1_true_label_id",
        }
    )
    print(f"Pipeline compiled successfully to {package_path}")

    if mode == "submit":
        aiplatform.init(
            project=PROJECT_ID,
            location=REGION,
            experiment=EXPERIMENT_NAME,
            experiment_tensorboard=TENSORBOARD_RESOURCE_NAME,
        )
        aiplatform.autolog()

        experiment = aiplatform.Experiment.get_or_create(
            experiment_name=EXPERIMENT_NAME,
            description="Tracking experiments for the Transak Iteration 1 Vertex AI Pipeline.",
        )

        tb = aiplatform.Tensorboard(TENSORBOARD_RESOURCE_NAME)  # type: ignore
        experiment.assign_backing_tensorboard(tb)
        print(f"Tensorboard resource name: {tb.resource_name}")

        print(f"Experiment name: '{EXPERIMENT_NAME}'")
        print(f"Experiment run name: '{run_name}'")
        with aiplatform.start_run(run=run_name, tensorboard=TENSORBOARD_RESOURCE_NAME) as experiment_run:
            print(f"Started experiment run '{run_name}' in experiment '{EXPERIMENT_NAME}'")
            pipeline_job = aiplatform.PipelineJob(
                display_name=PIPELINE_JOB_NAME,
                template_path=package_path,
                parameter_values={
                    "tensorboard_resource_name": TENSORBOARD_RESOURCE_NAME,
                    "experiment_name": EXPERIMENT_NAME,
                    "run_name": run_name,
                    "target_column": "i1_true_label_id",
                },
                #enable_caching=False  # Disable caching to ensure all new code runs
                enable_caching=True  # Enable caching to skip already executed steps
            )

            print(f"Submitting pipeline job '{PIPELINE_NAME}' to Vertex AI...")
            pipeline_job.submit(experiment=experiment)
            print(f"Pipeline job '{PIPELINE_NAME}' submitted successfully.")
