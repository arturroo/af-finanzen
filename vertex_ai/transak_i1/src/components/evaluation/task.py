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
    sorted_class_labels = _read_gcs_json(args.class_labels_uri)

    # --- Calculate Core Metrics ---
    print("Calculating core metrics...")
    au_prc = average_precision_score(y_true, y_pred_proba, average='micro')
    au_roc = roc_auc_score(y_true, y_pred_proba, average='micro', multi_class='ovr')
    logloss = log_loss(y_true, y_pred_proba)

    # --- Calculate Confidence Metrics ---
    print("Calculating confidence metrics...")
    confidence_metrics = []
    confidence_thresholds = [i / 100.0 for i in range(0, 100, 5)] + [0.96, 0.97, 0.98, 0.99]
    num_classes = len(sorted_class_labels)

    for threshold in confidence_thresholds:
        y_pred_thresholded = np.where(np.max(y_pred_proba, axis=1) >= threshold, y_pred, -1)
        valid_indices = y_pred_thresholded != -1

        if not np.any(valid_indices):
            confidence_metrics.append({
                "confidenceThreshold": threshold,
                "maxPredictions": 2147483647,
                "recall": 0.0, "precision": 0.0, "falsePositiveRate": 0.0,
                "f1Score": 0.0, "f1ScoreMicro": 0.0, "f1ScoreMacro": 0.0,
                "recallAt1": 0.0, "precisionAt1": 0.0, "falsePositiveRateAt1": 0.0, "f1ScoreAt1": 0.0,
                "truePositiveCount": 0, "falsePositiveCount": 0,
                "falseNegativeCount": len(y_true), "trueNegativeCount": len(y_true) * (num_classes - 1),
                "confusionMatrix": {
                    "annotationSpecs": [{"id": str(i), "displayName": label} for i, label in enumerate(sorted_class_labels)],
                    "rows": [{"row": [0] * num_classes} for _ in range(num_classes)]
                }
            })
            continue

        y_true_filtered = y_true[valid_indices]
        y_pred_filtered = y_pred_thresholded[valid_indices]

        # --- Metric Calculations ---
        precision_micro, recall_micro, f1_micro, _ = precision_recall_fscore_support(
            y_true_filtered, y_pred_filtered, average='micro', labels=range(num_classes), zero_division=0
        )
        _, _, f1_macro, _ = precision_recall_fscore_support(
            y_true_filtered, y_pred_filtered, average='macro', labels=range(num_classes), zero_division=0
        )

        cm_filtered = confusion_matrix(y_true_filtered, y_pred_filtered, labels=range(num_classes))

        # --- Counts ---
        tp_count = int(np.diag(cm_filtered).sum())
        fp_count = int(cm_filtered.sum() - tp_count)
        fn_count = len(y_true) - tp_count

        tn_per_class = []
        fp_per_class = []
        for i in range(num_classes):
            tp = cm_filtered[i, i]
            fp = cm_filtered[:, i].sum() - tp
            fn = cm_filtered[i, :].sum() - tp
            tn = cm_filtered.sum() - (tp + fp + fn)
            fp_per_class.append(fp)
            tn_per_class.append(tn)

        tn_total = sum(tn_per_class)
        fp_total = sum(fp_per_class)
        false_positive_rate = fp_total / (fp_total + tn_total) if (fp_total + tn_total) > 0 else 0.0

        # Since we take the argmax, we are always dealing with 1 prediction, so At1 metrics are the same
        confidence_metrics.append({
            "confidenceThreshold": threshold,
            "maxPredictions": 2147483647,
            "recall": recall_micro,
            "precision": precision_micro,
            "falsePositiveRate": false_positive_rate,
            "f1Score": f1_micro,
            "f1ScoreMicro": f1_micro,
            "f1ScoreMacro": f1_macro,
            "recallAt1": recall_micro,
            "precisionAt1": precision_micro,
            "falsePositiveRateAt1": false_positive_rate,
            "f1ScoreAt1": f1_micro,
            "truePositiveCount": tp_count,
            "falsePositiveCount": fp_count,
            "falseNegativeCount": fn_count,
            "trueNegativeCount": int(tn_total)
            # "confusionMatrix": {
            #     "annotationSpecs": [{"id": str(i), "displayName": label} for i, label in enumerate(sorted_class_labels)],
            #     "rows": [{"row": row} for row in cm_filtered.tolist()]
            # }
        })

    # --- Calculate Overall Confusion Matrix ---
    print("Calculating overall confusion matrix...")
    overall_cm = confusion_matrix(y_true, y_pred, labels=range(len(sorted_class_labels)))
    cm_rows_list = overall_cm.tolist()
    cm_rows = [{"row": row} for row in cm_rows_list]

    confusion_matrix_output = {
        "annotationSpecs": [{ "id": str(i), "displayName": label} for i, label in enumerate(sorted_class_labels)],
        "rows": cm_rows,
    }

    # --- Construct Final Evaluation Metrics Dictionary ---
    evaluation_metrics = {
        "auPrc": au_prc,
        "auRoc": au_roc,
        "logLoss": logloss,
        "confidenceMetrics": confidence_metrics,
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
