from contextlib import asynccontextmanager
from typing import AsyncIterator

import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from sqladmin import Admin

from admin.admin_models import register_models
from admin.authenticate import BasicAuthBackend
from api.v1.b24.b24_router import b24_router
from api.v1.health_checker import healht_router
from api.v1.test import test_router
from core.logger import LOGGING, logger
from core.settings import settings
from db.postgres import engine
from db.redis import close_redis, init_redis
from services.dependencies_bitrix import (
    initialize_container,
    shutdown_container,
)
from services.rabbitmq_client import get_rabbitmq


async def _init_rabbitmq() -> None:
    rabbitmq_client = get_rabbitmq()
    await rabbitmq_client.startup()


async def _shutdown_rabbitmq() -> None:
    rabbitmq_client = get_rabbitmq()
    await rabbitmq_client.shutdown()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await init_redis()
    await _init_rabbitmq()
    await initialize_container()
    yield
    await close_redis()
    await _shutdown_rabbitmq()
    await shutdown_container()


def setup_routes(app: FastAPI) -> None:
    """Настройка маршрутов приложения."""
    app.include_router(b24_router, prefix="/api/v1/b24", tags=["b24"])
    app.include_router(test_router, prefix="/api/v1/test", tags=["test"])
    app.include_router(healht_router, prefix="/api/v1", tags=["health"])


def setup_admin_panel(app: FastAPI) -> None:
    """Настройка админ-панели."""
    auth_backend = BasicAuthBackend()
    admin = Admin(
        app,
        engine,
        title="Админка",
        templates_dir="templates/admin",
        authentication_backend=auth_backend,
    )
    register_models(admin)


def create_app() -> FastAPI:
    """Фабрика для создания приложения."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        docs_url="/api/openapi",
        openapi_url="/api/openapi.json",
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    setup_routes(app)
    setup_admin_panel(app)

    return app


def start_server() -> None:
    logger.info("Start bp_sync.")
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        log_config=LOGGING,
        log_level=settings.LOG_LEVEL.lower(),
        reload=settings.APP_RELOAD,
    )


app = create_app()


if __name__ == "__main__":
    start_server()
