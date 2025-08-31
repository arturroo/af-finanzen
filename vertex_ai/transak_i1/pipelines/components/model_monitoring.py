from kfp.v2.dsl import component, Input, Output, Dataset
from google_cloud_pipeline_components.types.artifact_types import VertexModel

@component(
    base_image='python:3.9',
    packages_to_install=["pandas", "numpy", "google-cloud-aiplatform", "fsspec", "gcsfs"],
)
def model_monitoring_op(
    model: Input[VertexModel],
    prediction_data: Input[Dataset],
    drift_detected: Output[bool],
    drift_threshold: float = 0.1, # Example threshold
):
    """
    A component to compare training and prediction data statistics
    and detect data drift.
    """
    import pandas as pd
    import numpy as np
    from google.cloud import aiplatform
    import re

    # Get the training data URI from the model description
    model_resource_name = model.metadata["resourceName"]
    vertex_model = aiplatform.Model(model_name=model_resource_name)
    description = vertex_model.description
    
    match = re.search(r"\[training_data_uri:(.*)\]", description)
    if not match:
        raise ValueError("Could not find training_data_uri in model description.")
    
    training_data_uri = match.group(1)

    def _calculate_dataframe_statistics(df: pd.DataFrame) -> dict:
        # This is a simplified version of the function in data_splits_op
        stats = {}
        numerical_cols = df.select_dtypes(include=np.number).columns.tolist()
        categorical_cols = df.select_dtypes(include='object').columns.tolist()

        numerical_stats = {}
        for col in numerical_cols:
            numerical_stats[col] = {'mean': float(df[col].mean()), 'std': float(df[col].std())}
        stats['numerical_features_stats'] = numerical_stats

        categorical_stats = {}
        for col in categorical_cols:
            categorical_stats[col] = df[col].value_counts(normalize=True).to_dict()
        stats['categorical_features_stats'] = categorical_stats
        
        return stats

    train_df = pd.read_csv(training_data_uri)
    predict_df = pd.read_csv(prediction_data.path)

    train_stats = _calculate_dataframe_statistics(train_df)
    predict_stats = _calculate_dataframe_statistics(predict_df)

    is_drift_detected = False
    
    # Compare numerical features
    for feature, stats in train_stats['numerical_features_stats'].items():
        if feature in predict_stats['numerical_features_stats']:
            mean_diff = abs(stats['mean'] - predict_stats['numerical_features_stats'][feature]['mean'])
            if stats['mean'] != 0 and mean_diff > drift_threshold * abs(stats['mean']):
                print(f"Drift detected in numerical feature '{feature}': mean difference is {mean_diff}")
                is_drift_detected = True

    # Compare categorical features
    for feature, dist in train_stats['categorical_features_stats'].items():
        if feature in predict_stats['categorical_features_stats']:
            predict_dist = predict_stats['categorical_features_stats'][feature]
            all_keys = set(dist.keys()) | set(predict_dist.keys())
            total_diff = 0
            for key in all_keys:
                total_diff += abs(dist.get(key, 0) - predict_dist.get(key, 0))
            
            if total_diff / 2 > drift_threshold:
                print(f"Drift detected in categorical feature '{feature}': distribution difference is {total_diff / 2}")
                is_drift_detected = True

    drift_detected.value = is_drift_detected
