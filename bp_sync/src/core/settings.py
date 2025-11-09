from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):  # type: ignore
    PROJECT_NAME: str = "bp_sync"
    APP_RELOAD: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    POSTGRES_HOST: str = "127.0.0.1"
    POSTGRES_PORT: int = 5442
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "bp_sync"
    POSTGRES_DB_ECHO: bool = True
    SERVICE_USER: int = 1
    PROVIDER_B24: str = "B24"

    SECRET_KEY: str = "your-secret-key"
    ALGORITHM: str = "HS256"
    USER_ADMIN: str = "admin"
    PASS_ADMIN: str = "pass"
    TOKEN_EXPIRY_MINUTES: int = 60

    # BITRIX_LOGIN: str = ""
    # BITRIX_PASS: str = ""
    BITRIX_CLIENT_ID: str = ""
    BITRIX_CLIENT_SECRET: str = ""
    BITRIX_PORTAL: str = ""
    BITRIX_REDIRECT_URI: str = ""

    REDIS_HOST: str = ""
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""

    ENCRYPTION_KEY: str = (
        "your_fernet_key_here"  # сгенерировать Fernet.generate_key()
    )

    RABBIT_HOST: str = "rabbitmq"
    RABBIT_PORT: int = 5672
    RABBIT_USER: str = "admin"
    RABBIT_PASSWORD: str = "zxcvbn"
    RABBIT_VHOST: str = "/"
    RABBIT_EMAIL_QUEUE: str = "email_messages"
    RABBIT_EXCHANGE: str = "email_exchange"

    BASE_DIR: str = str(Path(__file__).resolve().parent.parent)
    LOGGING_FILE_MAX_BYTES: int = 500_000
    EXCHANGE_NAME: str = "sync"

    WEB_HOOK_PORTAL: str = ""
    WEB_HOOK_KEY: str = ""
    ENDPOINT_SEND_FAIL_INVOICE: str = ""
    ENDPOINT_SEND_DEAL_STATUS: str = ""

    WEB_HOOK_TEST: bool = True
    DEAL_ID_TEST: int = 1

    WEB_HOOK_TOKEN: str = "/rest/token/"
    WEB_HOOK_PRODUCT_UPDATE_TOKEN: str = "token"
    WEB_HOOK_DEAL_UPDATE_TOKEN: str = "token"
    WEB_HOOK_COMPANY_UPDATE_TOKEN: str = "company_update_token"
    WEB_HOOK_CONTACT_UPDATE_TOKEN: str = "contact_update_token"
    WEB_HOOK_USER_UPDATE_TOKEN: str = "user_update_token"
    WEB_HOOK_LEAD_UPDATE_TOKEN: str = "lead_update_token"
    WEB_HOOK_INVOICE_UPDATE_TOKEN: str = "invoice_update_token"
    MAX_AGE_WEBHOOK: int = 300  # seconds, 5 minutes
    CHAT_SUPERVISOR: int = 115
    TYPE_CHAT_SUPERVISOR: bool = False

    @property
    def dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8"
    )

    @property
    def web_hook_config(self) -> dict[str, Any]:
        return {
            "expected_tokens": {
                self.WEB_HOOK_DEAL_UPDATE_TOKEN: self.BITRIX_PORTAL.replace(
                    "https://", ""
                )
            },
            "allowed_events": [
                "ONCRMDEALUPDATE",
                "ONCRMDEALADD",
                "ONCRMDEALDELETE",
            ],
            "webhook_key": self.WEB_HOOK_KEY,
        }

    def web_hook_config_entity(
        self, token: str, events: set[str]
    ) -> dict[str, Any]:
        return {
            "expected_tokens": {
                token: self.BITRIX_PORTAL.replace("https://", "")
            },
            "allowed_events": events,
            "max_age": self.MAX_AGE_WEBHOOK,
        }

    @property
    def web_hook_config_company(self) -> dict[str, Any]:
        return self.web_hook_config_entity(
            self.WEB_HOOK_COMPANY_UPDATE_TOKEN,
            {"ONCRMCOMPANYUPDATE", "ONCRMCOMPANYADD", "ONCRMCOMPANYDELETE"},
        )

    @property
    def web_hook_config_contact(self) -> dict[str, Any]:
        return self.web_hook_config_entity(
            self.WEB_HOOK_CONTACT_UPDATE_TOKEN,
            {"ONCRMCONTACTUPDATE", "ONCRMCONTACTADD", "ONCRMCONTACTDELETE"},
        )

    @property
    def web_hook_config_user(self) -> dict[str, Any]:
        return self.web_hook_config_entity(
            self.WEB_HOOK_USER_UPDATE_TOKEN,
            {"ONUSERADD"},
        )

    @property
    def web_hook_config_lead(self) -> dict[str, Any]:
        return self.web_hook_config_entity(
            self.WEB_HOOK_LEAD_UPDATE_TOKEN,
            {"ONCRMLEADUPDATE", "ONCRMLEADADD", "ONCRMLEADDELETE"},
        )

    @property
    def web_hook_config_invoice(self) -> dict[str, Any]:
        return self.web_hook_config_entity(
            self.WEB_HOOK_INVOICE_UPDATE_TOKEN,
            {
                "ONCRMDYNAMICITEMUPDATE",
                "ONCRMINVOICEUPDATE",
                "ONCRMINVOICEADD",
                "ONCRMINVOICEDELETE",
            },
        )

    @property
    def web_hook_config_product(self) -> dict[str, Any]:
        return self.web_hook_config_entity(
            self.WEB_HOOK_PRODUCT_UPDATE_TOKEN,
            {
                "ONCRMPRODUCTUPDATE",
                "ONCRMPRODUCTADD",
            },
        )


settings = Settings()
