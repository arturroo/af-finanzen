from kfp.dsl import (
    Artifact,
    Dataset,
    Input,
    Output,
    component,
)


@component(
    base_image="europe-west6-docker.pkg.dev/af-finanzen/af-finanzen-mlops/transak-i1-train-predict:latest",
    packages_to_install=["pandas", "numpy", "gcsfs"],
)
def create_monitoring_baseline_op(
    predictions_artifact: Input[Artifact],
    monitoring_baseline: Output[Dataset],
):
    """
    Creates a monitoring baseline dataset from batch prediction results.
    The batch prediction output is expected to contain both the original instance and the prediction logits.

    Args:
        predictions_artifact (Input[Artifact]): The artifact from the batch prediction job.
                                                The component expects the prediction files to be
                                                locally available at predictions_artifact.path.
        class_labels (Input[Artifact]): The artifact containing the mapping from class IDs to class labels.
        monitoring_baseline (Output[Dataset]): The output dataset containing the baseline data (features + prediction).
    """
    import json
    import logging
    import numpy as np
    import pandas as pd
    from pathlib import Path

    logging.basicConfig(level=logging.INFO)

    # --- 1. Load label mapping ---
    with open(class_labels.path, "r") as f:
        label_mapping_str_keys = json.load(f)
    label_mapping = {int(k): v for k, v in label_mapping_str_keys.items()}
    logging.info(f"Loaded label mapping: {label_mapping}")

    # --- 2. Read predictions from local path ---
    prediction_dir = Path(predictions_artifact.path)
    logging.info(f"Searching for prediction files in local directory: {prediction_dir}")

    jsonl_files = list(prediction_dir.glob("prediction.results-*.jsonl"))
    if not jsonl_files:
        raise FileNotFoundError(
            f"No prediction results file found in {predictions_artifact.path}"
        )

    logging.info(f"Found local prediction files: {jsonl_files}")

    df_list = [pd.read_json(f, lines=True) for f in jsonl_files]
    predictions_df = pd.concat(df_list, ignore_index=True)
    logging.info(f"Successfully loaded {len(predictions_df)} predictions.")

    # --- 3. Process data ---
    instance_df = pd.json_normalize(predictions_df["instance"])
    logging.info(f"Extracted features. Columns: {instance_df.columns.tolist()}")

    logits = list(predictions_df["prediction"])
    predicted_class_ids = [np.argmax(logit_list) for logit_list in logits]
    
    predicted_labels = [label_mapping.get(id, "unknown") for id in predicted_class_ids]
    prediction_df = pd.DataFrame({"i1_pred_label": predicted_labels})
    logging.info("Calculated predicted class labels.")

    baseline_df = pd.concat([instance_df, prediction_df], axis=1)
    logging.info(
        f"Created baseline dataframe. Final columns: {baseline_df.columns.tolist()}"
    )

    # --- 4. Write baseline CSV to GCS ---
    # The URI of the output artifact is a GCS directory. We'll write our file into it.
    baseline_file_gcs_path = f"{monitoring_baseline.uri}/train_with_pred.csv"

    logging.info(f"Saving baseline data to GCS path: {baseline_file_gcs_path}")
    baseline_df.to_csv(baseline_file_gcs_path, index=False)

    # Update the artifact's URI to point directly to the created file
    monitoring_baseline.uri = baseline_file_gcs_path
