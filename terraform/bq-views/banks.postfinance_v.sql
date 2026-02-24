/*
  Silver Layer View for PostFinance.
  - Standardizes column names to English.
  - Parses dates and calculates a stable Transaction ID (tid).
  - Splits 'avisierungstext' into a related IBAN and a Memo.
*/
WITH base AS (
  SELECT
    FARM_FINGERPRINT(
      CONCAT(
        datum,
        avisierungstext,
        CAST(COALESCE(gutschrift, 0) AS STRING),
        CAST(COALESCE(lastschrift, 0) AS STRING),
        account
      )
    ) AS tid,
    PARSE_DATE('%d.%m.%Y', datum) AS date,
    COALESCE(gutschrift, 0) + COALESCE(lastschrift, 0) AS amount,
    bewegungstyp AS type,
    label,
    kategorie AS category,
    REGEXP_EXTRACT(avisierungstext, r'(CH[A-Z0-9]{19})') AS related_iban,
    REGEXP_REPLACE(
      avisierungstext, 
      r'^KONTOÜBERTRAG (?:AUF|VON) CH[A-Z0-9]{19} ?', 
      ''
    ) AS memo,
    month,
    account AS account_iban
  FROM `${project_id}.banks.postfinance`
)
SELECT
  b.tid,
  b.date,
  b.amount,
  b.type,
  b.label,
  b.category,
  m_rel.name AS related_iban_name,
  b.related_iban,
  b.memo,
  b.month,
  m_acc.name AS account_iban_name,
  b.account_iban
FROM base b
LEFT JOIN `${project_id}.banks.postfinance_iban_mapping_v` m_rel
  ON b.related_iban = m_rel.iban
LEFT JOIN `${project_id}.banks.postfinance_iban_mapping_v` m_acc
  ON b.account_iban = m_acc.iban
