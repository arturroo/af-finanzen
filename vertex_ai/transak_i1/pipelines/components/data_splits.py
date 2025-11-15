from kfp.v2.dsl import component, Input, Output, Dataset, Artifact
from google_cloud_pipeline_components.types.artifact_types import BQTable

@component(
    base_image='python:3.9',
    packages_to_install=["pandas", "google-cloud-bigquery", "db-dtypes", "google-cloud-pipeline-components"],
)
def data_splits_op(
    golden_data_table: Input[BQTable],
    train_data: Output[Dataset],
    val_data: Output[Dataset],
    test_data: Output[Dataset],
    class_labels: Output[Artifact],
    project_id: str,
    region: str,
    target_column: str,
):
    """
    A component that reads golden data, splits it into train, validation, and test sets,
    and calculates statistics for each split, attaching them as metadata.
    """

    import json
    import pandas as pd
    import numpy as np
    from google.cloud import bigquery
    
    def _calculate_dataframe_statistics(df: pd.DataFrame, target_column: str) -> dict:
        """Calculates various statistics for a given DataFrame."""
        stats = {}

        # 1. Number of Samples/Rows
        stats['num_rows'] = len(df)

        # 2. Number of Features/Columns (excluding target)
        stats['num_columns'] = len(df.columns) - 1 # Exclude target column

        # 3. Class Distribution (for classification)
        # Use 'i1_true_label' for human-readable class names in statistics
        if 'i1_true_label' in df.columns:
            class_counts = df['i1_true_label'].value_counts()
            stats['class_distribution'] = class_counts.to_dict()
            stats['class_distribution_percentage'] = {k: round(v, 2) for k, v in (class_counts / len(df) * 100).to_dict().items()}
        else:
            # Fallback if 'i1_true_label' is not found, use the provided target_column
            if target_column in df.columns:
                class_counts = df[target_column].value_counts()
                stats['class_distribution'] = {str(k): v for k, v in class_counts.to_dict().items()} # Ensure keys are strings
                stats['class_distribution_percentage'] = {str(k): round(v, 2) for k, v in (class_counts / len(df) * 100).to_dict().items()} # Ensure keys are strings
            else:
                stats['class_distribution'] = 'Target column or true label column not found'

        # Identify numerical and categorical columns
        numerical_cols = df.select_dtypes(include=np.number).columns.tolist()
        if target_column in numerical_cols:
            numerical_cols.remove(target_column) # Exclude target if it's numerical

        categorical_cols = df.select_dtypes(include='object').columns.tolist()

        # 4. Summary Statistics for Numerical Features
        numerical_stats = {}
        for col in numerical_cols:
            col_stats = {
                'mean': float(df[col].mean()),
                'median': float(df[col].median()),
                'std': float(df[col].std()),
                'min': float(df[col].min()),
                'max': float(df[col].max()),
                '25th_percentile': float(df[col].quantile(0.25)),
                '50th_percentile': float(df[col].quantile(0.50)),
                '75th_percentile': float(df[col].quantile(0.75)),
            }
            # Round numerical stats to 2 decimal places
            numerical_stats[col] = {k: (round(v, 2) if isinstance(v, (float, int)) else v) for k, v in col_stats.items()} # Replace NaN with None
        stats['numerical_features_stats'] = numerical_stats

        # 5. Missing Value Counts/Percentages
        missing_values = df.isnull().sum()
        missing_percentage = (df.isnull().sum() / len(df)) * 100
        missing_stats = {}
        for col in df.columns:
            if missing_values[col] > 0:
                missing_stats[col] = {
                    'count': int(missing_values[col]),
                    'percentage': float(missing_percentage[col])
                }
        stats['missing_values'] = missing_stats

        # 6. Cardinality for Categorical Features
        categorical_cardinality = {}
        for col in categorical_cols:
            categorical_cardinality[col] = int(df[col].nunique())
        stats['categorical_features_cardinality'] = categorical_cardinality

        return stats


    # Construct the Fully Qualified Table Name (FQTN)
    fqtn = f"{golden_data_table.metadata['projectId']}.{golden_data_table.metadata['datasetId']}.{golden_data_table.metadata['tableId']}"

    query = f"""
    SELECT
      *
      , DENSE_RANK() OVER(ORDER BY i1_true_label) - 1 AS i1_true_label_id
      , CASE
          WHEN ABS(MOD(tid, 10)) <= 7 THEN 'train'
          WHEN ABS(MOD(tid, 10)) = 8 THEN 'validation'
          WHEN ABS(MOD(tid, 10)) = 9 THEN 'test'
          ELSE "unknown"
        END AS split_set
    FROM `{fqtn}`
    -- WHERE i1_true_label IS NOT NULL AND i1_true_label != ''
    """
    bq_client = bigquery.Client(project=project_id)
    print(f"Running query: {query}")
    df = bq_client.query(query).to_dataframe()

    train_df = df[df.split_set == 'train'].drop(columns=['split_set'])
    val_df = df[df.split_set == 'validation'].drop(columns=['split_set'])
    test_df = df[df.split_set == 'test'].drop(columns=['split_set'])

    # Save splits data to GCS paths
    print(f"Saving splits data to {train_data.path}")
    train_df.to_csv(train_data.path, index=False)
    val_df.to_csv(val_data.path, index=False)
    test_df.to_csv(test_data.path, index=False)

    # Create and save a mapping from i1_true_label_id to i1_true_label
    label_mapping_df = train_df[['i1_true_label_id', 'i1_true_label']].drop_duplicates().sort_values('i1_true_label_id')
    label_mapping = pd.Series(label_mapping_df.i1_true_label.values, index=label_mapping_df.i1_true_label_id).to_dict()

    # Convert integer keys to strings for JSON compatibility
    label_mapping_json = {str(k): v for k, v in label_mapping.items()}

    with open(class_labels.path, 'w') as f:
        json.dump(label_mapping_json, f)

    print("Class Label Mapping (id: label):", label_mapping_json)

    # Calculate and attach statistics as metadata
    train_data.metadata = _calculate_dataframe_statistics(train_df, target_column)
    val_data.metadata = _calculate_dataframe_statistics(val_df, target_column)
    test_data.metadata = _calculate_dataframe_statistics(test_df, target_column)

    print("Train Data Statistics:", train_data.metadata)
    print("Validation Data Statistics:", val_data.metadata)
    print("Test Data Statistics:", test_data.metadata)

