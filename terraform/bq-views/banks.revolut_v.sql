SELECT
  -- transaction id
  FARM_FINGERPRINT(
    CONCAT(
        IFNULL(type, "")
      , IFNULL(product, "")
      , IFNULL(started, DATE("1970-01-01"))
      , IFNULL(completed, DATE("1970-01-01"))
      , IFNULL(description, "")
      , IFNULL(amount, 0)
      , IFNULL(fee, 0)
      , IFNULL(currency, "")
      , IFNULL(state, "")
      , IFNULL(balance, 0)
      , IFNULL(account, "")
    )
  ) tid
  -- standard columns from Revolut
  , type
  , product
  , started
  , completed
  , description
  , amount
  , fee
  , currency
  , state
  , balance
  , account
  , month
  -- additional columns - features
  , MIN(started) OVER (PARTITION BY description) first_started
FROM banks.revolut_raw
ORDER BY started DESC, completed DESC
