# Applicataion configuration will be added here

from pydantic_settings import BaseSettings, SettingsConfigDict

from pathlib import Path

class Settings(BaseSettings) :
    app_name : str
    debug : bool
    database_url : str
    github_webhook_secret : str

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent / "../../.env",
        extra="ignore"
    )

settings = Settings()