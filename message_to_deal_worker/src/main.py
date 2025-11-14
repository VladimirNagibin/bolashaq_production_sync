import asyncio
import signal
import sys
from types import FrameType

from core.logger import logger
from services.message_handler import MessageHandler
from services.rabbitmq_client import RabbitMQConsumer
from services.sender import Sender


class Application:
    """Основной класс приложения."""

    def __init__(self) -> None:
        self.consumer: RabbitMQConsumer | None = None
        self._is_shutting_down = False

    async def setup(self) -> bool:
        """Инициализирует приложение.

        Returns:
            True если инициализация успешна, иначе False
        """
        try:
            sender = Sender()
            handler = MessageHandler(sender)
            self.consumer = RabbitMQConsumer(handler)

            if not await self.consumer.startup():
                logger.error("Не удалось инициализировать RabbitMQ клиент")
                return False

            logger.info("Приложение успешно инициализировано")
            return True

        except Exception as e:
            logger.error(f"Ошибка инициализации приложения: {e}")
            return False

    async def run(self) -> None:
        """Запускает основную логику приложения."""
        if not self.consumer:
            logger.error("Consumer не инициализирован")
            return

        try:
            logger.info("Запуск обработки сообщений")
            await self.consumer.consume()
        except Exception as e:
            logger.error(f"Ошибка в основном цикле приложения: {e}")
        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        """Корректно завершает работу приложения."""
        if self._is_shutting_down:
            return

        self._is_shutting_down = True
        logger.info("Завершение работы приложения...")

        if self.consumer:
            await self.consumer.shutdown()

        logger.info("Приложение завершило работу")

    def setup_signal_handlers(self) -> None:
        """Устанавливает обработчики сигналов для graceful shutdown."""
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, self._signal_handler)

    def _signal_handler(self, signum: int, frame: FrameType | None) -> None:
        """Обработчик сигналов завершения."""
        logger.info(f"Получен сигнал {signum}, инициируется завершение...")
        asyncio.create_task(self.shutdown())


async def main() -> None:
    """Точка входа в приложение."""
    app = Application()
    app.setup_signal_handlers()

    if not await app.setup():
        logger.error("Не удалось запустить приложение")
        sys.exit(1)

    await app.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Приложение остановлено пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка приложения: {e}")
        sys.exit(1)
