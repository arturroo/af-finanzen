SELECT
    U.*
  , UM.Konto
FROM banks.ubs_v U
LEFT JOIN banks.ubs_mapping UM
ON
  U.Buchungstext = UM.Buchungstext
  -- AND U.Branche = UM.Branche