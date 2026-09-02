from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "TARK"
    environment: str = "development"

    alpaca_api_key: str
    alpaca_secret_key: str
    alpaca_paper: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()