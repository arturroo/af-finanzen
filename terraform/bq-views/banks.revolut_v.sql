SELECT
    *
  , MIN(started) OVER (PARTITION BY description) first_started
FROM banks.revolut
ORDER BY started DESC, completed DESC
