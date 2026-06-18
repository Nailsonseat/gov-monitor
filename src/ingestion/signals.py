from typing import Dict, Any
from gov_monitor.ingestion.base_extractor import BaseGovExtractor


class AQIExtractor(BaseGovExtractor):
    def __init__(self):
        super().__init__("3b01bab6-3b07-44c1-ab85-056345634563", "Environment", "AQI", "Index")

    def parse_value(self, record: Dict[str, Any]) -> float:
        return float(record.get("aqi_value", 0))


class MandiExtractor(BaseGovExtractor):
    def __init__(self):
        super().__init__("9ef84268-d588-465a-a308-a86d9fb11922", "Economy", "Mandi_Price", "INR/Quintal")

    def parse_value(self, record: Dict[str, Any]) -> float:
        return float(record.get("modal_price", 0))


class ReservoirExtractor(BaseGovExtractor):
    def __init__(self):
        super().__init__("5cc7dfbc-12aa-418b-b892-03487c631244", "Utilities", "Reservoir_Level", "Percent")

    def parse_value(self, record: Dict[str, Any]) -> float:
        return float(record.get("current_storage_pct", 0))


class VahanExtractor(BaseGovExtractor):
    def __init__(self):
        super().__init__("7a02b1f8-08ee-449d-bca7-8dfa192bc552", "Infrastructure", "Ev_Registrations", "Units")

    def parse_value(self, record: Dict[str, Any]) -> float:
        return float(record.get("ev_count", 0))


class HealthExtractor(BaseGovExtractor):
    def __init__(self):
        super().__init__("a3b4c5d6-e7f8-490a-b1c2-d3e4f5a6b7c8", "Health", "Active_Beds", "Beds")

    def parse_value(self, record: Dict[str, Any]) -> float:
        return float(record.get("available_beds", 0))


SIGNAL_EXTRACTORS = [
    AQIExtractor,
    MandiExtractor,
    ReservoirExtractor,
    VahanExtractor,
    HealthExtractor
]
