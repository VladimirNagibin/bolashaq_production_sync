from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):  # type: ignore
    PROJECT_NAME: str = "quick_sign_bot"
    APP_RELOAD: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    REDIS_HOST: str = ""
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""

    # API settings
    SITE_API_BASE_URL: str = "https://your-site.com/api"
    SITE_API_KEY: str | None = None

    API_SECRET_KEY: str = "secret_key"

    BASE_DIR: str = str(Path(__file__).resolve().parent.parent)
    LOGGING_FILE_MAX_BYTES: int = 500_000

    # Токен бота из @BotFather
    BOT_TOKEN: str = "bot_token"

    # ID согласующего пользователя
    APPROVER_ID: int = 123

    # ID администратора
    ADMIN_ID: int = 0

    # Настройки файлов
    MAX_FILE_SIZE: int = 52428800  # 50 MB
    ALLOWED_EXTENSIONS: list[str] = [
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".jpg",
        ".jpeg",
        ".png",
        ".txt",
        ".csv",
    ]

    # Время ожидания ответа (секунды)
    TIMEOUT_SECONDS: int = 300

    # Путь для сохранения файлов локально
    UPLOAD_FOLDER: str = "uploads"

    MAX_RETRIES: int = 3
    RETRY_DELAY_SECONDS: int = 300000

    model_config = SettingsConfigDict(
        env_file=".env.sign_bot", env_file_encoding="utf-8"
    )


settings = Settings()
