from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Telegram Bot
    bot_token: str = Field(..., description="Telegram Bot API token")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/mathtrainer",
        description="Async PostgreSQL connection URL",
    )

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )

    # WebApp backend
    webapp_url: str = Field(default="http://localhost:8080", description="Public URL for Telegram Web App API")
    webapp_host: str = Field(default="0.0.0.0", description="Bind host for local web server")
    webapp_port: int = Field(default=8080, description="Bind port for local web server")

    # Logging
    log_level: str = Field(default="DEBUG", description="Log level (DEBUG/INFO/WARN/ERROR)")

    # Admin
    admin_ids: List[int] = Field(default=[], description="Telegram IDs of admins")

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, v):
        """Accept comma-separated '123,456' or JSON '[123,456]' or single int."""
        if isinstance(v, (list, tuple)):
            return [int(x) for x in v]
        if isinstance(v, int):
            return [v]
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            if v.startswith("["):
                import json
                return json.loads(v)
            # comma-separated: "123456789,987654321"
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        return v


settings = Settings()
