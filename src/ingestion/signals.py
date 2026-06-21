from typing import Dict, Any
from src.ingestion.base_extractor import BaseGovExtractor


class AQIExtractor(BaseGovExtractor):
    def __init__(self):
        # Uses exact lowercase "city" for API filtering
        super().__init__("3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69", "Environment", "AQI", "Index", filter_column="city")

    def parse_value(self, record: Dict[str, Any]) -> float:
        # Maps exactly to the "avg_value" key in your JSON payload
        val = record.get("avg_value", 0)
        return float(val) if val is not None else 0.0


class MandiExtractor(BaseGovExtractor):
    def __init__(self):
        # Uses exact lowercase "district" for API filtering
        super().__init__("9ef84268-d588-465a-a308-a864a43d0070", "Economy", "Mandi_Price", "INR/Quintal", filter_column="district")

    def parse_value(self, record: Dict[str, Any]) -> float:
        # Maps exactly to the "modal_price" key in your JSON payload
        val = record.get("modal_price", 0)
        return float(val) if val is not None else 0.0


class ReservoirExtractor(BaseGovExtractor):
    def __init__(self):
        # Reservoirs don't use district filtering, so we keep filter_column=None
        super().__init__("1fc2148c-fc41-46f5-a364-bdc03f77053f", "Utilities", "Reservoir_Level", "Percent", filter_column=None)

    def parse_value(self, record: Dict[str, Any]) -> float:
        # Maps exactly to the capitalized "Storage" key in your JSON payload
        val = record.get("Storage", 0)
        return float(val) if val is not None else 0.0


class AnganwadiJJMExtractor(BaseGovExtractor):
    def __init__(self):
        # Uses exact lowercase "district_name" for API filtering
        super().__init__("6cf7a5f8-a50c-4b94-bd90-742bfe9d507b", "Infrastructure", "Anganwadi_Students_Served", "Students", filter_column="district_name")

    def parse_value(self, record: Dict[str, Any]) -> float:
        # Maps exactly to the "no_of_student" key in your JSON payload
        val = record.get("no_of_student", 0)
        return float(val) if val is not None else 0.0


class DistrictRainfallExtractor(BaseGovExtractor):
    def __init__(self):
        # Uses exact capitalized "District" for API filtering
        super().__init__("6c05cd1b-ed59-40c2-bc31-e314f39c6971", "Environment", "Rainfall", "mm", filter_column="District")

    def parse_value(self, record: Dict[str, Any]) -> float:
        # Maps exactly to the capitalized "Avg_rainfall" key in your JSON payload
        val = record.get("Avg_rainfall", 0)
        return float(val) if val is not None else 0.0


SIGNAL_EXTRACTORS = [
    AQIExtractor,
    MandiExtractor,
    ReservoirExtractor,
    AnganwadiJJMExtractor,
    DistrictRainfallExtractor
]
