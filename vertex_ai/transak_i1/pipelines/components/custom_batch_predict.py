from kfp.v2.dsl import (
    component,
    Input,
    Output,
    Model,
    Dataset,
    Artifact,
)
from google_cloud_pipeline_components.types.artifact_types import VertexModel


@component(
    base_image="tensorflow/tensorflow:2.16.1",
    packages_to_install=["pandas", "fsspec", "gcsfs", "db-dtypes", "google-cloud-aiplatform", "google-cloud-pipeline-components"],
)
def custom_batch_predict_op(
    project: str,
    location: str,
    vertex_model: Input[VertexModel],
    test_data: Input[Dataset],
    predictions: Output[Artifact],
):
    """
    A custom component to perform batch predictions using a trained TensorFlow model
    retrieved from the Vertex AI Model Registry.
    """
    import tensorflow as tf
    import pandas as pd
    import json
    import numpy as np
    from google.cloud import aiplatform

    print(f"Initializing AI Platform for project {project} in {location}...")
    aiplatform.init(project=project, location=location)

    # 1. Read the model resource name from the input artifact
    print(f"Reading model resource name from: {vertex_model.path}")
    with open(vertex_model.path, 'r') as f:
        model_resource_name = f.read().strip()
    print(f"Retrieved model resource name: {model_resource_name}")

    # 2. Get the model artifact URI from the Model Registry
    # 2. Get the model artifact URI from the Model Registry
    model_registry_object = aiplatform.Model(model_name=model_resource_name)
    model_artifact_uri = model_registry_object.uri
    print(f"Loading model from artifact URI: {model_artifact_uri}")

    # 3. Load the TensorFlow model
    loaded_model = tf.saved_model.load(model_artifact_uri)
    predict_fn = loaded_model.signatures['serving_default']
    print("Model loaded successfully.")

    # 4. Load and prepare the test data
    print(f"Loading test data from: {test_data.uri}")
    test_df = pd.read_csv(test_data.uri)
    
    # Keep original instances for the output file
    instances = test_df.to_dict(orient='records')

    # Drop columns that are not model features
    if 'i1_true_label' in test_df.columns:
        test_df = test_df.drop(columns=['i1_true_label'])
    if 'i1_true_label_id' in test_df.columns:
        test_df = test_df.drop(columns=['i1_true_label_id'])
    if 'tid' in test_df.columns:
        test_df = test_df.drop(columns=['tid'])

    # Convert the pandas DataFrame to a dictionary of Tensors for the model
    input_tensors = {}
    for name in test_df.columns:
        if test_df[name].dtype in [np.float64, np.int64]: # Check for numerical types that might be float64 or int64
            input_tensors[name] = tf.constant(test_df[name].values, dtype=tf.float32)
        else:
            input_tensors[name] = tf.constant(test_df[name].values)
    
    # 5. Run predictions
    print("Running predictions...")
    predictions_tensor = predict_fn(**input_tensors)
    
    # Extract the prediction results
    output_key = list(predictions_tensor.keys())[0]
    predictions_list = predictions_tensor[output_key].numpy().tolist()
    print("Predictions generated successfully.")

    # 6. Format and save predictions as a JSONL file
    print(f"Writing predictions to: {predictions.path}")
    with open(predictions.path, 'w') as f:
        for instance, pred in zip(instances, predictions_list):
            json_record = json.dumps({
                "instance": instance,
                "prediction": pred
            })
            f.write(json_record + '\n')
    
    print("Predictions saved successfully.")
