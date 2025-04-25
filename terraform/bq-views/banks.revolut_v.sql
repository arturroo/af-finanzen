
SELECT
  -- transaction id
  FARM_FINGERPRINT(
    CONCAT(
        IFNULL(RAW.type, "")
      , IFNULL(RAW.product, "")
      , IFNULL(RAW.started, DATE("1970-01-01"))
      , IFNULL(RAW.completed, DATE("1970-01-01"))
      , IFNULL(RAW.description, "")
      , IFNULL(RAW.amount, 0)
      , IFNULL(RAW.fee, 0)
      , IFNULL(RAW.currency, "")
      , IFNULL(RAW.state, "")
      , IFNULL(RAW.balance, 0)
      , IFNULL(RAW.account, "")
    )
  ) tid
  -- standard columns from Revolut
  , RAW.type
  , RAW.product
  , RAW.started
  , RAW.completed
  , RAW.description
  , RAW.amount
  , RAW.fee
  , RAW.currency
  , RAW.state
  , RAW.balance
  , RAW.account
  , RAW.month
  -- additional columns - features
  , MIN(RAW.started) OVER (PARTITION BY RAW.description) first_started
FROM `af-finanzen.banks.revolut_raw` RAW
ORDER BY RAW.month DESC, RAW.started DESC