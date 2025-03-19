SELECT
    description AS in
    , new_label AS out
    , amount AS value
FROM banks.revolut
ORDER BY started DESC, completed DESC
