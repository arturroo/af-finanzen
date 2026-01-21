SELECT
    description
  , amount
  , new_label
  , comment
  , PARSE_DATE("%Y%m", _TABLE_SUFFIX) AS month
FROM `af-finanzen.monatsabschluss.sankey_*`
