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
