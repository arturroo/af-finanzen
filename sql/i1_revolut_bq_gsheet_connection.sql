SELECT
  CAST(R.tid AS STRING) AS tid,
  R.type,
  R.product,
  R.started,
  R.completed,
  R.description,
  R.amount,
  0 - R.fee AS fee,
  R.currency,
  R.state,
  R.balance,
  R.account,
  R.month,
  R.first_started,
  L.name AS i1_pred_label,
  ROUND(P.confidence_msp, 2) AS c_msp,
  ROUND(P.confidence_margin, 2) AS c_marigin,
  ROUND(P.confidence_entropy, 2) AS c_entropy
FROM `banks.revolut_v` AS R
LEFT JOIN `transak.i1_predictions` AS P
  ON R.tid = P.tid
LEFT JOIN `transak.i1_labels` AS L
  ON P.i1_pred_label_id = L.id
WHERE
  R.month = 202509
ORDER BY
  R.started;