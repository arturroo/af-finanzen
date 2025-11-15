import os
import sys
import time
from kfp import dsl,compiler
from google.cloud import aiplatform
from google.cloud import storage
from pipelines.components.data_splits import data_splits_op
from pipelines.components.trainer import train_model_op
from pipelines.components.register import register_model_op
from pipelines.components.bq_config_generator import bq_config_generator_op
from pipelines.components.bless_model import bless_model_op
from pipelines.components.evaluation import model_evaluation_op
from pipelines.components.get_production_model import get_production_model_op
from pipelines.components.batch_predict import batch_predict_op
from google_cloud_pipeline_components.v1.bigquery import BigqueryQueryJobOp
from src.common.base_sql import train_data_query
from pipelines.components.get_production_model import get_production_model_op
from pipelines.components.bless_or_not_to_bless import bless_or_not_to_bless_op
from pipelines.components.create_monitoring_baseline import create_monitoring_baseline_op
from pipelines.components.setup_monitoring import setup_monitoring_op
from typing import List


# Define Your Pipeline Configuration
PROJECT_ID = os.getenv("VERTEX_PROJECT_ID")
REGION = os.getenv("VERTEX_REGION")
PIPELINE_BUCKET = os.getenv("VERTEX_BUCKET") # gcs bucket for pipeline artifacts
TENSORBOARD_RESOURCE_NAME = os.getenv("TENSORBOARD_RESOURCE_NAME")
PIPELINE_NAME = os.getenv("PIPELINE_NAME", "transak-i1-train")
SERVING_CONTAINER_IMAGE_URI = os.getenv("SERVING_CONTAINER_IMAGE_URI", "europe-docker.pkg.dev/vertex-ai-restricted/prediction/tf_opt-cpu.2-17:latest")
NOTIFICATION_CHANNEL = os.getenv("NOTIFICATION_CHANNEL")
USER_EMAILS = list(os.getenv("USER_EMAILS", "artur.fejklowicz@gmail.com").split(","))


if not all([PROJECT_ID, REGION, PIPELINE_BUCKET, TENSORBOARD_RESOURCE_NAME, NOTIFICATION_CHANNEL]):
    raise ValueError(
        "The following environment variables must be set: VERTEX_PROJECT_ID, VERTEX_REGION, PIPELINE_BUCKET, TENSORBOARD_RESOURCE_NAME, NOTIFICATION_CHANNEL"
    )
PIPELINE_ROOT = f"{PIPELINE_BUCKET}/pipelines/{PIPELINE_NAME}"
PIPELINE_TEMPLATE_GCS_PATH = f"{PIPELINE_ROOT}/{PIPELINE_NAME}.json"
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
    notification_channel: str = NOTIFICATION_CHANNEL, # type: ignore
    user_emails: List[str] = USER_EMAILS, # type: ignore
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

    # 2. Get golden data from BigQuery
    golden_data = BigqueryQueryJobOp(
        project=project_id,
        location=REGION,
        query=train_data_query(),
        job_configuration_query=bq_config_generator.output,
    )
    golden_data.set_display_name("Get Golden Data")

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

   # Get production model
    get_prod_model = get_production_model_op( # type: ignore
        project=project_id,
        location=REGION,
        model_display_name=f"{PIPELINE_NAME}-model",
    )
    get_prod_model.set_display_name("Get Production Model")

    # Batch Prediction for Evaluation (Production Model)
    batch_predict_production = batch_predict_op( # type: ignore
        project=project_id,
        location=REGION,
        vertex_model=get_prod_model.outputs['production_model'],
        test_data=data_splits.outputs['test_data'],
        experiment_name=experiment_name,
    )
    batch_predict_production.set_display_name("Batch Predict: Production")

    # Model Evaluation (Production Model)
    evaluate_model_production = model_evaluation_op( # type: ignore
        project=project_id,
        location=REGION,
        predictions=batch_predict_production.outputs['predictions'],
        class_labels=data_splits.outputs['class_labels'],
        vertex_model=get_prod_model.outputs['production_model'], # Associate with production model
        evaluation_display_name=f"{run_name}-production-evaluation"
        # cache_trigger11=True
    )
    evaluate_model_production.set_display_name("Evaluate Model: Production")

    # 5. Batch Prediction for Evaluation
    batch_predict_candidate = batch_predict_op( # type: ignore
        project=project_id,
        location=REGION,
        vertex_model=register_model.outputs['candidate_model'],
        test_data=data_splits.outputs['test_data'],
        experiment_name=experiment_name,
    )
    batch_predict_candidate.set_display_name("Batch Predict: Candidate")

    # 6. Model Evaluation (Candidate)
    evaluate_model_candidate = model_evaluation_op( # type: ignore
        project=project_id,
        location=REGION,
        predictions=batch_predict_candidate.outputs['predictions'],
        class_labels=data_splits.outputs['class_labels'],
        vertex_model=register_model.outputs['candidate_model'],
        evaluation_display_name=f"{run_name}-candidate-evaluation"
        # cache_trigger11=True
    )
    evaluate_model_candidate.set_display_name("Evaluate Model: Candidate")

    # 7. Compare metrics and decide whether to bless
    to_bless_or_not_to_bless = bless_or_not_to_bless_op(
        candidate_metrics=evaluate_model_candidate.outputs['evaluation_metrics'],
        production_metrics=evaluate_model_production.outputs['evaluation_metrics'],
    )
    to_bless_or_not_to_bless.set_display_name("Production vs Candidate")

    # 8. Bless Model (Conditional Step)
    with dsl.Condition(
        to_bless_or_not_to_bless.outputs['decision'] == 'bless',
        name="Bless Model Condition"
    ):
        bless_model = bless_model_op(
            vertex_model=register_model.outputs['candidate_model'],
            project=project_id,
            location=REGION
        )
        bless_model.set_display_name("Bless Model")

        # Create monitoring baseline
        batch_predict_monitoring = batch_predict_op(
            project=project_id,
            location=REGION,
            vertex_model=register_model.outputs['candidate_model'],
            test_data=data_splits.outputs['train_data'],  # Use training data for baseline
            experiment_name=experiment_name,
        )
        batch_predict_monitoring.set_display_name("Batch Predict: Monitoring Baseline")

        create_baseline = create_monitoring_baseline_op(
            predictions_artifact=batch_predict_monitoring.outputs['predictions']
        )
        create_baseline.set_display_name("Create Monitoring Baseline")

        # Setup monitoring
        setup_monitoring = setup_monitoring_op(
            project=project_id,
            location=REGION,
            vertex_model=register_model.outputs['candidate_model'],
            baseline_dataset=create_baseline.outputs['monitoring_baseline'],
            notification_channel=notification_channel,
            user_emails=user_emails,
            display_name_prefix=f"{PIPELINE_NAME}-monitor"
        )
        setup_monitoring.set_display_name("Setup Model Monitoring")

    

# Compile and Run the Pipeline
if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "compile"
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
            "user_emails": USER_EMAILS,
            "notification_channel": NOTIFICATION_CHANNEL,
        }
    )
    print(f"Pipeline compiled successfully to {package_path}")

    # Upload the compiled pipeline to GCS
    bucket_name = PIPELINE_BUCKET.replace("gs://", "")
    blob_path = PIPELINE_TEMPLATE_GCS_PATH.replace(f"gs://{bucket_name}/", "")
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    blob.upload_from_filename(package_path)
    print(f"Compiled pipeline uploaded to {PIPELINE_TEMPLATE_GCS_PATH}")

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
                # enable_caching=False  # Disable caching to ensure all new code runs
                enable_caching=True  # Enable caching to skip already executed steps
            )

            print(f"Submitting pipeline job '{PIPELINE_NAME}' to Vertex AI...")
            pipeline_job.submit(experiment=experiment)
            print(f"Pipeline job '{PIPELINE_NAME}' submitted successfully.")
