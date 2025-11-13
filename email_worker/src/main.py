#!/usr/bin/env python3
"""
Email Worker Service - проверяет почту и отправляет сообщения в RabbitMQ

Этот сервис периодически проверяет почтовый ящик на наличие новых писем
от заданного отправителя, парсит их и отправляет содержимое в RabbitMQ.
"""

import asyncio
import signal
import sys
from typing import NoReturn

from core.logger import logger
from services.email_worker_service import EmailWorkerService


async def main() -> None:
    """
    Основная асинхронная функция приложения.

    Запускает и управляет жизненным циклом EmailWorkerService.
    Обеспечивает graceful shutdown при получении сигналов остановки.

    Raises:
        SystemExit: При возникновении критических ошибок
    """
    logger.info("Starting Email Worker Service...")
    service = EmailWorkerService()

    # Обработка сигналов для graceful shutdown
    def signal_handler(signum: int, frame: object | None) -> None:
        """
        Обработчик сигналов для корректного завершения работы.

        Args:
            signum: Номер сигнала (SIGINT, SIGTERM)
            frame: Текущий stack frame (не используется)
        """
        signal_name = signal.Signals(signum).name
        logger.info(
            f"Received signal {signal_name} ({signum}), initiating shutdown..."
        )
        service.stop()

    # Регистрация обработчиков сигналов
    try:
        signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
        signal.signal(signal.SIGTERM, signal_handler)  # Сигнал завершения
        logger.debug("Signal handlers registered for SIGINT and SIGTERM")
    except OSError as e:
        logger.error(f"Failed to register signal handlers: {e}")
        # Продолжаем работу, но graceful shutdown может не работать
        logger.warning("Graceful shutdown may not work properly")
    try:
        # Основной цикл выполнения сервиса
        logger.info("Starting main service loop...")
        await service.run()

    except KeyboardInterrupt:
        # Обработка явного прерывания пользователем (Ctrl+C)
        logger.info("Keyboard interrupt received, shutting down...")
        service.stop()

    except asyncio.CancelledError:
        # Обработка отмены асинхронных задач
        logger.info("Service task was cancelled")

    except Exception as error:
        # Обработка неожиданных ошибок
        logger.critical(
            f"Fatal error in main service loop: {error}",
            exc_info=True,  # Включаем полную трассировку стека
            extra={
                "error_type": type(error).__name__,
                "error_message": str(error),
            },
        )
        # Завершаем работу с ошибкой
        sys.exit(1)

    finally:
        # Всегда выполняем финальные операции
        logger.info("Performing final cleanup...")
        await _perform_final_cleanup(service)


async def _perform_final_cleanup(service: EmailWorkerService) -> None:
    """
    Выполняет финальные операции очистки перед завершением работы.

    Args:
        service: Экземпляр EmailWorkerService для очистки
    """
    try:
        # Дополнительная очистка ресурсов если нужно
        if hasattr(service, "cleanup"):
            await service.cleanup()
        logger.info("Cleanup completed successfully")
    except Exception as cleanup_error:
        logger.error(f"Error during cleanup: {cleanup_error}")


def check_environment() -> bool:
    """
    Проверяет необходимые переменные окружения и зависимости.

    Returns:
        True если все проверки пройдены, False в противном случае
    """
    try:
        # Проверка основных зависимостей
        import email  # noqa: F401
        import imaplib  # noqa: F401

        import aio_pika  # noqa: F401

        # Можно добавить проверки версий
        logger.debug("All dependencies are available")
        return True

    except ImportError as e:
        logger.critical(f"Missing dependency: {e}")
        return False


def run_application() -> NoReturn:
    """
    Основная точка входа приложения.

    Returns:
        NoReturn: Функция не возвращает управление
    """
    logger.info("Initializing Email Worker Service...")

    # Предварительные проверки
    if not check_environment():
        logger.critical("Environment check failed, exiting...")
        sys.exit(1)

    try:
        # Запуск основного асинхронного приложения
        asyncio.run(main())

    except KeyboardInterrupt:
        # Дополнительная обработка KeyboardInterrupt на верхнем уровне
        logger.info("Application terminated by user")

    except Exception as fatal_error:
        # Обработка любых непойманных исключений
        logger.critical(
            f"Unhandled fatal error: {fatal_error}",
            exc_info=True,
            extra={
                "error_type": type(fatal_error).__name__,
                "error_message": str(fatal_error),
            },
        )
        sys.exit(1)

    finally:
        # Финальное сообщение при завершении
        logger.info("Email Worker Service stopped")

    # Успешное завершение
    sys.exit(0)


if __name__ == "__main__":
    # Точка входа при запуске скрипта напрямую
    run_application()
