import os
from kfp import dsl,compiler
# from google.cloud import aiplatform
from pipeline.components.data_prep import data_prep_op
from pipeline.components.training import train_model_op
from pipeline.components.evaluation import evaluate_model_op

# Define Your Pipeline Configuration
PROJECT_ID = os.getenv("VERTEX_PROJECT_ID")
REGION = os.getenv("VERTEX_REGION")
PIPELINE_BUCKET = os.getenv("VERTEX_BUCKET") # gcs bucket for pipeline artifacts
PIPELINE_NAME = os.getenv("PIPELINE_NAME", "transak-i1-train-pipeline-subclassing")
if not all([PROJECT_ID, REGION, PIPELINE_BUCKET]):
    raise ValueError(
        "The following environment variables must be set: "
        "VERTEX_PROJECT_ID, VERTEX_REGION, PIPELINE_BUCKET"
    )
PIPELINE_ROOT = f"{PIPELINE_BUCKET}/pipelines/{PIPELINE_NAME}"

# Define the Pipeline using the KFP DSL
# The @dsl.pipeline decorator defines this function as a pipeline blueprint.
@dsl.pipeline(
    name=PIPELINE_NAME,
    description="Artur's project Transak - Iteration 1 - An end-to-end pipeline " \
    "to train the transaction classifier. Framework TensorFlow Keras Functional API and Subclassing.",
    pipeline_root=PIPELINE_ROOT, # type: ignore GCS path for pipeline artifacts
)
def transaction_classifier_pipeline(
    project_id: str,
    num_epochs: int = 100,
    learning_rate: float = 0.0002,
    batch_size: int = 16,
    num_classes: int = 13
):
    """Defines the sequence of operations in the pipeline. Pipeline orchestrator will execute them."""
    # 1. Data Preparation
    data_prep_task = data_prep_op( # type: ignore
        project_id=project_id
    )
    # This task now has outputs, like `data_prep_task.outputs['train_data_path']`

    # 2. Model Training
    train_model_task = train_model_op( # type: ignore
        train_data_path=data_prep_task.outputs['train_data_path'],
        val_data_path=data_prep_task.outputs['val_data_path'],
        num_epochs=num_epochs,
        learning_rate=learning_rate,
        batch_size=batch_size,
        num_classes=num_classes
    )
    # This task will produce the final model artifact.
    
    # 3. Model Evaluation
    evaluate_model_task = evaluate_model_op( # type: ignore
        model=train_model_task.outputs['output_model_path'],
        test_data=data_prep_task.outputs['test_data_path']
    )

# Compile and Run the Pipeline 
if __name__ == "__main__":
    # Compile the pipeline into a JSON (which is a form of YAML) file
    compiler.Compiler().compile(
        pipeline_func=transaction_classifier_pipeline, # type: ignore
        package_path=f"{PIPELINE_NAME}.json",
    )
    