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
  , NULL i0_true_label
  , NULL i0_pred_label
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202508`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202507`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202506`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202505`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202504`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202404`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202403`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202402`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202401`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202312`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202311`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202310`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202309`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202308`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202307`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202306`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202305`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202304`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202303`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202302`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202301`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202212`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202211`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202210`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202209`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202208`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202207`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202206`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202205`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202204`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202203`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202202`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202201`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202112`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202111`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202110`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202109`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202108`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202107`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202106`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202105`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202104`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202103`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202102`
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
  , i0_new_label
  , i1_true_label
  , status
  , comment
FROM `af-finanzen.monatsabschluss.revolut_abrechnung_202101`
WHERE month IS NOT NULL
