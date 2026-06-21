import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    DATABASE_URL = os.getenv("DATABASE_URL")
    DATA_GOV_API_KEY = os.getenv("DATA_GOV_IN_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    TARGET_CITY = os.getenv("TARGET_CITY", "Pune")
    TARGET_DISTRICT = os.getenv("TARGET_DISTRICT", "Pune")
    LANGUAGE_TARGET = os.getenv("LANGUAGE_TARGET", "Marathi")

    # How long the daemon sleeps between full ingestion cycles (default: 24 hours).
    API_FETCH_INTERVAL_SECONDS = int(os.getenv("API_FETCH_INTERVAL_SECONDS", "86400"))

    # Maximum rows requested from and parsed per data.gov.in endpoint per cycle.
    MAX_ROWS_PER_API_CALL = int(os.getenv("MAX_ROWS_PER_API_CALL", "100"))
