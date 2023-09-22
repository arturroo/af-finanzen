WITH F AS (
  WITH RN AS(
    SELECT
      description
      , started
      , row_number() OVER(PARTITION BY description ORDER BY started) rn
    FROM banks.revolut
  )
  SELECT 
    description first_description
    , started first_started FROM RN
  WHERE RN.rn = 1
  ORDER BY first_started
)
SELECT * EXCEPT(first_description) FROM banks.revolut R
LEFT JOIN F ON R.description = F.first_description
ORDER BY started DESC