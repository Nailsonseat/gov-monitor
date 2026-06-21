from typing import List, Dict, Any, Optional
import requests
from src.config import Config


class BaseGovExtractor:
    # Subclasses set the API column key used for numeric parsing.
    value_field: str = ""

    def __init__(self, resource_id: str, category: str, metric_name: str, unit: str, filter_column: Optional[str] = "District"):
        self.resource_id = resource_id
        self.category = category
        self.metric_name = metric_name
        self.unit = unit
        self.filter_column = filter_column
        self.api_url = f"https://api.data.gov.in/resource/{self.resource_id}"

    def fetch_raw(self) -> List[Dict[str, Any]]:
        """
        Pull records from data.gov.in with server-side filters and a configurable
        row cap (MAX_ROWS_PER_API_CALL) to bound each ingestion cycle.
        """
        row_limit = Config.MAX_ROWS_PER_API_CALL
        print(
            f"[INGESTION] Fetching signal [{self.metric_name}] "
            f"(category={self.category}, limit={row_limit}) via OGD API..."
        )

        params = {
            "api-key": Config.DATA_GOV_API_KEY,
            "format": "json",
            "limit": row_limit,
        }

        if self.filter_column:
            filter_val = Config.TARGET_CITY if self.filter_column.lower() == "city" else Config.TARGET_DISTRICT
            params[f"filters[{self.filter_column}]"] = filter_val

        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Mobile Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en",
            "Connection": "keep-alive",
        }

        try:
            response = requests.get(self.api_url, params=params, headers=headers, timeout=30)
            response.raise_for_status()

            payload = response.json()
            total_available = payload.get("total", "unknown")
            records = payload.get("records", [])

            print(
                f"[INGESTION] Signal [{self.metric_name}] API response: "
                f"{len(records)} record(s) returned (total_available={total_available}, "
                f"parsed_cap={row_limit})"
            )

            if not records:
                print(f"[INGESTION] WARNING: Empty dataset for [{self.metric_name}].")
                return []

            if self.filter_column:
                filter_val = Config.TARGET_CITY if self.filter_column.lower() == "city" else Config.TARGET_DISTRICT
                filtered_records = [
                    r for r in records
                    if str(r.get(self.filter_column, "")).lower() == filter_val.lower()
                ]
                if filtered_records:
                    records = filtered_records
                    print(
                        f"[INGESTION] Signal [{self.metric_name}] client-side filter "
                        f"on [{self.filter_column}]={filter_val}: {len(records)} row(s)"
                    )

            return records[:row_limit]

        except requests.exceptions.ReadTimeout:
            print(f"[INGESTION] CRITICAL: API timed out for [{self.metric_name}]. Returning 0 rows.")
            return []
        except requests.exceptions.RequestException as e:
            print(f"[INGESTION] CRITICAL: Network/HTTP error for [{self.metric_name}]: {e}. Returning 0 rows.")
            return []
        except Exception as e:
            print(f"[INGESTION] CRITICAL: Unexpected parsing error for [{self.metric_name}]: {e}. Returning 0 rows.")
            return []

    def parse_value(self, record: Dict[str, Any]) -> float:
        raise NotImplementedError("Each signal extractor must implement parse_value().")
