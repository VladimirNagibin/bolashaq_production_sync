import logging as log
import os
from logging import config
from logging.handlers import RotatingFileHandler
from typing import Any

from core.settings import settings


def create_directory(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path)


create_directory(os.path.join(settings.BASE_DIR, "logs"))

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DEFAULT_HANDLERS = ("console",)
LOGGING: dict[str, Any] = {  # noqa: WPS407
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": LOG_FORMAT},
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(message)s",
            "use_colors": None,
        },
        "access": {  # noqa: WPS226
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": (
                "%(levelprefix)s %(client_addr)s - '%(request_line)s' "
                "%(status_code)s"
            ),
        },
    },
    "handlers": {  # noqa: WPS226
        "console": {
            "level": "DEBUG",  # noqa: WPS226
            "class": "logging.StreamHandler",
            "formatter": "verbose",  # noqa: WPS226
        },
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "": {
            "handlers": LOG_DEFAULT_HANDLERS,
            "level": "INFO",  # noqa: WPS226
        },
        "uvicorn.error": {
            "level": "INFO",
        },
        "uvicorn.access": {
            "handlers": ["access"],
            "level": "INFO",
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
