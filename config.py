"""
AI Analytics Agent — Configuration Module
Centralised configuration using pydantic-settings, loading from .env file.
"""

import secrets
import logging
from pathlib import Path
from typing import List, Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application-wide settings loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Application ---
    app_env: Literal["development", "production"] = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = False
    secret_key: str = ""

    # --- Security ---
    cors_origins: str = "*"
    allowed_hosts: str = "*"

    # --- Data Mode ---
    data_mode: Literal["demo", "mssql"] = "demo"

    # --- MS SQL Server ---
    mssql_host: str = "localhost"
    mssql_port: int = 1433
    mssql_database: str = "analytics"
    mssql_user: str = "sa"
    mssql_password: str = ""
    mssql_driver: str = "ODBC Driver 17 for SQL Server"

    # --- AppTask ---
    apptask_mode: Literal["api", "db", "csv"] = "csv"
    apptask_api_url: str = ""
    apptask_api_token: str = ""
    apptask_csv_path: str = "data/demo/tasks.csv"

    # --- AI Provider ---
    ai_provider: Literal["openai", "anthropic", "none"] = "none"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"

    # --- Google Sheets ---
    google_sheets_enabled: bool = False
    google_service_account_file: str = "credentials/google_service_account.json"
    google_spreadsheet_name: str = "AI Analytics Agent Report"

    # --- Analytics Storage ---
    analytics_db_url: str = f"sqlite:///{BASE_DIR / 'data' / 'analytics.db'}"

    # --- Scheduler ---
    etl_schedule_hours: int = 24
    etl_schedule_enabled: bool = False

    # --- UI ---
    ui_language: Literal["ru", "en"] = "ru"

    # --- Derived ---
    @property
    def mssql_connection_string(self) -> str:
        return (
            f"mssql+pyodbc://{self.mssql_user}:{self.mssql_password}"
            f"@{self.mssql_host}:{self.mssql_port}/{self.mssql_database}"
            f"?driver={self.mssql_driver.replace(' ', '+')}"
        )

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS comma-separated string into a list."""
        if self.cors_origins == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def allowed_hosts_list(self) -> List[str]:
        """Parse ALLOWED_HOSTS comma-separated string into a list."""
        if self.allowed_hosts == "*":
            return ["*"]
        return [h.strip() for h in self.allowed_hosts.split(",") if h.strip()]

    @model_validator(mode="after")
    def _validate_production_settings(self) -> "Settings":
        """Enforce secure settings in production."""
        if not self.secret_key:
            if self.app_env == "production":
                raise ValueError(
                    "SECRET_KEY is required in production mode. "
                    "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
                )
            # Auto-generate for development
            self.secret_key = secrets.token_urlsafe(32)
            logger.warning("SECRET_KEY not set — auto-generated for development")

        if self.app_env == "production" and self.secret_key == "change-me":
            raise ValueError(
                "SECRET_KEY must not be 'change-me' in production mode. "
                "Generate a secure key with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
            )

        if self.app_env == "production" and self.app_debug:
            logger.warning("APP_DEBUG=true in production mode — overriding to false")
            self.app_debug = False

        return self


settings = Settings()
