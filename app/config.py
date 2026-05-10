import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


default_sqlite_path = Path(os.getenv("LOCALAPPDATA", Path.cwd())) / "TeamTaskManager" / "team_task_manager.db"


class Settings(BaseSettings):
    app_name: str = "S and Groups"
    environment: Literal["development", "production", "test"] = "development"
    secret_key: str = Field(min_length=32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=60 * 24, gt=0)
    database_url: str = f"sqlite:///{default_sqlite_path.as_posix()}"
    secure_cookies: bool = False
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    cookie_domain: str | None = None
    cors_origins: str = ""
    frontend_url: str | None = None
    demo_password: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        normalized = value.strip()
        insecure_values = {
            "change-this-secret-before-production",
            "replace-me-with-a-long-random-secret",
            "team-task-manager-local-dev-secret-key",
        }
        if normalized in insecure_values:
            raise ValueError("SECRET_KEY must be changed to a long unique value before deployment.")
        return normalized

    @field_validator("frontend_url")
    @classmethod
    def normalize_frontend_url(cls, value: str | None) -> str | None:
        return value.strip().rstrip("/") if value else None

    @model_validator(mode="after")
    def finalize_settings(self) -> "Settings":
        if self.environment == "production" and not self.secure_cookies:
            raise ValueError("SECURE_COOKIES must be true in production.")
        if self.cookie_samesite == "none" and not self.secure_cookies:
            raise ValueError("SECURE_COOKIES must be true when COOKIE_SAMESITE is set to 'none'.")
        if self.environment == "production" and self.cookie_samesite == "none" and not self.resolved_cors_origins:
            raise ValueError(
                "At least one trusted frontend origin must be configured in production when COOKIE_SAMESITE is 'none'."
            )
        return self

    @property
    def resolved_cors_origins(self) -> list[str]:
        origins = [item.strip().rstrip("/") for item in self.cors_origins.split(",") if item.strip()]
        if self.frontend_url and self.frontend_url not in origins:
            origins.append(self.frontend_url)
        return origins


@lru_cache
def get_settings() -> Settings:
    return Settings()
