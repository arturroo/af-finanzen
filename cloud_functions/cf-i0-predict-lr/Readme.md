
# Transak - prediction serving Google Cloud Function

This Cloud Function provides a service to make predictions using logistic regression machine learning model.
It expects a JSON payload containing:
- training_dt: Date and time when the model was trained.
- vectorizer_fn: Filename of the saved vectorizer object.
- model_fn: Filename of the saved model object.
- test_text (optional): A single text string to be used for prediction.
- month (optional): The month for which to load test data from BigQuery.


## Example call:
Using gcloud functions call (CLI):
```Bash
gcloud functions call cf-predict-lr \
  --project=af-finanzen \
  --region=europe-west6 \
  --data='{"training_dt": "20241002234942", "vectorizer_fn": "vec_tfidf.pkl", "model_fn": "log_reg_tfidf_acc_0.44.joblib", "month": "2024-10"}'
```

## Maching predictions with raw data in BigQuery
```SQL
WITH RAW_DATA AS (
SELECT
    P.pred_label
  , R.*
  , P.* EXCEPT(description, pred_label)
FROM banks.revolut_v R
JOIN banks.predictions P
ON R.description = P.description
WHERE 
      R.month = "2024-10"
  AND P.month = "2024-10"
ORDER BY started desc
)
SELECT
  pred_label
  , SUM(amount) sum_of_expenses
FROM RAW_DATA
WHERE
  type != "TOPUP"
GROUP BY pred_label
ORDER BY sum_of_expenses
```


Author: Artur Fejklowicz