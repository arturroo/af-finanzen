from kfp.dsl import component, Output
from typing import Optional

@component(
    base_image="python:3.9",
)
def prediction_config_generator_op(
    # resolved_prediction_month: Output[int],
    month: Optional[int] = None
) -> int:
    """
    Resolves the prediction month.
    Defaults to the previous month if no month is provided.
    """
    from datetime import datetime, timedelta

    print(f"Generating prediction config for month: {month}")
    if month is not None:
        print(f"Prediction month provided: {month}")
        resolved_month = month
    else:
        print("No prediction month provided, calculating default (last month).")
        # Go back 30 days to ensure we are in the previous month.
        last_month_date = datetime.now() - timedelta(days=30)
        resolved_month_str = last_month_date.strftime("%Y%m")
        resolved_month = int(resolved_month_str)
        print(f"Default prediction month calculated: {resolved_month}")

    # resolved_prediction_month.value = resolved_month_str
    return resolved_month
