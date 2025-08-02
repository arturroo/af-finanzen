import os
import argparse
import pandas as pd
import numpy as np
from google.cloud import bigquery
from google.cloud import aiplatform

def _parse_args():
    """Parses command-line arguments for the data prep task."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--bq-project-id', required=True, type=str, help='BigQuery project ID.')
    parser.add_argument('--bq-dataset-id', required=True, type=str, help='BigQuery dataset ID.')
    parser.add_argument('--bq-table-id', required=True, type=str, help='BigQuery table ID.')
    parser.add_argument('--train-data-path', required=True, type=str, help='GCS output path for the training CSV file.')
    parser.add_argument('--val-data-path', required=True, type=str, help='GCS output path for the validation CSV file.')
    parser.add_argument('--test-data-path', required=True, type=str, help='GCS output path for the test CSV file.')
    parser.add_argument('--project-id', required=True, type=str, help='Google Cloud project ID.')
    parser.add_argument('--region', required=True, type=str, help='GCP Region for Vertex AI resources.')
    parser.add_argument('--target-column', required=True, type=str, help='Name of the target column for classification.')
    parser.add_argument('--train-stats-path', required=True, type=str, help='GCS output path for the training stats JSON file.')
    parser.add_argument('--val-stats-path', required=True, type=str, help='GCS output path for the validation stats JSON file.')
    parser.add_argument('--test-stats-path', required=True, type=str, help='GCS output path for the test stats JSON file.')
    return parser.parse_args()

def _calculate_dataframe_statistics(df: pd.DataFrame, target_column: str) -> dict:
    """Calculates various statistics for a given DataFrame."""
    stats = {}

    # 1. Number of Samples/Rows
    stats['num_rows'] = len(df)

    # 2. Number of Features/Columns (excluding target)
    stats['num_columns'] = len(df.columns) - 1 # Exclude target column

    # 3. Class Distribution (for classification)
    if target_column in df.columns:
        class_counts = df[target_column].value_counts()
        stats['class_distribution'] = class_counts.to_dict()
        stats['class_distribution_percentage'] = (class_counts / len(df) * 100).to_dict()
    else:
        stats['class_distribution'] = 'Target column not found'

    # Identify numerical and categorical columns
    numerical_cols = df.select_dtypes(include=np.number).columns.tolist()
    if target_column in numerical_cols:
        numerical_cols.remove(target_column) # Exclude target if it's numerical

    categorical_cols = df.select_dtypes(include='object').columns.tolist()

    # 4. Summary Statistics for Numerical Features
    numerical_stats = {}
    for col in numerical_cols:
        col_stats = {
            'mean': df[col].mean(),
            'median': df[col].median(),
            'std': df[col].std(),
            'min': df[col].min(),
            'max': df[col].max(),
            '25th_percentile': df[col].quantile(0.25),
            '50th_percentile': df[col].quantile(0.50),
            '75th_percentile': df[col].quantile(0.75),
        }
        numerical_stats[col] = {k: (None if pd.isna(v) else v) for k, v in col_stats.items()} # Replace NaN with None
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

def main():
    """Main entrypoint for the data preparation task."""
    args = _parse_args()

    # Construct the Fully Qualified Table Name (FQTN)
    fqtn = f"{args.bq_project_id}.{args.bq_dataset_id}.{args.bq_table_id}"

    # print("Initializing AI Platform with autologging...")
    # aiplatform.init(project=args.project_id, 
    #                 location=args.region, 
    #                 # experiment=args.experiment_name, 
    #                 # experiment_tensorboard=args.tensorboard_resource_name
    #                 )
    # aiplatform.autolog()
    #with aiplatform.start_run(
    #    #run=args.run_name, 
    #    resume=True
    #    ) as experiment_run:
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
    """
    bq_client = bigquery.Client(project=args.project_id)
    print(f"Running query: {query}")
    df = bq_client.query(query).to_dataframe()
    train_df = df[df.split_set == 'train'].drop(columns=['split_set'])
    val_df = df[df.split_set == 'validation'].drop(columns=['split_set'])
    test_df = df[df.split_set == 'test'].drop(columns=['split_set'])
    os.makedirs(os.path.dirname(args.train_data_path), exist_ok=True)
    os.makedirs(os.path.dirname(args.val_data_path), exist_ok=True)
    os.makedirs(os.path.dirname(args.test_data_path), exist_ok=True)
    print(f"Saving splits data to {args.train_data_path}")
    train_df.to_csv(args.train_data_path, index=False)
    val_df.to_csv(args.val_data_path, index=False)
    test_df.to_csv(args.test_data_path, index=False)

    # Calculate and print statistics
    train_stats = _calculate_dataframe_statistics(train_df, args.target_column)
    val_stats = _calculate_dataframe_statistics(val_df, args.target_column)
    test_stats = _calculate_dataframe_statistics(test_df, args.target_column)

    print("Train Data Statistics:", train_stats)
    print("Validation Data Statistics:", val_stats)
    print("Test Data Statistics:", test_stats)

    # Save statistics to JSON files
    with open(args.train_stats_path, 'w') as f:
        json.dump(train_stats, f)
    with open(args.val_stats_path, 'w') as f:
        json.dump(val_stats, f)
    with open(args.test_stats_path, 'w') as f:
        json.dump(test_stats, f)
    

if __name__ == '__main__':
    main()
