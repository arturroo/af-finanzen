import os
import argparse
import pandas as pd
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
    parser.add_argument('--tensorboard-resource-name', required=True, type=str)
    parser.add_argument('--project-id', required=True, type=str, help='Google Cloud project ID.')
    parser.add_argument('--region', required=True, type=str, help='GCP Region for Vertex AI resources.')
    parser.add_argument('--experiment-name', required=True, type=str, help='Name of the experiment for tracking.')
    parser.add_argument('--run-name', required=True, type=str, help='Name of the run for tracking.')
    return parser.parse_args()

def main():
    """Main entrypoint for the data preparation task."""
    args = _parse_args()

    # Construct the Fully Qualified Table Name (FQTN)
    fqtn = f"{args.bq_project_id}.{args.bq_dataset_id}.{args.bq_table_id}"

    print("Initializing AI Platform with autologging...")
    aiplatform.init(project=args.project_id, 
                    location=args.region, 
                    experiment=args.experiment_name, 
                    experiment_tensorboard=args.tensorboard_resource_name)
    aiplatform.autolog()
    with aiplatform.start_run(run=args.run_name, resume=True) as experiment_run:
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
        df = bq_client.query(query).to_dataframe()

        train_df = df[df.split_set == 'train'].drop(columns=['split_set'])
        val_df = df[df.split_set == 'validation'].drop(columns=['split_set'])
        test_df = df[df.split_set == 'test'].drop(columns=['split_set'])

        os.makedirs(os.path.dirname(args.train_data_path), exist_ok=True)
        os.makedirs(os.path.dirname(args.val_data_path), exist_ok=True)
        os.makedirs(os.path.dirname(args.test_data_path), exist_ok=True)

        train_df.to_csv(args.train_data_path, index=False)
        val_df.to_csv(args.val_data_path, index=False)
        test_df.to_csv(args.test_data_path, index=False)
    

if __name__ == '__main__':
    main()
