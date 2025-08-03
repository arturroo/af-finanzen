import tensorflow as tf
import pandas as pd
import json
import numpy as np
from google.cloud import aiplatform
from src.common.utils import df2dataset
import argparse
import sys
import os

def main():
    parser = argparse.ArgumentParser(description="Perform batch predictions using a trained TensorFlow model.")
    parser.add_argument("--project", type=str, required=True, help="Google Cloud project ID.")
    parser.add_argument("--location", type=str, required=True, help="Google Cloud region.")
    parser.add_argument("--vertex-model-path", type=str, required=True, help="Path to the VertexModel artifact.")
    parser.add_argument("--test-data-uri", type=str, required=True, help="URI of the test data.")
    parser.add_argument("--predictions-path", type=str, required=True, help="Path to save the predictions.")
    parser.add_argument("--experiment-name", type=str, required=True, help="Vertex AI Experiment name.")

    args = parser.parse_args()

    print(f"Initializing AI Platform for project {args.project} in {args.location}...")
    aiplatform.init(project=args.project, location=args.location, experiment=args.experiment_name)

    # 1. Read the model resource name from the input artifact
    print(f"Reading model resource name from: {args.vertex_model_path}")
    with open(args.vertex_model_path, 'r') as f:
        model_resource_name = f.read().strip()
    print(f"Retrieved model resource name: {model_resource_name}")

    # 2. Get the model artifact URI from the Model Registry
    model_registry_object = aiplatform.Model(model_name=model_resource_name)
    model_artifact_uri = model_registry_object.uri
    print(f"Loading model from artifact URI: {model_artifact_uri}")

    # 3. Load the TensorFlow model
    loaded_model = tf.saved_model.load(model_artifact_uri)
    print("Model loaded successfully.")
    print(dir(loaded_model))

    # 4. Load and prepare the test data
    print(f"Loading test data from: {args.test_data_uri}")
    test_df = pd.read_csv(args.test_data_uri)
    
    # Keep original instances for the output file
    instances = test_df.to_dict(orient='records')

    # Convert DataFrame to tf.data.Dataset for consistent preprocessing
    prediction_dataset = df2dataset(test_df, shuffle=False, batch_size=32, mode='inference')

    # 5. Run predictions using the 'serving_default' signature
    print("Running predictions using 'serving_default' signature...")
    # This is reallye oneliner, but I need to understand this so I do prediction step by step
    #predictions_tensor = loaded_model.signatures['serving_default'](prediction_dataset)
    predict_fn = loaded_model.signatures['serving_default']
    # predict_fn(image_tensor=t1, metadata_tensor=t2)
    # predictions_tensor = predict_fn(prediction_dataset) # Commented out: Old prediction call
    all_predictions = []
    for batch in prediction_dataset:
        predictions_tensor = predict_fn(
            amount=batch['amount'],
            currency=batch['currency'],
            description=batch['description'],
            first_started_day=batch['first_started_day'],
            first_started_month=batch['first_started_month'],
            first_started_weekday=batch['first_started_weekday'],
            first_started_year=batch['first_started_year'],
            started_day=batch['started_day'],
            started_month=batch['started_month'],
            started_weekday=batch['started_weekday'],
            started_year=batch['started_year'],
            type=batch['type']
        )
        # The output of the model is a dictionary, so we need to extract the predictions.
        output_key = list(predictions_tensor.keys())[0]
        all_predictions.extend(predictions_tensor[output_key].numpy().tolist())
    
    print("Predictions generated successfully.")
    output_dir = os.path.dirname(args.predictions_path)
    os.makedirs(output_dir, exist_ok=True)

    # 6. Format and save predictions as a JSONL file
    print(f"Writing predictions to: {args.predictions_path}")
    with open(args.predictions_path, 'w') as f:
        for instance, pred in zip(instances, all_predictions):
            json_record = json.dumps({
                "instance": instance,
                "prediction": pred
            })
            f.write(json_record + '\n')
    
    print("Predictions saved successfully.")

if __name__ == "__main__":
    main()
