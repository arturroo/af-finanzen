SELECT
  *
  -- label
  , CASE
      WHEN RAW.description in ("Amazon Prime") THEN "PK Abo"
      WHEN RAW.description like "Refund from %mazon.de" THEN "eShop"
      When RAW.type = "CARD_REFUND" THEN "Rückzahlung"
      WHEN RAW.description in ("Amazon", "Allegro") THEN "eShop"
      WHEN RAW.type = "EXCHANGE" THEN "Exchange"
      -- WHEN RMI.Konto IS NULL THEN IF(i0P.true_label="Others", "PK Rest", i0P.true_label)
      WHEN RMI.Konto IS NULL THEN "PK Rest"
      ELSE
        RMI.Konto
    END i1_true_label
FROM banks.revolut_v RAW
LEFT JOIN `af-finanzen.banks.revolut_mapping_internal` RMI
  ON RAW.description = RMI.description
WHERE
  RAW.month < 202404
