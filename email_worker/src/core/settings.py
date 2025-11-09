from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):  # type: ignore

    # Email settings
    EMAIL_IMAP_SERVER: str = "imap_server"
    EMAIL_IMAP_PORT: int = 993
    EMAIL_USERNAME: str = "username"
    EMAIL_PASSWORD: str = "password"
    EMAIL_FOLDER: str = "INBOX"
    TARGET_SENDER_EMAIL: str = "sender_email"
    EMAIL_CHECK_INTERVAL: int = 300  # seconds

    # RabbitMQ settings
    RABBIT_HOST: str = "rabbitmq"
    RABBIT_PORT: int = 5672
    RABBIT_USER: str = "admin"
    RABBIT_PASSWORD: str = "zxcvbn"
    RABBIT_VHOST: str = "/"
    RABBIT_EMAIL_QUEUE: str = "email_messages"
    RABBIT_EXCHANGE: str = "email_exchange"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOGGING_FILE_MAX_BYTES: int = 500_000

    BASE_DIR: str = str(Path(__file__).resolve().parent.parent)

    model_config = SettingsConfigDict(
        env_file=".env.mail", env_file_encoding="utf-8"
    )


settings = Settings()
