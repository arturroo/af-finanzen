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
    parser.add_argument("--vertex-model-uri", type=str, required=True, help="URI to the model registered in Vertex AI Model Registry.")
    parser.add_argument("--test-data-uri", type=str, required=True, help="URI of the test data.")
    parser.add_argument("--predictions-path", type=str, required=True, help="Path to save the predictions.")
    parser.add_argument("--experiment-name", type=str, required=True, help="Vertex AI Experiment name.")

    args = parser.parse_args()

    print(f"Initializing AI Platform for project {args.project} in {args.location}...")
    if args.experiment_name == "":
        aiplatform.init(project=args.project, location=args.location)
    else:
        aiplatform.init(project=args.project, location=args.location, experiment=args.experiment_name)

    # 3. Load the TensorFlow model
    loaded_model = tf.saved_model.load(args.vertex_model_uri)
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
    # This is really a oneliner, but I need to understand this so I do prediction step by step
    predict_fn = loaded_model.signatures['serving_default']
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
    # 6. Format and save predictions as a JSONL file
    # The predictions_path is now expected to be a directory.
    # We will create a file inside this directory with the required prefix.
    output_file_name = 'prediction.results-00000-of-00001' # Adhering to Vertex AI evaluation component requirements
    output_file_path = os.path.join(args.predictions_path, output_file_name)
    os.makedirs(args.predictions_path, exist_ok=True)

    print(f"Writing predictions to: {output_file_path}")

    with open(output_file_path, 'w') as f:
        for instance, pred in zip(instances, all_predictions):
            json_record = json.dumps({
                # "instance": instance_values,
                "instance": instance,
                "prediction": pred
            })
            f.write(json_record + '\n')
    
    print("Predictions saved successfully.")

if __name__ == "__main__":
    main()
