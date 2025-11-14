from typing import Any

from core.logger import logger
from schemas.message_schemas import MessageData

from .sender import Sender


class MessageHandler:
    """Основной обработчик сообщений из RabbitMQ."""

    def __init__(self, sender: Sender):
        """
        Args:
            sender: Сервис для отправки данных
        """
        self.sender = sender

    async def handle_message(self, message: dict[str, Any]) -> bool:
        """
        Обрабатывает входящее сообщение.

        Args:
            message: Словарь с данными сообщения

        Returns:
            True если сообщение успешно обработано, иначе False
        """
        try:
            logger.debug(
                f"Обработка сообщения: {message.get('message_id', 'unknown')}"
            )

            message_data = MessageData(**message)
            result = await self.sender.send_to_deal(message_data)

            if result:
                logger.info("Сообщение успешно обработано")
            else:
                logger.warning("Ошибка обработки сообщения")

            return result

        except Exception as e:
            logger.error(f"Критическая ошибка обработки сообщения: {e}")
            return False
