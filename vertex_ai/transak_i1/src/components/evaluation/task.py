import argparse
import json
import pandas as pd
import numpy as np
import os
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    log_loss,
    confusion_matrix,
    precision_recall_fscore_support,
    f1_score,
    accuracy_score
)
from google.cloud import aiplatform, storage
from google.cloud.aiplatform import gapic

# Initialize Google Cloud Storage client
storage_client = storage.Client()

def _read_gcs_jsonl(gcs_uri: str) -> list:
    """Reads a JSONL file from GCS into a list of dictionaries."""
    path_parts = gcs_uri.replace("gs://", "").split("/")
    bucket_name = path_parts[0]
    blob_prefix = "/".join(path_parts[1:])

    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=blob_prefix)

    jsonl_blob = None
    for blob in blobs:
        if "prediction.results-" in blob.name: # prediction file has not extention, just shard indicator # and blob.name.endswith((".jsonl", ".json")):
            jsonl_blob = blob
            break
    
    if not jsonl_blob:
        raise FileNotFoundError(f"No JSONL file found at {gcs_uri} with 'prediction.results' in name.")

    print(f"Reading JSONL from gs://{bucket_name}/{jsonl_blob.name}")
    content = jsonl_blob.download_as_text()
    return [json.loads(line) for line in content.splitlines() if line.strip()]

def _read_gcs_json(gcs_uri: str) -> dict:
    """Reads a JSON file from GCS into a dictionary."""
    path_parts = gcs_uri.replace("gs://", "").split("/")
    bucket_name = path_parts[0]
    blob_name = "/".join(path_parts[1:])

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    print(f"Reading JSON from gs://{bucket_name}/{blob_name}")
    return json.loads(blob.download_as_text())

def main():
    parser = argparse.ArgumentParser(description="Model Evaluation Script.")
    parser.add_argument("--predictions_uri", type=str, required=True, help="GCS URI to the batch predictions JSONL.")
    parser.add_argument("--class_labels_uri", type=str, required=True, help="GCS URI to the class labels JSON.")
    parser.add_argument("--output_path", type=str, required=True, help="Local path to save the evaluation metrics JSON.")
    parser.add_argument("--target_column", type=str, default='i1_true_label_id', help="Name of the target column in the instance data.")
    parser.add_argument("--project", type=str, required=True, help="Google Cloud project ID.")
    parser.add_argument("--location", type=str, required=True, help="Google Cloud location.")
    parser.add_argument("--model_resource_path", type=str, required=True, help="Path to the Vertex AI model resource name file.")
    parser.add_argument("--evaluation_display_name", type=str, required=True, help="Display name for the model evaluation.")


    args = parser.parse_args()

    aiplatform.init(project=args.project, location=args.location)

    # Read the model resource name from the input artifact
    print(f"Reading model resource name from: {args.model_resource_path}")
    with open(args.model_resource_path, 'r') as f:
        model_resource_name = f.read().strip()
    print(f"Retrieved model resource name: {model_resource_name}")

    print("Loading predictions and ground truth...")
    predictions_list = _read_gcs_jsonl(args.predictions_uri)
    
    # Extract ground truth and prediction logits
    y_true = np.array([item["instance"][args.target_column] for item in predictions_list])
    y_pred_logits = np.array([item["prediction"] for item in predictions_list])

    # Apply softmax to convert logits to probabilities for metric calculations
    def softmax(x):
        """Compute softmax values for each sets of scores in x."""
        e_x = np.exp(x - np.max(x, axis=1, keepdims=True))
        return e_x / e_x.sum(axis=1, keepdims=True)

    y_pred_proba = softmax(y_pred_logits)
    y_pred = np.argmax(y_pred_proba, axis=1)

    print(f"Found {len(y_true)} records for evaluation.")

    print("Loading class labels...")
    class_labels = _read_gcs_json(args.class_labels_uri)

    # --- Calculate Core Metrics ---
    print("Calculating core metrics...")
    au_prc = average_precision_score(y_true, y_pred_proba, average='micro')
    au_roc = roc_auc_score(y_true, y_pred_proba, average='micro', multi_class='ovr')
    logloss = log_loss(y_true, y_pred_proba)

    # --- Calculate Confidence Metrics (Corrected) ---
    print("Calculating confidence metrics...")
    confidence_metrics = []

    # 1. CORRECT: Use all unique probability scores from the model as thresholds.
    #    We flatten the probability array to get all scores from all classes.
    all_probabilities = y_pred_proba.ravel() # flatten matrix into long vector later for unique
    confidence_thresholds = np.unique(np.concatenate(([0.0, 1.0], all_probabilities)))
    # Sort in descending order to build the curve correctly
    confidence_thresholds = np.sort(confidence_thresholds)[::-1] # np.sort has no desc switch, and best practice is to present thresholds in desc

    print(f"Generating metrics for {len(confidence_thresholds)} unique thresholds...")

    num_classes = len(class_labels)
    total_instances = len(y_true)
    total_possible_negatives = total_instances * (num_classes - 1) # -1 because in multiclass there is always 1 positive and num_classes - 1 negative

    annotation_specs_list = [
        {"id": label_id, "displayName": label_name}
        for label_id, label_name in sorted(class_labels.items(), key=lambda item: int(item[0]))
    ]

    for threshold in confidence_thresholds:
        # Get the predicted class and its probability
        y_pred_class = np.argmax(y_pred_proba, axis=1)
        y_pred_max_proba = np.max(y_pred_proba, axis=1)

        # Filter predictions based on the confidence threshold
        valid_indices = y_pred_max_proba >= threshold # numpy boolean masking - returns list of booleans

        y_true_filtered = y_true[valid_indices] # returns numpy with only valueas where mask is True
        y_pred_filtered = y_pred_class[valid_indices]

        confusion_matrix_dict = {}

        # --- Metric Calculations for this threshold ---
        if len(y_true_filtered) == 0:
            # If no predictions meet the threshold, all are negative predictions.
            # All probabilities are smaller then the threshold
            tp_count = 0
            fp_count = 0
            fn_count = total_instances # All true instances were missed.
            tn_count = total_possible_negatives

            precision_micro = 1.0 # Convention: No positive predictions means perfect precision
            recall_micro = 0.0
            f1_micro = 0.0
            f1_macro = 0.0
            false_positive_rate = 0.0

            # Create an all-zero confusion matrix for the empty case
            zero_matrix = [[0] * num_classes for _ in range(num_classes)]
            confusion_matrix_dict = {
                "annotationSpecs": annotation_specs_list,
                "rows": [{"row": row_values} for row_values in zero_matrix]
            }

        else:
            # Calculate confusion matrix on the *filtered* data
            cm_filtered = confusion_matrix(y_true_filtered, y_pred_filtered, labels=range(num_classes))

            # Calculate micro-averaged counts
            tp_count = int(np.diag(cm_filtered).sum())
            fp_count = int(cm_filtered.sum() - tp_count)

            # 2. CORRECT: FN = All true instances minus the ones we correctly identified.
            fn_count = total_instances - tp_count
            tn_count = total_possible_negatives - fp_count

            # Calculate micro-averaged precision and recall
            precision_micro = tp_count / (tp_count + fp_count) if (tp_count + fp_count) > 0 else 1.0
            recall_micro = tp_count / (tp_count + fn_count) if (tp_count + fn_count) > 0 else 0.0

            # False Positive Rate
            false_positive_rate = fp_count / (fp_count + tn_count) if (fp_count + tn_count) > 0 else 0.0

            # F1 scores
            f1_micro = 2 * (precision_micro * recall_micro) / (precision_micro + recall_micro) if (precision_micro + recall_micro) > 0 else 0.0
            f1_macro = f1_score(y_true_filtered, y_pred_filtered, average='macro', labels=range(num_classes), zero_division=0)

            # NEW: Format the calculated confusion matrix for the schema
            # The schema expects a list of dictionaries, where each dict is {"row": [values...]}
            confusion_matrix_dict = {
                "annotationSpecs": annotation_specs_list,
                "rows": [{"row": row_values} for row_values in cm_filtered.tolist()]
            }

        confidence_metrics.append({
            "confidenceThreshold": float(threshold),
            # "maxPredictions": 2147483647,
            "maxPredictions": 10000,
            "recall": recall_micro,
            "precision": precision_micro,
            "falsePositiveRate": false_positive_rate,
            "f1Score": f1_micro,
            "f1ScoreMicro": f1_micro,
            "f1ScoreMacro": f1_macro,
            "truePositiveCount": tp_count,
            "falsePositiveCount": fp_count,
            "falseNegativeCount": fn_count,
            "trueNegativeCount": tn_count,
            # 'At1' metrics are the same for this logic
            "recallAt1": recall_micro,
            "precisionAt1": precision_micro,
            "falsePositiveRateAt1": false_positive_rate,
            "f1ScoreAt1": f1_micro,
            # "confusionMatrix": confusion_matrix_dict
        })

    # --- Calculate Overall Confusion Matrix ---
    print("Calculating overall confusion matrix...")
    overall_cm = confusion_matrix(y_true, y_pred, labels=range(len(class_labels)))
    #cm_rows_list = overall_cm.tolist()
    #cm_rows = [{"row": row} for row in cm_rows_list]

    confusion_matrix_output = {
        "annotationSpecs": annotation_specs_list,
        "rows": overall_cm.tolist(),
    }

    # --- Construct Final Evaluation Metrics Dictionary ---
    evaluation_metrics = {
        "auPrc": au_prc,
        "auRoc": au_roc,
        "logLoss": logloss,
        "confidenceMetrics": confidence_metrics,
        # I do not know which format should be applied here. 
        # "confusionMatrix": confusion_matrix_output,
    }

    output_dir = os.path.dirname(args.output_path)
    os.makedirs(output_dir, exist_ok=True)

    print(f"Saving evaluation metrics to {args.output_path}")
    with open(args.output_path, 'w') as f:
        json.dump(evaluation_metrics, f, indent=4)

    print("Evaluation metrics saved successfully.")

    # --- Upload metrics to Vertex AI Model Registry ---
    print("Uploading evaluation metrics to Vertex AI Model Registry...")
    
    # Define the schema URI for classification metrics
    METRICS_SCHEMA_URI = "gs://google-cloud-aiplatform/schema/modelevaluation/classification_metrics_1.0.0.yaml"
    
    # Create the ModelEvaluation object
    model_evaluation = gapic.ModelEvaluation(
        display_name=args.evaluation_display_name,
        metrics_schema_uri=METRICS_SCHEMA_URI,
        metrics=evaluation_metrics,
    )
    
    # Initialize the ModelServiceClient
    API_ENDPOINT = f"{args.location}-aiplatform.googleapis.com"
    client_options = {"api_endpoint": API_ENDPOINT}
    client = gapic.ModelServiceClient(client_options=client_options)
    
    # Create the import request
    request = gapic.ImportModelEvaluationRequest(
        parent=model_resource_name,
        model_evaluation=model_evaluation,
    )
    
    # Import the evaluation
    response = client.import_model_evaluation(request=request)
    print(f"Successfully imported model evaluation: {response.name}")

if __name__ == "__main__":
    main()
