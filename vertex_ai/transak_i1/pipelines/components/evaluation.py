from kfp import dsl
from kfp.dsl import (
    Artifact,
    Input,
    Output,
)
from google_cloud_pipeline_components.types.artifact_types import (
    VertexModel,
    ClassificationMetrics,
)


@dsl.component(
    base_image="python:3.10",
    packages_to_install=[
        "google-cloud-aiplatform==1.100.0",
        "google-cloud-pipeline-components==2.20.1",
        "kfp==2.7.0",
        "numpy==1.26.4",
        "pandas==2.2.2",
        "scikit-learn==1.5.0",
    ],
)
def model_evaluation_op(
    project: str,
    location: str,
    predictions: Input[Artifact],
    class_labels: Input[Artifact],
    vertex_model: Input[VertexModel],
    evaluation_metrics: Output[ClassificationMetrics],
    target_column: str = 'i1_true_label_id',
    evaluation_display_name: str = "production_evaluation",
):
    """
    Perform model evaluation, add metadata, and upload metrics.

    This lightweight component reads artifact data from local paths, calculates
    a comprehensive set of classification metrics, adds the max F1 macro score
    to the artifact's metadata, and uploads the metrics as a ModelEvaluation
    to the Vertex AI Model Registry.
    """
    import json
    import os
    from pathlib import Path
    import numpy as np
    import pandas as pd
    from google.cloud import aiplatform
    from google.cloud.aiplatform import gapic
    from sklearn.metrics import (
        average_precision_score,
        confusion_matrix,
        f1_score,
        log_loss,
        roc_auc_score,
    )

    # Initialize clients
    aiplatform.init(project=project, location=location)

    def softmax(x):
        """Compute softmax values for each sets of scores in x."""
        e_x = np.exp(x - np.max(x, axis=1, keepdims=True))
        return e_x / e_x.sum(axis=1, keepdims=True)

    # 1. Read inputs from local paths and artifact metadata
    print("Reading inputs...")
    model_resource_name = vertex_model.metadata["resourceName"]
    print(f"Retrieved model resource name from artifact metadata: {model_resource_name}")

    # Find the prediction file and read it directly into Pandas
    prediction_dir = Path(predictions.path)
    jsonl_file = next(
        (f for f in prediction_dir.iterdir() if "prediction.results-" in f.name),
        None,
    )
    if not jsonl_file:
        raise FileNotFoundError(f"No prediction results file found in {predictions.path}")

    print(f"Reading predictions from {jsonl_file} into DataFrame.")
    predictions_df = pd.read_json(jsonl_file, lines=True)

    # Read class labels
    with open(class_labels.path, 'r') as f:
        class_labels = json.load(f)
    print("Inputs read successfully.")

    # Extract numpy arrays from the DataFrame
    y_true = predictions_df['instance'].apply(lambda x: x[target_column]).to_numpy()
    y_pred_logits = np.stack(predictions_df['prediction'].to_numpy())
    y_pred = np.argmax(softmax(y_pred_logits), axis=1)
    print(f"Found {len(y_true)} records for evaluation.")

    # 2. Calculate metrics
    print("Calculating metrics...")
    y_pred_proba = softmax(y_pred_logits)
    au_prc = average_precision_score(y_true, y_pred_proba, average='micro')
    au_roc = roc_auc_score(y_true, y_pred_proba, average='micro', multi_class='ovr')
    logloss = log_loss(y_true, y_pred_proba)

    confidence_metrics = []
    all_probabilities = y_pred_proba.ravel()
    confidence_thresholds = np.sort(np.unique(np.concatenate(([0.0, 1.0], all_probabilities))))[::-1]
    print(f"Generating metrics for {len(confidence_thresholds)} unique thresholds...")

    num_classes = len(class_labels)
    total_instances = len(y_true)
    total_possible_negatives = total_instances * (num_classes - 1)
    annotation_specs_list = [
        {"id": str(label_id), "displayName": label_name}
        for label_id, label_name in sorted(class_labels.items(), key=lambda item: int(item[0]))
    ]

    for threshold in confidence_thresholds:
        y_pred_max_proba = np.max(y_pred_proba, axis=1)
        valid_indices = y_pred_max_proba >= threshold
        y_true_filtered = y_true[valid_indices]
        y_pred_filtered = y_pred[valid_indices]

        if len(y_true_filtered) == 0:
            tp_count, fp_count, fn_count = 0, 0, total_instances
            tn_count = total_possible_negatives
            precision_micro, recall_micro, f1_micro, f1_macro, false_positive_rate = 1.0, 0.0, 0.0, 0.0, 0.0
        else:
            cm_filtered = confusion_matrix(y_true_filtered, y_pred_filtered, labels=range(num_classes))
            tp_count = int(np.diag(cm_filtered).sum())
            fp_count = int(cm_filtered.sum() - tp_count)
            fn_count = total_instances - tp_count
            tn_count = total_possible_negatives - fp_count
            precision_micro = tp_count / (tp_count + fp_count) if (tp_count + fp_count) > 0 else 1.0
            recall_micro = tp_count / (tp_count + fn_count) if (tp_count + fn_count) > 0 else 0.0
            false_positive_rate = fp_count / (fp_count + tn_count) if (fp_count + tn_count) > 0 else 0.0
            f1_micro = 2 * (precision_micro * recall_micro) / (precision_micro + recall_micro) if (precision_micro + recall_micro) > 0 else 0.0
            f1_macro = f1_score(y_true_filtered, y_pred_filtered, average='macro', labels=range(num_classes), zero_division=0)

        confidence_metrics.append({
            "confidenceThreshold": float(threshold), "maxPredictions": 10000,
            "recall": recall_micro, "precision": precision_micro,
            "falsePositiveRate": false_positive_rate, "f1Score": f1_micro,
            "f1ScoreMicro": f1_micro, "f1ScoreMacro": f1_macro,
            "truePositiveCount": tp_count, "falsePositiveCount": fp_count,
            "falseNegativeCount": fn_count, "trueNegativeCount": tn_count,
            "recallAt1": recall_micro, "precisionAt1": precision_micro,
            "falsePositiveRateAt1": false_positive_rate, "f1ScoreAt1": f1_micro,
        })

    # 3. Finalize metrics and add metadata
    final_evaluation_metrics = {
        "auPrc": au_prc, "auRoc": au_roc, "logLoss": logloss,
        "confidenceMetrics": confidence_metrics,
    }

    # Find the max f1_macro from the calculated confidence metrics
    max_f1_macro = 0.0
    if confidence_metrics:
        max_f1_macro = max(m.get('f1ScoreMacro', 0.0) for m in confidence_metrics)

    print(f"Saving evaluation metrics to {evaluation_metrics.path}")
    with open(evaluation_metrics.path, 'w') as f:
        json.dump(final_evaluation_metrics, f, indent=4)

    print(f"Adding metadata to artifact: max_f1_macro = {max_f1_macro}")
    evaluation_metrics.metadata["max_f1_macro"] = max_f1_macro

    # 4. Upload metrics to Vertex AI Model Registry
    print("Uploading evaluation metrics to Vertex AI Model Registry...")
    METRICS_SCHEMA_URI = "gs://google-cloud-aiplatform/schema/modelevaluation/classification_metrics_1.0.0.yaml"
    model_evaluation = gapic.ModelEvaluation(
        display_name=evaluation_display_name,
        metrics_schema_uri=METRICS_SCHEMA_URI,
        metrics=final_evaluation_metrics,
    )
    API_ENDPOINT = f"{location}-aiplatform.googleapis.com"
    client = gapic.ModelServiceClient(client_options={"api_endpoint": API_ENDPOINT})
    request = gapic.ImportModelEvaluationRequest(
        parent=model_resource_name,
        model_evaluation=model_evaluation,
    )
    response = client.import_model_evaluation(request=request)
    print(f"Successfully imported model evaluation: {response.name}")
