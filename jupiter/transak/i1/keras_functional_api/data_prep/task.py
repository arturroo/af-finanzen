import argparse
import pandas as pd
from google.cloud import bigquery
import os

def _parse_args():
    """Parses command-line arguments for the data prep task."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--project-id', required=True, type=str, help='Google Cloud project ID.')
    parser.add_argument('--train-data-path', required=True, type=str, help='GCS output path for the training CSV file.')
    parser.add_argument('--val-data-path', required=True, type=str, help='GCS output path for the validation CSV file.')
    parser.add_argument('--test-data-path', required=True, type=str, help='GCS output path for the test CSV file.')
    return parser.parse_args()

def main():
    """Main entrypoint for the data preparation task."""
    args = _parse_args()

    query = """
    WITH RAW_DATA AS (
      SELECT
          tid
        , type
        , EXTRACT(YEAR  FROM started) AS started_year
        , EXTRACT(MONTH FROM started) AS started_month
        , EXTRACT(DAY   FROM started) AS started_day
        , MOD(EXTRACT(DAYOFWEEK FROM started) + 5, 7) AS started_weekday
        , EXTRACT(YEAR  FROM first_started) AS first_started_year
        , EXTRACT(MONTH FROM first_started) AS first_started_month
        , EXTRACT(DAY   FROM first_started) AS first_started_day
        , MOD(EXTRACT(DAYOFWEEK FROM first_started) + 5, 7) AS first_started_weekday
        , LOWER(description) AS description
        , amount
        , currency
        , CASE
            WHEN i1_true_label = 'PK Prezenty' THEN 'PK Rest'
            WHEN i1_true_label = 'PK Auto' THEN 'PK Rest'
            WHEN i1_true_label = 'Apt' THEN 'PK Kasia'
            ELSE i1_true_label
          END AS i1_true_label
      FROM `af-finanzen.monatsabschluss.revolut_abrechnung`
      WHERE
        type NOT IN ("FEE", "ATM")
      ORDER BY started
    ),
    LABEL_INT AS (
      SELECT
        *
        , DENSE_RANK() OVER(ORDER BY i1_true_label) - 1 AS i1_true_label_id
      FROM RAW_DATA
    ),
    SPLIT_SET AS (
      SELECT
          tid
        , i1_true_label
        , CASE
            WHEN ABS(MOD(tid, 10)) <= 7 THEN 'train'
            WHEN ABS(MOD(tid, 10)) = 8 THEN 'validation'
            WHEN ABS(MOD(tid, 10)) = 9 THEN 'test'
            ELSE "unknown"
          END AS split_set
      FROM RAW_DATA
      GROUP BY i1_true_label, tid
    )
    SELECT
      LABEL_INT.* EXCEPT(tid)
      , SPLIT_SET.split_set
    FROM LABEL_INT
    JOIN SPLIT_SET
    ON LABEL_INT.tid = SPLIT_SET.tid
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
