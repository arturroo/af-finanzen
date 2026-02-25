SELECT
  iban,
  name,
  cre_ts,
  DATE(cre_ts, "Europe/Zurich") AS valid_from,
  IFNULL(
    LEAD(DATE(cre_ts, "Europe/Zurich")) OVER (PARTITION BY iban ORDER BY cre_ts),
    DATE("9999-12-31")
  ) AS valid_to,
  DATETIME(cre_ts, "Europe/Zurich") AS cre_dt,
  comments
FROM `${project_id}.banks.postfinance_iban_mapping`
