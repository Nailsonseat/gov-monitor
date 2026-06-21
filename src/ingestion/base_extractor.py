from typing import List, Dict, Any, Optional
import requests
from src.config import Config


class BaseGovExtractor:
    def __init__(self, resource_id: str, category: str, metric_name: str, unit: str, filter_column: Optional[str] = "District"):
        self.resource_id = resource_id
        self.category = category
        self.metric_name = metric_name
        self.unit = unit
        self.filter_column = filter_column
        self.api_url = f"https://api.data.gov.in/resource/{self.resource_id}"

    def fetch_raw(self) -> List[Dict[str, Any]]:
        print(f"-> Attempting live pull for [{self.metric_name}] via OGD API...")

        params = {
            "api-key": Config.DATA_GOV_API_KEY,
            "format": "json",
            "limit": 100
        }

        # 1. Ask the API to filter on the server side
        if self.filter_column:
            filter_val = Config.TARGET_CITY if self.filter_column.lower() == "city" else Config.TARGET_DISTRICT
            params[f"filters[{self.filter_column}]"] = filter_val

        # --- THE FIREWALL BYPASS HEADERS ---
        # Mimics the exact successful request from your browser network tab
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Mobile Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en",
            "Connection": "keep-alive"
        }

        try:
            # Inject the headers dictionary into the request
            response = requests.get(self.api_url, params=params, headers=headers, timeout=30)
            response.raise_for_status()

            # Extract the 'records' array from the JSON payload
            records = response.json().get("records", [])

            if not records:
                print(f"⚠️ Server returned an empty dataset for [{self.metric_name}].")
                return []

            # 2. Python Client-Side Filtering
            if self.filter_column:
                filter_val = Config.TARGET_CITY if self.filter_column.lower() == "city" else Config.TARGET_DISTRICT
                filtered_records = [
                    r for r in records
                    if str(r.get(self.filter_column, "")).lower() == filter_val.lower()
                ]
                if filtered_records:
                    records = filtered_records

            return records[:10]

        except requests.exceptions.ReadTimeout:
            print(f"⚠️ CRITICAL: data.gov.in API timed out while fetching [{self.metric_name}]. Returning 0 rows.")
            return []
        except requests.exceptions.RequestException as e:
            print(f"⚠️ CRITICAL: Network/HTTP error fetching [{self.metric_name}]: {e}. Returning 0 rows.")
            return []
        except Exception as e:
            print(f"⚠️ CRITICAL: Unexpected parsing error for [{self.metric_name}]: {e}. Returning 0 rows.")
            return []
