# Applicataion configuration will be added here

from pydantic_settings import BaseSettings, SettingsConfigDict

from pathlib import Path

class Settings(BaseSettings) :
    app_name : str
    debug : bool
    database_url : str
    github_webhook_secret : str
    github_api_url : str = "https://api.github.com"
    github_app_id : int
    github_app_private_key_path : str
    openai_api_key : str
    openai_base_url : str
    redis_url : str

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent / "../../.env",
        extra="ignore"
    )

settings = Settings()