from typing import Dict, Any, Optional, List, Tuple, Union

# Canonical noisy / sentinel values returned by data.gov.in or upstream sources.
_NOISY_STRINGS = frozenset({"", "n/a", "na", "null", "none", "-", "nan", "nil", "#n/a"})

# Deterministic confidence deduction applied per missing or noisy field.
MISSING_FIELD_PENALTY = 0.12


def is_missing_or_noisy(value: Any) -> bool:
    """Return True when a raw API value is absent, empty, or a known corrupt sentinel."""
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in _NOISY_STRINGS
    return False


def normalize_numeric(value: Any, fallback: float = 0.0) -> Tuple[float, bool]:
    """
    Coerce a raw API field to float, falling back when missing or noisy.

    Returns (normalized_value, was_imputed) where was_imputed is True when the
    original value could not be trusted and the fallback was applied.
    """
    if is_missing_or_noisy(value):
        return fallback, True
    try:
        return float(value), False
    except (TypeError, ValueError):
        return fallback, True


def normalize_string(value: Any, fallback: str = "Unknown") -> Tuple[str, bool]:
    """
    Coerce a raw API field to a clean string, falling back when missing or noisy.

    Returns (normalized_string, was_imputed).
    """
    if is_missing_or_noisy(value):
        return fallback, True
    return str(value).strip(), False


def normalize_metric_field(
    record: Dict[str, Any],
    field_key: str,
    fallback: float = 0.0,
) -> Tuple[float, List[str]]:
    """
    Read and normalize a single numeric metric column from a raw API record.

    Appends a human-readable issue tag when imputation occurs so scoring can
    apply a transparent confidence penalty.
    """
    raw_value = record.get(field_key)
    normalized, was_imputed = normalize_numeric(raw_value, fallback=fallback)
    issues: List[str] = []
    if was_imputed:
        issues.append(f"missing_or_noisy:{field_key}")
    return normalized, issues


def audit_record_fields(
    record: Dict[str, Any],
    metric_name: str,
    value_field: str,
) -> List[str]:
    """
    Scan a raw record for missing, null, empty, or corrupt field data.

    Checks the primary value column plus geographic context markers so every
    gap is surfaced before persistence and LLM synthesis.
    """
    issues: List[str] = []

    if is_missing_or_noisy(record.get(value_field)):
        issues.append(f"missing_or_noisy:{value_field}")

    # Reservoir metrics lack standard district strings; skip unfair geo checks.
    if metric_name != "Reservoir_Level":
        geo_keys = [
            "state", "State", "State Name", "state_name",
            "district", "District", "District Name", "district_name",
            "city", "City",
        ]
        for key in geo_keys:
            if key in record and is_missing_or_noisy(record.get(key)):
                issues.append(f"missing_or_noisy:{key}")

    return issues


def calculate_confidence(
    value: Optional[float],
    raw_record: Dict[str, Any],
    metric_name: str,
    field_issues: Optional[List[str]] = None,
) -> float:
    """
    Assign an algorithmic trust score from 0.0 to 1.0 for a normalized row.

    Applies a fixed penalty per missing/noisy parameter so degraded records are
    flagged transparently for the dashboard and LLM synthesis layer.
    """
    issues = list(field_issues or [])
    score = 1.0

    # Deterministic penalty for every missing or noisy parameter detected upstream.
    score -= len(issues) * MISSING_FIELD_PENALTY

    # Hard fail when the normalized numeric value itself is unusable.
    if value is None or value < 0:
        return 0.0

    # Metric-specific range verification and anomaly penalties.
    if metric_name == "AQI":
        if value > 500 or value == 0:
            score -= 0.7
    elif metric_name == "Mandi_Price":
        if value < 100 or value > 50000:
            score -= 0.6
    elif metric_name == "Reservoir_Level":
        if value > 10000:
            score -= 0.5
    elif metric_name == "Anganwadi_Students_Served":
        if value == 0:
            score -= 0.4
        elif value > 1000:
            score -= 0.3
    elif metric_name == "Rainfall":
        if value > 300.0:
            score -= 0.4

    # Missing regional classification context (structural API layout variations).
    if metric_name != "Reservoir_Level":
        has_state = any(k in raw_record for k in ["state", "State", "State Name", "state_name"])
        has_regional_marker = any(
            k in raw_record
            for k in ["district", "District", "District Name", "district_name", "city", "City"]
        )
        if not has_state or not has_regional_marker:
            score -= 0.2

    return round(max(0.0, min(1.0, score)), 2)
