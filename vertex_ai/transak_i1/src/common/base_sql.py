def get_feature_selection_sql() -> str:
    """Returns the feature selection part of the query."""
    return """
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
    """

def get_label_selection_sql() -> str:
    """Returns the label selection and mapping part of the query."""
    return """,
            CASE
                WHEN i1_true_label = 'PK Prezenty' THEN 'PK Rest'
                WHEN i1_true_label = 'PK Auto' THEN 'PK Rest'
                WHEN i1_true_label = 'Apt' THEN 'PK Kasia'
                ELSE i1_true_label
            END AS i1_true_label
    """

def get_base_from_where_sql() -> str:
    """Returns the FROM and base WHERE clause."""
    return """
        FROM `af-finanzen.monatsabschluss.revolut_abrechnung`
        WHERE type NOT IN ('FEE', 'ATM')
    """

def train_data_query() -> str:
    """
    Returns the full query for fetching raw, labeled data for training.
    Combines feature selection, label selection, and the FROM clause.
    """
    return f"""
        {get_feature_selection_sql()}
        {get_label_selection_sql()}
        {get_base_from_where_sql()}
    """

def predict_data_query() -> str:
    """
    Returns the full query for fetching raw, unlabeled data for prediction for a given month.
    Combines feature selection and the FROM clause, and adds a filter for the given month.
    """
    return f"""
        {get_feature_selection_sql()}
        {get_base_from_where_sql()}
        AND month = {{month_placeholder}}
    """
