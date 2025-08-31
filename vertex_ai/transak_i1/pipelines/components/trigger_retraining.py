from kfp.v2.dsl import component

@component(
    base_image='python:3.9',
    packages_to_install=["google-cloud-aiplatform"],
)
def trigger_retraining_op(
    project_id: str,
    region: str,
    pipeline_name: str,
    pipeline_template_path: str,
):
    """
    A component that triggers a new run of the training pipeline.
    """
    from google.cloud import aiplatform

    aiplatform.init(project=project_id, location=region)

    pipeline_job = aiplatform.PipelineJob(
        display_name=f"Retraining job for {pipeline_name}",
        template_path=pipeline_template_path,
        # parameter_values can be set here if needed
    )

    pipeline_job.submit()
    print(f"Submitted retraining pipeline job: {pipeline_job.resource_name}")
