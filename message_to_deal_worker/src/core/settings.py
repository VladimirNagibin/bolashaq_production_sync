from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):  # type: ignore

    # RabbitMQ settings
    RABBIT_HOST: str = "rabbitmq"
    RABBIT_PORT: int = 5672
    RABBIT_USER: str = "admin"
    RABBIT_PASSWORD: str = "zxcvbn"
    RABBIT_VHOST: str = "/"
    RABBIT_EMAIL_QUEUE: str = "email_messages"
    RABBIT_EXCHANGE: str = "email_exchange"

    # API settings
    SITE_API_BASE_URL: str = "https://your-site.com/api"
    SITE_API_KEY: str | None = None

    # Logging
    LOG_LEVEL: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    LOGGING_FILE_MAX_BYTES: int = 500_000

    # Application
    BASE_DIR: str = str(Path(__file__).resolve().parent.parent)
    MAX_RETRIES: int = 3
    RETRY_DELAY_MS: int = 30000

    model_config = SettingsConfigDict(
        env_file=".env.mess", env_file_encoding="utf-8"
    )


settings = Settings()
