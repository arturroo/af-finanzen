SELECT
    description AS dst
    -- , new_label AS src
    , "mockup" AS src
    , amount AS value
FROM banks.revolut_v
ORDER BY started DESC, completed DESC
