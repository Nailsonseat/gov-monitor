from typing import List, Dict, Any
import requests
from gov_monitor.config import Config


class BaseGovExtractor:
    def __init__(self, resource_id: str, category: str, metric_name: str, unit: str):
        self.resource_id = resource_id
        self.category = category
        self.metric_name = metric_name
        self.unit = unit
        self.api_url = f"https://api.data.gov.in/resource/{self.resource_id}"

    def fetch_raw(self) -> List[Dict[str, Any]]:
        params = {
            "api-key": Config.DATA_GOV_API_KEY,
            "format": "json",
            "filters[district]": Config.TARGET_DISTRICT,
            "limit": 10
        }
        try:
            response = requests.get(self.api_url, params=params, timeout=15)
            if response.status_code == 200:
                return response.json().get("records", [])
            return []
        except Exception:
            return []  # Defensive resilience against public server connection dropouts
