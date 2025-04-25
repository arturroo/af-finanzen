WITH i0P AS (
  SELECT
    description
    , true_label
  FROM `af-finanzen.transak.i0_predictions`
  GROUP BY
      description
    , true_label
)
SELECT
  *
  -- label
  , CASE
      WHEN RAW.description in ("Amazon Prime") THEN "PK Abo"
      WHEN RAW.description like "Refund from %mazon.de" OR RAW.type = "CARD_REFUND" THEN "Rückzahlung"
      WHEN RAW.description in ("Amazon", "Allegro") THEN "eShop"
      WHEN RAW.type = "EXCHANGE" THEN "Exchange"
      WHEN RMI.Konto IS NULL THEN IF(i0P.true_label="Others", "PK Rest", i0P.true_label)
      ELSE
        RMI.Konto
    END i1_true_label
FROM banks.revolut_v
LEFT JOIN `af-finanzen.banks.revolut_mapping_internal` RMI
  ON RAW.description = RMI.description
LEFT JOIN i0P
  ON RAW.description = i0P.description
