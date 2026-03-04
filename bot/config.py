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
    webapp_allowed_origins: List[str] = Field(
        default=[],
        description="Allowed CORS origins for admin webapp (comma-separated or JSON array)",
    )
    webapp_auth_mode: str = Field(
        default="telegram_strict",
        description="WebApp auth mode: telegram_strict (safe default) or test_bypass (tests only)",
    )
    webapp_init_data_ttl_seconds: int = Field(
        default=600,
        description="Max age for Telegram initData auth_date in seconds",
    )
    webapp_enable_hsts: bool = Field(
        default=False,
        description="Enable Strict-Transport-Security header for HTTPS deployments",
    )
    webapp_csp: str = Field(
        default="default-src 'self'; script-src 'self' https://telegram.org https://*.telegram.org; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' https:; frame-ancestors 'self' https://web.telegram.org https://*.telegram.org; base-uri 'self'; form-action 'self'",
        description="Content-Security-Policy header value for admin webapp",
    )
    webapp_rate_limit_window_seconds: int = Field(
        default=60,
        description="Time window for sensitive API rate limit",
    )
    webapp_rate_limit_sensitive_per_window: int = Field(
        default=20,
        description="Max requests per sensitive endpoint within window",
    )
    webapp_max_request_bytes: int = Field(
        default=2_097_152,
        description="Maximum allowed request size for non-upload routes",
    )

    # S3 Storage
    s3_endpoint_url: str = Field(default="http://localhost:9000", description="S3 Endpoint URL (MinIO usually)")
    s3_access_key: str = Field(default="minioadmin", description="S3 Access Key")
    s3_secret_key: str = Field(default="minioadmin", description="S3 Secret Key")
    s3_bucket_name: str = Field(default="mathtrainer", description="S3 Bucket Name")
    s3_public_url: str = Field(default="http://localhost:9000", description="Public URL for presigned links if endpoint is internal")

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

    @field_validator("webapp_allowed_origins", mode="before")
    @classmethod
    def parse_webapp_allowed_origins(cls, v):
        if isinstance(v, (list, tuple)):
            return [str(x).strip() for x in v if str(x).strip()]
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            if v.startswith("["):
                import json
                parsed = json.loads(v)
                return [str(x).strip() for x in parsed if str(x).strip()]
            return [x.strip() for x in v.split(",") if x.strip()]
        return v


settings = Settings()
