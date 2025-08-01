def raw_data_query():

    raw_query = """
        SELECT
              tid
            , type
            , EXTRACT(YEAR  FROM started) AS started_year
            , EXTRACT(MONTH FROM started) AS started_month
            , EXTRACT(DAY   FROM started) AS started_day
            , MOD(EXTRACT(DAYOFWEEK FROM started) + 5, 7) AS started_weekday
            , EXTRACT(YEAR  FROM first_started) AS first_started_year
            , EXTRACT(MONTH FROM first_started) AS first_started_month
            , EXTRACT(DAY   FROM first_started) AS first_started_day
            , MOD(EXTRACT(DAYOFWEEK FROM first_started) + 5, 7) AS first_started_weekday
            , LOWER(description) AS description
            , amount
            , currency
            , CASE
                WHEN i1_true_label = 'PK Prezenty' THEN 'PK Rest'
                WHEN i1_true_label = 'PK Auto' THEN 'PK Rest'
                WHEN i1_true_label = 'Apt' THEN 'PK Kasia'
                ELSE i1_true_label
            END AS i1_true_label
        FROM `af-finanzen.monatsabschluss.revolut_abrechnung`
        WHERE
            type NOT IN ('FEE', 'ATM')
    """
    return raw_query