from kfp.v2.dsl import component

@component(
    base_image="python:3.9",
    packages_to_install=["google-cloud-aiplatform"],
)
def get_production_model_metrics_op(
    project: str,
    location: str,
    model_display_name: str,
) -> float:
    """
    A component that retrieves the key metric (auPrc or accuracy) of the model 
    currently aliased as 'production' in the Vertex AI Model Registry.
    """
    from google.cloud import aiplatform
    import json

    print(f"Initializing AI Platform for project {project} in {location}...")
    aiplatform.init(project=project, location=location)

    production_metric_value = 0.0

    all_models = aiplatform.Model.list(filter=f'display_name="{model_display_name}"')

    production_model = None
    for model in all_models:
        if "production" in model.version_aliases:
            production_model = model
            break

    if production_model:
        print(f"Found production model: {production_model.resource_name}")
        evaluations = production_model.list_model_evaluations()
        if evaluations:
            latest_evaluation = evaluations[0]
            print(f"Found evaluation: {latest_evaluation.resource_name}")
            
            metrics = latest_evaluation.metrics
            metrics_dict = {}
            if isinstance(metrics, str):
                try:
                    metrics_dict = json.loads(metrics)
                except json.JSONDecodeError:
                    print(f"Could not parse metrics string: {metrics}")
            elif isinstance(metrics, dict):
                metrics_dict = metrics

            if 'auPrc' in metrics_dict:
                production_metric_value = metrics_dict['auPrc']
                print(f"Production model auPrc: {production_metric_value}")
            elif 'accuracy' in metrics_dict:
                production_metric_value = metrics_dict['accuracy']
                print(f"Production model accuracy: {production_metric_value}")
            else:
                print("Neither 'auPrc' nor 'accuracy' found in production model's evaluation metrics.")
        else:
            print("No evaluations found for the production model.")
    else:
        print("No model with 'production' alias found.")

    return production_metric_value
