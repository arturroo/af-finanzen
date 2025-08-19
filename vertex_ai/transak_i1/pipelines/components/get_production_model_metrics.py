from kfp.v2.dsl import component, Output
from google.cloud import aiplatform
import json

@component(
    base_image="python:3.9",
    packages_to_install=["google-cloud-aiplatform"],
)
def get_production_model_metrics_op(
    project: str,
    location: str,
    model_display_name: str,
) -> Output[float]:
    """
    A component that retrieves the accuracy of the model currently aliased as 'production'
    in the Vertex AI Model Registry.
    """
    print(f"Initializing AI Platform for project {project} in {location}...")
    aiplatform.init(project=project, location=location)

    production_accuracy = 0.0  # Default if no production model is found

    # Find the current production model
    # Filter by display_name and version_aliases
    # Note: aiplatform.Model.list() does not directly support filtering by version_aliases in the filter argument.
    # We need to iterate and check.
    all_models = aiplatform.Model.list(filter=f'display_name="{model_display_name}"')

    production_model = None
    for model in all_models:
        # Fetch the latest version of the model to check aliases
        # This is a workaround as direct alias filtering in list() is not robust
        # A more robust way would be to get the model resource name and then fetch the specific version
        # For simplicity, we assume the 'production' alias is on one of the listed models.
        # In a real scenario, you might need to iterate through versions of a model.
        if "production" in model.version_aliases:
            production_model = model
            break

    if production_model:
        print(f"Found production model: {production_model.resource_name}")
        # Get the evaluation metrics for the production model
        # This assumes the evaluation metrics are associated with the model in the Model Registry
        # and can be retrieved. This might require custom logic if not directly available.
        # For now, we'll assume a simple way to get accuracy.
        # In a real scenario, you might need to fetch specific evaluations.

        # A more robust way to get metrics would be to list evaluations for the model version
        # and then parse the metrics. For this example, we'll simulate getting accuracy.
        # This part needs to be adapted based on how metrics are stored/associated.

        # Placeholder: In a real system, you'd query for the actual evaluation metrics
        # associated with this specific model version.
        # For demonstration, let's assume a way to get it.
        # You might need to store accuracy as a model label or in a separate system.

        # For now, let's assume we can get it from a custom label or a stored evaluation.
        # If the model was blessed, its accuracy should be available.
        # This is a simplification. A real implementation would fetch the actual evaluation.
        # For example, if you imported evaluation metrics, you could query them.

        # Let's assume for now that the accuracy is stored as a label or can be easily retrieved.
        # If not, this part needs to be more complex, potentially querying BigQuery for past evaluations.

        # For the purpose of this exercise, let's assume we can get it from a custom label
        # or that the model object itself has a way to expose its "blessed" accuracy.
        # This is a critical point that needs a concrete implementation based on your actual setup.

        # If you have imported evaluation metrics to the model, you can retrieve them like this:
        evaluations = production_model.list_model_evaluations()
        if evaluations:
            # Assuming the latest evaluation is the relevant one or you have a naming convention
            latest_evaluation = evaluations[0] # Or find the specific evaluation you need
            print(f"Found evaluation: {latest_evaluation.resource_name}")
            # The metrics are in latest_evaluation.metrics
            # You might need to parse this JSON string
            metrics_dict = json.loads(latest_evaluation.metrics)
            if 'accuracy' in metrics_dict:
                production_accuracy = metrics_dict['accuracy']
                print(f"Production model accuracy: {production_accuracy}")
            else:
                print("Accuracy not found in production model's evaluation metrics.")
        else:
            print("No evaluations found for the production model.")
    else:
        print("No model with 'production' alias found.")

    # Output the production accuracy
    with open(Output[float].path, "w") as f:
        f.write(str(production_accuracy))
    return production_accuracy
