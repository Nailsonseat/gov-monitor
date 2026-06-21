from typing import Dict, Any, Tuple, List
from src.ingestion.base_extractor import BaseGovExtractor
from src.pipeline.scoring import normalize_metric_field, audit_record_fields


class AQIExtractor(BaseGovExtractor):
    value_field = "avg_value"

    def __init__(self):
        super().__init__("3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69", "Environment", "AQI", "Index", filter_column="city")

    def parse_value(self, record: Dict[str, Any]) -> float:
        value, _ = normalize_metric_field(record, self.value_field, fallback=0.0)
        return value

    def parse_with_audit(self, record: Dict[str, Any]) -> Tuple[float, List[str]]:
        value, issues = normalize_metric_field(record, self.value_field, fallback=0.0)
        issues.extend(audit_record_fields(record, "AQI", self.value_field))
        return value, list(dict.fromkeys(issues))


class MandiExtractor(BaseGovExtractor):
    value_field = "modal_price"

    def __init__(self):
        super().__init__("9ef84268-d588-465a-a308-a864a43d0070", "Economy", "Mandi_Price", "INR/Quintal", filter_column="district")

    def parse_value(self, record: Dict[str, Any]) -> float:
        value, _ = normalize_metric_field(record, self.value_field, fallback=0.0)
        return value

    def parse_with_audit(self, record: Dict[str, Any]) -> Tuple[float, List[str]]:
        value, issues = normalize_metric_field(record, self.value_field, fallback=0.0)
        issues.extend(audit_record_fields(record, "Mandi_Price", self.value_field))
        return value, list(dict.fromkeys(issues))


class ReservoirExtractor(BaseGovExtractor):
    value_field = "Storage"

    def __init__(self):
        super().__init__("1fc2148c-fc41-46f5-a364-bdc03f77053f", "Utilities", "Reservoir_Level", "Percent", filter_column=None)

    def parse_value(self, record: Dict[str, Any]) -> float:
        value, _ = normalize_metric_field(record, self.value_field, fallback=0.0)
        return value

    def parse_with_audit(self, record: Dict[str, Any]) -> Tuple[float, List[str]]:
        value, issues = normalize_metric_field(record, self.value_field, fallback=0.0)
        issues.extend(audit_record_fields(record, "Reservoir_Level", self.value_field))
        return value, list(dict.fromkeys(issues))


class AnganwadiJJMExtractor(BaseGovExtractor):
    value_field = "no_of_student"

    def __init__(self):
        super().__init__("6cf7a5f8-a50c-4b94-bd90-742bfe9d507b", "Infrastructure", "Anganwadi_Students_Served", "Students", filter_column="district_name")

    def parse_value(self, record: Dict[str, Any]) -> float:
        value, _ = normalize_metric_field(record, self.value_field, fallback=0.0)
        return value

    def parse_with_audit(self, record: Dict[str, Any]) -> Tuple[float, List[str]]:
        value, issues = normalize_metric_field(record, self.value_field, fallback=0.0)
        issues.extend(audit_record_fields(record, "Anganwadi_Students_Served", self.value_field))
        return value, list(dict.fromkeys(issues))


class DistrictRainfallExtractor(BaseGovExtractor):
    value_field = "Avg_rainfall"

    def __init__(self):
        super().__init__("6c05cd1b-ed59-40c2-bc31-e314f39c6971", "Environment", "Rainfall", "mm", filter_column="District")

    def parse_value(self, record: Dict[str, Any]) -> float:
        value, _ = normalize_metric_field(record, self.value_field, fallback=0.0)
        return value

    def parse_with_audit(self, record: Dict[str, Any]) -> Tuple[float, List[str]]:
        value, issues = normalize_metric_field(record, self.value_field, fallback=0.0)
        issues.extend(audit_record_fields(record, "Rainfall", self.value_field))
        return value, list(dict.fromkeys(issues))


SIGNAL_EXTRACTORS = [
    AQIExtractor,
    MandiExtractor,
    ReservoirExtractor,
    AnganwadiJJMExtractor,
    DistrictRainfallExtractor,
]
