import asyncio
import os

import uvicorn

from core.logger import logger
from core.settings import settings
from services.api_server import api_server
from services.document_approval_bot import DocumentApprovalBot


async def main() -> None:
    """Основная функция запуска"""
    # Создаем папку для загрузок если нужно
    if hasattr(settings, "UPLOAD_FOLDER"):
        os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)

    # Запускаем бота
    bot = DocumentApprovalBot()

    # Запускаем в асинхронном режиме
    await bot.application.initialize()
    await bot.application.start()
    await bot.application.updater.start_polling()

    logger.info(
        "Бот запущен. API доступен на "
        f"http://{settings.APP_HOST}:{settings.APP_PORT}"
    )

    # Запускаем API сервер в отдельной задаче
    import threading

    api_thread = threading.Thread(
        target=lambda: uvicorn.run(
            api_server.app,
            host=settings.APP_HOST,
            port=settings.APP_PORT,
            log_level=settings.LOG_LEVEL.lower(),
        ),
        daemon=True,
    )
    api_thread.start()

    try:
        # Ждем остановки
        await bot.application.updater.idle()
    except KeyboardInterrupt:
        logger.info("Остановка бота...")
    finally:
        await bot.application.stop()


if __name__ == "__main__":
    asyncio.run(main())
