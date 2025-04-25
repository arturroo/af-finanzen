SELECT 
    CAST(tid AS INT64) AS tid
  , type
  , product
  , started
  , completed
  , description
  , amount
  , fee
  , currency
  , state
  , balance
  , account
  , month
  , first_started
  , true_label i0_true_label
  , pred_label i0_pred_label
  , new_label i0_new_label
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202503`
WHERE month IS NOT NULL
UNION ALL
SELECT 
    CAST(tid AS INT64) AS tid
  , type
  , product
  , started
  , completed
  , description
  , amount
  , fee
  , currency
  , state
  , balance
  , account
  , month
  , first_started
  , true_label i0_true_label
  , pred_label i0_pred_label
  , new_label i0_new_label
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202502`
WHERE month IS NOT NULL
UNION ALL
SELECT 
    CAST(tid AS INT64) AS tid
  , type
  , product
  , started
  , completed
  , description
  , amount
  , fee
  , currency
  , state
  , balance
  , account
  , month
  , first_started
  , true_label i0_true_label
  , pred_label i0_pred_label
  , new_label i0_new_label
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202501`
WHERE month IS NOT NULL
UNION ALL
SELECT 
    CAST(tid AS INT64) AS tid
  , type
  , product
  , started
  , completed
  , description
  , amount
  , fee
  , currency
  , state
  , balance
  , account
  , month
  , first_started
  , true_label i0_true_label
  , pred_label i0_pred_label
  , new_label i0_new_label
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202412`
WHERE month IS NOT NULL
UNION ALL
SELECT 
    CAST(tid AS INT64) AS tid
  , type
  , product
  , started
  , completed
  , description
  , amount
  , fee
  , currency
  , state
  , balance
  , account
  , month
  , first_started
  , true_label i0_true_label
  , pred_label i0_pred_label
  , new_label i0_new_label
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202411`
WHERE month IS NOT NULL
UNION ALL
SELECT 
    CAST(tid AS INT64) AS tid
  , type
  , product
  , started
  , completed
  , description
  , amount
  , fee
  , currency
  , state
  , balance
  , account
  , month
  , first_started
  , true_label i0_true_label
  , pred_label i0_pred_label
  , new_label i0_new_label
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202410`
WHERE month IS NOT NULL
UNION ALL
SELECT 
    CAST(tid AS INT64) AS tid
  , type
  , product
  , started
  , completed
  , description
  , amount
  , fee
  , currency
  , state
  , balance
  , account
  , month
  , first_started
  , true_label i0_true_label
  , pred_label i0_pred_label
  , new_label i0_new_label
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202409`
WHERE month IS NOT NULL
UNION ALL
SELECT 
    CAST(tid AS INT64) AS tid
  , type
  , product
  , started
  , completed
  , description
  , amount
  , fee
  , currency
  , state
  , balance
  , account
  , month
  , first_started
  , true_label i0_true_label
  , pred_label i0_pred_label
  , new_label i0_new_label
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202408`
WHERE month IS NOT NULL
UNION ALL
SELECT 
    CAST(tid AS INT64) AS tid
  , type
  , product
  , started
  , completed
  , description
  , amount
  , fee
  , currency
  , state
  , balance
  , account
  , month
  , first_started
  , true_label i0_true_label
  , pred_label i0_pred_label
  , new_label i0_new_label
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202407`
WHERE month IS NOT NULL
UNION ALL
SELECT 
    CAST(tid AS INT64) AS tid
  , type
  , product
  , started
  , completed
  , description
  , amount
  , fee
  , currency
  , state
  , balance
  , account
  , month
  , first_started
  , true_label i0_true_label
  , pred_label i0_pred_label
  , new_label i0_new_label
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202406`
WHERE month IS NOT NULL
UNION ALL
SELECT 
    CAST(tid AS INT64) AS tid
  , type
  , product
  , started
  , completed
  , description
  , amount
  , fee
  , currency
  , state
  , balance
  , account
  , month
  , first_started
  , true_label i0_true_label
  , pred_label i0_pred_label
  , new_label i0_new_label
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202405`
WHERE month IS NOT NULL
UNION ALL
SELECT 
    CAST(tid AS INT64) AS tid
  , type
  , product
  , started
  , completed
  , description
  , amount
  , fee
  , currency
  , state
  , balance
  , account
  , month
  , first_started
  , true_label i0_true_label
  , pred_label i0_pred_label
  , new_label i0_new_label
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202404`
WHERE month IS NOT NULL
