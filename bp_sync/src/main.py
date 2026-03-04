import sys
from contextlib import asynccontextmanager
from typing import AsyncIterator

import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, ORJSONResponse
from sqladmin import Admin

from admin.admin_models import register_models
from admin.authenticate import BasicAuthBackend
from api.v1.b24.b24_router import b24_router
from api.v1.health_checker import health_router
from api.v1.schemas.response_schemas import ErrorResponse
from api.v1.suppliers.suppliers_router import suppliers_router
from api.v1.test import test_router
from core.logger import LOGGING, logger
from core.settings import settings
from db.postgres import engine
from db.redis import close_redis, init_redis
from services.dependencies.dependencies_bitrix import (
    initialize_container,
    shutdown_container,
)
from services.exceptions import BaseAppException
from services.leads.lead_services_factory import LeadServiceFactory
from services.rabbitmq_client import get_rabbitmq

SCHEDULER_JOB_ID = "daily_overdue_leads_notification"
TIME_TASK = (4, 0)


async def _init_rabbitmq() -> None:
    """Инициализация клиента RabbitMQ."""
    try:
        rabbitmq_client = get_rabbitmq()
        await rabbitmq_client.startup()
        logger.info("RabbitMQ client initialized successfully.")
    except Exception as e:
        logger.exception("Failed to initialize RabbitMQ client: %s", e)
        raise


async def _shutdown_rabbitmq() -> None:
    """Корректное завершение работы клиента RabbitMQ."""
    try:
        rabbitmq_client = get_rabbitmq()
        await rabbitmq_client.shutdown()
        logger.info("RabbitMQ client shutdown successfully.")
    except Exception as e:
        logger.exception("Error during RabbitMQ shutdown: %s", e)


def _configure_scheduler(
    scheduler: AsyncIOScheduler, lead_service: LeadServiceFactory
) -> None:
    """Настройка задач планировщика."""
    scheduler.add_job(
        lead_service.send_overdue_leads_notifications,
        trigger="cron",
        hour=TIME_TASK[0],
        minute=TIME_TASK[1],
        id=SCHEDULER_JOB_ID,
        replace_existing=True,
    )
    logger.info("Scheduler job '%s' added.", SCHEDULER_JOB_ID)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Управление жизненным циклом приложения (запуск и остановка)."""
    logger.info("Application startup initiated...")

    # Инициализация ресурсов
    try:
        await init_redis()
        await _init_rabbitmq()
        await initialize_container()

        # Инициализация сервисов
        lead_service = LeadServiceFactory()
        await lead_service.initialize()

        # Настройка и запуск планировщика
        scheduler = AsyncIOScheduler()
        _configure_scheduler(scheduler, lead_service)
        scheduler.start()
        logger.info("Scheduler started.")

    except Exception as e:
        logger.critical("Fatal error during startup: %s", e)
        # Если произошла ошибка при старте, завершаем работу
        sys.exit(1)

    yield  # Приложение работает

    # Завершение работы
    logger.info("Application shutdown initiated...")

    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped.")

    await lead_service.cleanup()
    await shutdown_container()
    await _shutdown_rabbitmq()
    await close_redis()

    logger.info("Application shutdown complete.")


def setup_routes(app: FastAPI) -> None:
    """Регистрация маршрутов API."""
    app.include_router(b24_router, prefix="/api/v1/b24", tags=["b24"])
    app.include_router(test_router, prefix="/api/v1/test", tags=["test"])
    app.include_router(health_router, prefix="/api/v1", tags=["health"])
    app.include_router(
        suppliers_router, prefix="/api/v1/suppliers", tags=["suppliers"]
    )


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
    logger.info("Admin panel configured.")


def register_exception_handler(app: FastAPI) -> None:
    """
    Регистрирует глобальные обработчики исключений для приложения.
    """

    @app.exception_handler(BaseAppException)  # type: ignore[misc]
    async def app_exception_handler(  # type: ignore
        request: Request, exc: BaseAppException
    ):
        """Обработчик для бизнес-исключений приложения."""
        logger.warning(
            "Business exception occurred: %s (code: %s)",
            exc.message,
            exc.error_code,
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                error_code=exc.error_code, message=exc.message
            ).model_dump(mode="json"),
        )

    @app.exception_handler(Exception)  # type: ignore[misc]
    async def generic_exception_handler(  # type: ignore
        request: Request, exc: Exception
    ):
        """Обработчик для неперехваченных исключений."""
        logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal Server Error"},
        )


def create_app() -> FastAPI:
    """Фабрика для создания экземпляра приложения FastAPI."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        docs_url="/api/openapi",
        openapi_url="/api/openapi.json",
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    setup_routes(app)
    setup_admin_panel(app)
    register_exception_handler(app)

    return app


def start_server() -> None:
    """Точка входа для запуска Uvicorn сервера."""
    logger.info(
        "Starting server on %s:%s", settings.APP_HOST, settings.APP_PORT
    )
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
