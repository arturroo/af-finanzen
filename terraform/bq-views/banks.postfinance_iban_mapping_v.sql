SELECT
  iban,
  name,
  mutation_ts,
  DATETIME(mutation_ts, "Europe/Zurich") AS mutation_dt,
  comments
FROM `${project_id}.banks.postfinance_iban_mapping`
