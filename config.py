# config.py
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DB_HOST: str
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    LOG_LEVEL: str = "INFO"


settings = Settings()
