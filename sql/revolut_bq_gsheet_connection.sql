SELECT
    R.*
  , RM.Konto
FROM banks.revolut R
LEFT JOIN banks.revolut_mapping RM
ON R.description = RM.description