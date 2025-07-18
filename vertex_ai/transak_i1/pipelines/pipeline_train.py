import os
import sys
import time
from kfp import dsl,compiler
from google.cloud import aiplatform
from pipelines.components.data_prep import data_prep_op
from pipelines.components.trainer import train_model_op
from pipelines.components.evaluation import evaluate_model_op
from pipelines.components.register import register_model_op


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

# Define the Pipeline using the KFP DSL
# The @dsl.pipeline decorator defines this function as a pipeline blueprint.
@dsl.pipeline(
    name=PIPELINE_NAME,
    description="Artur's project Transak - Iteration 1 - An end-to-end pipeline " \
    "to train the transaction classifier. Framework TensorFlow Keras Functional API and Subclassing.",
    pipeline_root=PIPELINE_ROOT, # type: ignore
)
def transaction_classifier_pipeline(
    project_id: str = PROJECT_ID, # type: ignore
    num_epochs: int = 100,
    learning_rate: float = 0.0002,
    batch_size: int = 16,
    num_classes: int = 13,
    accuracy_threshold: float = 0.88,
    tensorboard_resource_name: str = TENSORBOARD_RESOURCE_NAME, # type: ignore
    serving_container_image_uri: str = SERVING_CONTAINER_IMAGE_URI, # type: ignore
    experiment_name: str = EXPERIMENT_NAME, # type: ignore
    run_name: str = PIPELINE_JOB_NAME, # type: ignore
):
    """Defines the sequence of operations in the pipeline. Pipeline orchestrator will execute them."""
    # 1. Data Preparation
    data_prep_task = data_prep_op( # type: ignore
        tensorboard_resource_name=tensorboard_resource_name,
        project_id=project_id,
        region=REGION,
        experiment_name=experiment_name,
        run_name=run_name,
    )
    # This task now has outputs, like `data_prep_task.outputs['train_data_path']`

    # 2. Model Training
    train_model_task = train_model_op( # type: ignore
        train_data_path=data_prep_task.outputs['train_data_path'],
        val_data_path=data_prep_task.outputs['val_data_path'],
        num_epochs=num_epochs,
        learning_rate=learning_rate,
        batch_size=batch_size,
        num_classes=num_classes,
        tensorboard_resource_name=tensorboard_resource_name,
        project_id=project_id,
        region=REGION,
        experiment_name=experiment_name,
        run_name=run_name
    )
    # This task will produce the final model artifact.
    
    # 3. Model Evaluation
    evaluate_model_task = evaluate_model_op( # type: ignore
        model=train_model_task.outputs['output_model_path'],
        test_data=data_prep_task.outputs['test_data_path'],
        tensorboard_resource_name=tensorboard_resource_name,
        project_id=project_id,
        region=REGION,
        experiment_name=experiment_name,
        run_name=run_name
    )

    # 4. Model Registration
    # with dsl.Condition(
    #     evaluate_model_task.outputs['metrics']['accuracy'].value >= accuracy_threshold, # type: ignore
    #     name="Register Model Condition"
    # ):
    register_model_task = register_model_op( # type: ignore
        metrics=evaluate_model_task.outputs['metrics'],
        model=train_model_task.outputs['output_model_path'],
        model_display_name=f"{PIPELINE_NAME}-model",
        container_image_uri=serving_container_image_uri,
        accuracy_threshold=accuracy_threshold,
        tensorboard_resource_name=tensorboard_resource_name,
        project_id=project_id,
        region=REGION,
        experiment_name=experiment_name,
        run_name=run_name
    )

    

# Compile and Run the Pipeline 
if __name__ == "__main__":

    mode = sys.argv[1] if len(sys.argv) > 1 else "submit"
    package_path = f"{PIPELINE_NAME}.json"
    experiment_name = EXPERIMENT_NAME
    # run_name = f"{experiment_name}-{int(time.time())}"
    # run_name = f"run-{int(time.time())}"
    local_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
    run_name = f"run-{local_time}"
    print(f"Executing pipeline script in '{mode}' mode.")
    
    # Compile the pipeline into a JSON (which is a form of YAML) file
    compiler.Compiler().compile(
        pipeline_func=transaction_classifier_pipeline, # type: ignore
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
            description="Tracking experiments for the Transak Iteration 1 Vertex AI Pipeline."
        )

        tb = aiplatform.Tensorboard(TENSORBOARD_RESOURCE_NAME) # type: ignore
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
                    'tensorboard_resource_name': TENSORBOARD_RESOURCE_NAME,
                    'accuracy_threshold': 0.88,
                    'experiment_name': EXPERIMENT_NAME,
                    'run_name': run_name,
                },
                enable_caching=False # Disable caching to ensure all new code runs
            )

            print(f"Submitting pipeline job '{PIPELINE_NAME}' to Vertex AI...")
            #aiplatform.start_run(PIPELINE_NAME)
            # pipeline_job.run()
            pipeline_job.submit(experiment=experiment)
            #aiplatform.end_run()
