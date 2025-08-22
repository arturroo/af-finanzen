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
from google.cloud import storage

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

    args = parser.parse_args()

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

    for threshold in confidence_thresholds:
        y_pred_thresholded = np.where(np.max(y_pred_proba, axis=1) >= threshold, y_pred, -1)
        valid_indices = y_pred_thresholded != -1
        
        if not np.any(valid_indices):
            confidence_metrics.append({
                "confidenceThreshold": threshold, "recall": 0.0, "precision": 0.0,
                "falsePositiveRate": 0.0, "f1Score": 0.0, "truePositiveCount": 0,
                "falsePositiveCount": 0, "falseNegativeCount": 0, "trueNegativeCount": len(y_true)
            })
            continue

        y_true_filtered = y_true[valid_indices]
        y_pred_filtered = y_pred_thresholded[valid_indices]
        num_classes = len(sorted_class_labels)
        cm_filtered = confusion_matrix(y_true_filtered, y_pred_filtered, labels=range(num_classes))

        TP = np.sum(np.diag(cm_filtered))
        FP = np.sum(cm_filtered) - TP
        FN = cm_filtered.sum() - TP # This is TP + FN + FP - TP = FN + FP
        # Correcting FP and FN calculation
        FP = cm_filtered.sum(axis=0).sum() - TP
        FN = cm_filtered.sum(axis=1).sum() - TP
        TN = len(y_true) * num_classes - (TP + FP + FN)


        precision = TP / (TP + FP) if (TP + FP) > 0 else 0.0
        recall = TP / (TP + FN) if (TP + FN) > 0 else 0.0
        f1_score = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        false_positive_rate = FP / (FP + TN) if (FP + TN) > 0 else 0.0

        confidence_metrics.append({
            "confidenceThreshold": threshold, "recall": recall, "precision": precision,
            "falsePositiveRate": false_positive_rate, "f1Score": f1_score,
            "truePositiveCount": int(TP), "falsePositiveCount": int(FP),
            "falseNegativeCount": int(FN), "trueNegativeCount": int(TN)
        })

    # --- Calculate Overall Confusion Matrix ---
    print("Calculating overall confusion matrix...")
    overall_cm = confusion_matrix(y_true, y_pred, labels=range(len(sorted_class_labels)))
    cm_rows = [{"row": row} for row in overall_cm.tolist()]

    confusion_matrix_output = {
        "annotationSpecs": [{"displayName": label} for label in sorted_class_labels],
        "rows": cm_rows,
    }

    # --- Construct Final Evaluation Metrics Dictionary ---
    evaluation_metrics = {
        "auPrc": au_prc, "auRoc": au_roc, "logLoss": logloss,
        "confidenceMetrics": confidence_metrics, "confusionMatrix": confusion_matrix_output,
    }

    output_dir = os.path.dirname(args.output_path)
    os.makedirs(output_dir, exist_ok=True)

    print(f"Saving evaluation metrics to {args.output_path}")
    with open(args.output_path, 'w') as f:
        json.dump(evaluation_metrics, f, indent=4)

    print("Evaluation metrics saved successfully.")

if __name__ == "__main__":
    main()
