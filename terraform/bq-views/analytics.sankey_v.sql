SELECT
    description AS dst
    -- , new_label AS src
    , "mockup" AS src
    , amount AS value
FROM banks.revolut
ORDER BY started DESC, completed DESC
