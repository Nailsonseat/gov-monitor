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
            score -= 0.7  # Telemetry connection out of bounds
    elif metric_name == "Mandi_Price":
        if value < 100 or value > 50000:
            score -= 0.6  # Severe extreme marketplace entry noise
    elif metric_name == "Reservoir_Level":
        if value > 10000:  # Adjusting for absolute storage capacity volume spikes
            score -= 0.5
    elif metric_name == "Anganwadi_Students_Served":
        if value == 0:
            score -= 0.4  # Flag centers registering zero attendance
        elif value > 1000:
            score -= 0.3  # Statistically improbable student count for a single center
    elif metric_name == "Rainfall":
        if value > 300.0:
            score -= 0.4  # Extreme outlier precipitation entry (typo safety)

    # Rule 3: Missing Regional Classification Data Context
    # Reservoir metrics naturally lack standard district strings; bypass check to avoid unfair degradation
    if metric_name != "Reservoir_Level":
        # Scan for structural variations of geographic markers across layout variations
        has_state = any(k in raw_record for k in ["state", "State", "State Name", "state_name"])
        has_regional_marker = any(k in raw_record for k in ["district", "District", "District Name", "district_name", "city", "City"])

        if not has_state or not has_regional_marker:
            score -= 0.2

    return round(max(0.0, score), 2)
