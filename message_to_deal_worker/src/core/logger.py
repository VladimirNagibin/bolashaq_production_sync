import logging as log
import os
from logging import config
from logging.handlers import RotatingFileHandler
from typing import Any

from core.settings import settings


def create_directory(path: str) -> None:
    """Создает директорию, если она не существует.

    Args:
        path: Путь к директории
    """
    if not os.path.exists(path):
        os.makedirs(path)


# Создаем директорию для логов
create_directory(os.path.join(settings.BASE_DIR, "logs"))

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DEFAULT_HANDLERS = ("console",)

LOGGING: dict[str, Any] = {  # noqa: WPS407
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": LOG_FORMAT},
        "default": {
            "fmt": "%(levelprefix)s %(message)s",
            "use_colors": None,
        },
    },
    "handlers": {  # noqa: WPS226
        "console": {
            "level": "DEBUG",  # noqa: WPS226
            "class": "logging.StreamHandler",
            "formatter": "verbose",  # noqa: WPS226
        },
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(settings.BASE_DIR, "logs", "app.log"),
            "maxBytes": settings.LOGGING_FILE_MAX_BYTES,
            "backupCount": 5,
            "encoding": "utf-8",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "": {
            "handlers": LOG_DEFAULT_HANDLERS,
            "level": "INFO",  # noqa: WPS226
        },
        "email_worker": {
            "handlers": ["console", "file"],
            "level": settings.LOG_LEVEL,
            "propagate": False,
        },
    },
    "root": {
        "level": "INFO",
        "formatter": "verbose",
        "handlers": LOG_DEFAULT_HANDLERS,
    },
}

config.dictConfig(LOGGING)
logger = log.getLogger("email_worker")

logger.setLevel(settings.LOG_LEVEL)
formatter = log.Formatter(fmt=LOG_FORMAT)
file_handler = RotatingFileHandler(
    os.path.join(settings.BASE_DIR, "logs", "log.log"),
    maxBytes=settings.LOGGING_FILE_MAX_BYTES,
    backupCount=5,
    encoding="utf-8",
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
