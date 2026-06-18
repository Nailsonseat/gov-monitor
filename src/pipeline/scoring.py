from typing import Dict, Any, Optional


def calculate_confidence(
    value: Optional[float],
    raw_record: Dict[str, Any],
    metric_name: str
) -> float:
    """
    Evaluates individual data rows to assign an algorithmic trust score from 0.0 to 1.0.
    """
    score = 1.0

    # Rule 1: Hard Fail for Vital Target Points
    if value is None or value < 0:
        return 0.0

    # Rule 2: Metric Specific Range Verification & Anomaly Penalties
    if metric_name == "AQI":
        if value > 500 or value == 0:
            score -= 0.7  # Telemetry collection out of bounds
    elif metric_name == "Mandi_Price":
        if value < 100 or value > 50000:
            score -= 0.6  # Severe extreme marketplace entry noise
    elif metric_name == "Reservoir_Level":
        if value > 100.0:  # Percentage storage boundaries
            score -= 0.5
    elif metric_name == "Ev_Registrations":
        if value > 10000:  # Statistically anomalous spike for single batch window
            score -= 0.3
    elif metric_name == "Active_Beds":
        if value == 0:
            score -= 0.4  # Data field potentially dropped or unrecorded

    # Rule 3: Missing Regional Classification Data Context
    if not raw_record.get("state") or not raw_record.get("district"):
        score -= 0.2

    return round(max(0.0, score), 2)
