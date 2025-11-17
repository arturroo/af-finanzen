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

def get_train_from_sql() -> str:
    return """
        FROM `af-finanzen.monatsabschluss.revolut_abrechnung`
    """

def get_predict_from_sql() -> str:
    return """
        FROM `af-finanzen.banks.revolut_v`
    """

def get_common_where_sql() -> str:
    return """
        WHERE 
            type NOT IN ('FEE', 'ATM') -- less then 10 examples of each type
            AND ABS(amount) < 900 -- outliers
            -- AND month < 202501 -- only for demonstration purposes to train bad model
    """

def train_data_query() -> str:
    """
    Returns the full query for fetching raw, labeled data for training.
    Combines feature selection, label selection, and the FROM clause.
    """
    return f"""
        {get_feature_selection_sql()}
        {get_label_selection_sql()}
        {get_train_from_sql()}
        {get_common_where_sql()}
    """

def predict_data_query() -> str:
    """
    Returns the full query for fetching raw, unlabeled data for prediction for a given month.
    Combines feature selection and the FROM clause, and adds a filter for the given month.
    """
    return f"""
        {get_feature_selection_sql()}
        {get_predict_from_sql()}
        {get_common_where_sql()}
        AND month = {{month_placeholder}}
    """

def get_monitoring_feature_selection_sql() -> str:
    """Returns the feature selection part of the monitoring query."""
    return "SELECT PREDICTIONS.*"

def get_monitoring_label_selection_sql() -> str:
    """Returns the label selection part of the monitoring query."""
    return ", LABELS.name AS i1_pred_label"

def get_monitoring_from_sql() -> str:
    """Returns the FROM and JOIN clauses for the monitoring query."""
    return """
        FROM `{table_placeholder}` AS PREDICTIONS
        LEFT JOIN `af-finanzen.transak.i1_labels` AS LABELS ON PREDICTIONS.i1_pred_label_id = LABELS.id
    """

def get_monitoring_where_sql() -> str:
    """Returns the WHERE clause for the monitoring query."""
    return """
        WHERE PREDICTIONS.month = {month_placeholder}
    """

def monitoring_query() -> str:
    """
    Returns the full query for fetching prediction data for monitoring.
    Combines modular SQL parts into a single query.
    """
    return f"""
        {get_monitoring_feature_selection_sql()}
        {get_monitoring_label_selection_sql()}
        {get_monitoring_from_sql()}
        {get_monitoring_where_sql()}
    """

def labels_query() -> str:
    """
    Returns the SQL query for fetching the label mapping from the i1_labels table.
    """
    return """
        SELECT
            id,
            name
        FROM
            `af-finanzen.transak.i1_labels`
    """