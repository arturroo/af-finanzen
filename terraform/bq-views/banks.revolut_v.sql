SELECT
    *
  , MIN(started) OVER (PARTITION BY description) first_started
  , FARM_FINGERPRINT(CONCAT(
        type
      , product
      , started
      , completed
      , description
      , amount
      , fee
      , currency
      , state
      , balance)) tid
FROM banks.revolut
ORDER BY started DESC, completed DESC
