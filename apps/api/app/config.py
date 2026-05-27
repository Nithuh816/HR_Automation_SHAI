from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: Literal["development", "staging", "production"] = "development"
    app_secret_key: str = "dev-secret-change-me"
    pii_enc_key: str = ""
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg://hr:hr_dev_password@localhost:5432/hr_automation"

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    storage_backend: Literal["local", "minio", "r2", "s3"] = "local"
    storage_bucket: str = "hr-documents"
    s3_endpoint_url: str = "http://localhost:9000"
    s3_region: str = "auto"
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_presign_ttl_seconds: int = 300

    ms_tenant_id: str = ""
    ms_client_id: str = ""
    ms_client_secret: str = ""
    ms_redirect_uri: str = "http://localhost:5173/auth/callback"
    ms_scopes: str = "openid profile email User.Read"

    greythr_base_url: str = ""
    greythr_api_key: str = ""
    greythr_tenant: str = ""

    whatsapp_phone_number_id: str = ""
    whatsapp_business_account_id: str = ""
    whatsapp_access_token: str = ""
    whatsapp_verify_token: str = ""

    email_provider: Literal["smtp", "resend"] = "smtp"
    email_from: str = "hr-noreply@shaihealth.example"
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = False
    resend_api_key: str = ""

    magic_link_hmac_key: str = "dev-magic-key-change-me"
    magic_link_base_url: str = "http://localhost:5173/c"

    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
