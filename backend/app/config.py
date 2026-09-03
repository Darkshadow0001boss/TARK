from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    app_name: str = "TARK"
    environment: str = "development"

    alpaca_api_key: str
    alpaca_secret_key: str
    alpaca_paper: bool = True

    gemini_api_key: str

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
    )


settings = Settings()

import os


# ============================================================
# TARK APPLICATION CONFIGURATION
# ============================================================


# ------------------------------------------------------------
# EXECUTION MODE
# ------------------------------------------------------------
#
# True:
#     Orders are built but NOT submitted.
#
# False:
#     Orders are submitted to the configured Alpaca account.
#
# IMPORTANT:
# Keep True during normal development and demos unless you
# explicitly want Alpaca paper execution.
# ------------------------------------------------------------

TARK_DRY_RUN = (
    os.getenv(
        "TARK_DRY_RUN",
        "true",
    ).lower()
    == "true"
)


# ------------------------------------------------------------
# POSITION MANAGEMENT
# ------------------------------------------------------------

CRITICAL_FRAGILITY = int(
    os.getenv(
        "TARK_CRITICAL_FRAGILITY",
        "80",
    )
)