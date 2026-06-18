from typing import Dict, Any
from src.ingestion.base_extractor import BaseGovExtractor


class AQIExtractor(BaseGovExtractor):
    def __init__(self):
        super().__init__("3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69", "Environment", "AQI", "Index", filter_column="City")

    def parse_value(self, record: Dict[str, Any]) -> float:
        # Maps directly to the 'Pollutant Avg' attribute from your preview
        # Uses .get falling back to 0 if the value is temporarily null due to telemetry dropouts
        val = record.get("pollutant_avg", record.get("Pollutant Avg", 0))
        return float(val) if val is not None else 0.0


class MandiExtractor(BaseGovExtractor):
    def __init__(self):
        super().__init__("9ef84268-d588-465a-a308-a864a43d0070", "Economy", "Mandi_Price", "INR/Quintal", filter_column="District")

    def parse_value(self, record: Dict[str, Any]) -> float:
        # Maps directly to the 'Modal Price' or encoded variations
        val = record.get("modal_price", record.get("Modal X0020 Price", 0))
        return float(val) if val is not None else 0.0


class ReservoirExtractor(BaseGovExtractor):
    def __init__(self):
        super().__init__("9ef84268-d588-465a-a308-a864a43d0070", "Utilities", "Reservoir_Level", "Percent", filter_column="District")

    def parse_value(self, record: Dict[str, Any]) -> float:
        # Uses the 'Storage' or live capacity percentage relative to 'Full Reservoir Level'
        # If 'Storage' is an absolute metric, we can capture the raw volume or current gauge 'Level'
        val = record.get("storage", record.get("Storage", record.get("level", record.get("Level", 0))))
        return float(val) if val is not None else 0.0


class AnganwadiJJMExtractor(BaseGovExtractor):
    def __init__(self):
        # 4. Anganwadis with Tap Connection under Jal Jeevan Mission (JJM)
        # Category mapped to Infrastructure; captures size of target groups served with clean water
        super().__init__("6cf7a5f8-a50c-4b94-bd90-742bfe9d507b", "Infrastructure", "Anganwadi_Students_Served", "Students", filter_column="District Name")

    def parse_value(self, record: Dict[str, Any]) -> float:
        # Maps directly to the 'No Of Student' attribute from your preview
        val = record.get("no_of_student", record.get("No Of Student", 0))
        return float(val) if val is not None else 0.0


class DistrictRainfallExtractor(BaseGovExtractor):
    def __init__(self):
        # 5. Daily District-wise Rainfall Data
        super().__init__("6c05cd1b-ed59-40c2-bc31-e314f39c6971", "Environment", "Rainfall", "mm", filter_column="District")

    def parse_value(self, record: Dict[str, Any]) -> float:
        # Maps directly to the 'Avg Rainfall' attribute from your preview
        val = record.get("avg_rainfall", record.get("Avg Rainfall", 0))
        return float(val) if val is not None else 0.0


SIGNAL_EXTRACTORS = [
    AQIExtractor,
    MandiExtractor,
    ReservoirExtractor,
    AnganwadiJJMExtractor,
    DistrictRainfallExtractor
]
