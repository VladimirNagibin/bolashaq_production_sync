import uuid
from asyncio import Lock
from http import HTTPStatus
from typing import Any

import aio_pika
from aio_pika import ExchangeType, Message
from aio_pika.abc import (
    AbstractChannel,
    AbstractConnection,
    AbstractExchange,
    AbstractIncomingMessage,
    AbstractQueue,
)
from aio_pika.exceptions import AMQPConnectionError, AMQPError

from core.logger import logger
from core.settings import settings

QUEUE_NAME = "fastapi_queue"


class RabbitMQClient:
    """Клиент для работы с RabbitMQ."""

    def __init__(self) -> None:
        self.connection: AbstractConnection | None = None
        self.channel: AbstractChannel | None = None
        self.exchange: AbstractExchange | None = None
        self.dlx_exchange: AbstractExchange | None = None
        self.queue: AbstractQueue | None = None
        self.dlq: AbstractQueue | None = None

        self.queue_name = QUEUE_NAME
        self._lock = Lock()
        self.unacked_messages: dict[str, AbstractIncomingMessage] = {}
        self._is_shutting_down = False

    async def startup(self) -> None:
        """Инициализация подключения и объявление RabbitMQ объектов."""

        if self._is_shutting_down:
            logger.warning("Попытка инициализации во время завершения работы")
            return

        try:
            await self._initialize_connection()
            await self._initialize_channel()
            await self._initialize_exchanges()
            await self._initialize_queues()

            async with self._lock:
                self.unacked_messages.clear()

            logger.info("RabbitMQ клиент успешно инициализирован")

        except AMQPConnectionError as e:
            logger.error(f"Ошибка подключения к RabbitMQ: {e}")
            raise
        except Exception as e:
            logger.error(f"Неожиданная ошибка при инициализации RabbitMQ: {e}")
            raise

    async def _initialize_connection(self) -> None:
        """Инициализация соединения с RabbitMQ."""
        connection_url = (
            f"amqp://{settings.RABBIT_USER}:{settings.RABBIT_PASSWORD}"
            f"@{settings.RABBIT_HOST}:{settings.RABBIT_PORT}/"
        )
        self.connection = await aio_pika.connect_robust(connection_url)

    async def _initialize_channel(self) -> None:
        """Инициализация канала и настройка QoS."""
        if not self.connection:
            raise RuntimeError("Соединение не установлено")

        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=1)

    async def _initialize_exchanges(self) -> None:
        """Инициализация exchanges."""
        if not self.channel:
            raise RuntimeError("Канал не инициализирован")

        # Основной exchange
        self.exchange = await self.channel.declare_exchange(
            name=settings.EXCHANGE_NAME,
            type=ExchangeType.DIRECT,
            durable=True,
        )

        # Dead Letter Exchange
        self.dlx_exchange = await self.channel.declare_exchange(
            name="dlx_exchange",
            type=ExchangeType.FANOUT,
            durable=True,
        )

    async def _initialize_queues(self) -> None:
        """Инициализация очередей."""
        if not self.channel:
            raise RuntimeError("Канал не инициализирован")

        if not self.dlx_exchange:
            raise RuntimeError("DLX exchange не инициализирован")

        if not self.exchange:
            raise RuntimeError("Основной exchange не инициализирован")

        # Dead Letter Queue
        self.dlq = await self.channel.declare_queue(
            name="dead_letter_queue",
            durable=True,
        )
        await self.dlq.bind(self.dlx_exchange)

        # Основная очередь с DLX политикой
        self.queue = await self.channel.declare_queue(
            name=self.queue_name,
            durable=True,
            arguments={
                "x-dead-letter-exchange": "dlx_exchange",
                # "x-message-ttl": 130000,  # 130 секунд до DLX
            },
        )
        await self.queue.bind(self.exchange, routing_key=self.queue_name)

    async def shutdown(self) -> None:
        """Корректное закрытие соединения."""
        self._is_shutting_down = True

        if self.connection:
            try:
                await self.connection.close()
                logger.info("Соединение с RabbitMQ закрыто")
            except AMQPError as e:
                logger.error(f"Ошибка при закрытии соединения: {e}")
            finally:
                self.connection = None
                self.channel = None
                self.exchange = None
                self.dlx_exchange = None
                self.queue = None
                self.dlq = None

    async def ensure_connection(self) -> None:
        """Гарантирует наличие активного соединения."""
        if (
            not self.connection
            or self.connection.is_closed
            or not self.channel
            or self.channel.is_closed
        ):

            logger.info("Восстановление соединения с RabbitMQ")
            await self.startup()

    async def send_message(
        self, message_body: bytes, message_type: str | None = None
    ) -> tuple[dict[str, Any], HTTPStatus]:
        """
        Отправка сообщения в RabbitMQ.

        Args:
            message_body: Тело сообщения в bytes
            message_type: Тип сообщения для логирования

        Returns:
            Кортеж с результатом операции и HTTP статусом
        """
        try:
            await self.ensure_connection()

            if not self.exchange:
                raise RuntimeError("Exchange не инициализирован")

            message_id = str(uuid.uuid4())
            message = Message(
                body=message_body,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                message_id=message_id,
                content_type="application/json",
                headers={"type": message_type} if message_type else None,
            )
            await self.exchange.publish(
                message=message,
                routing_key=self.queue_name,
            )

            log_context = f" ({message_type})" if message_type else ""
            logger.info(f"Отправлено сообщение{log_context}: {message_id}")
            return {"message_id": message_id}, HTTPStatus.CREATED

        except AMQPConnectionError as e:
            logger.error(f"Ошибка подключения при отправке сообщения: {e}")
            return (
                {"error": "Service unavailable"},
                HTTPStatus.SERVICE_UNAVAILABLE,
            )

        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения: {e}")
            return {"error": str(e)}, HTTPStatus.BAD_REQUEST

    async def get_message(
        self,
    ) -> aio_pika.abc.AbstractIncomingMessage | None:
        """
        Получение одного сообщения из очереди без подтверждения.

        Returns:
            Сообщение или None если очередь пуста или произошла ошибка
        """
        try:
            await self.ensure_connection()

            if not self.queue:
                raise RuntimeError("Очередь не инициализирована")

            message = await self.queue.get(fail=False, no_ack=False)

            if message:
                message_id = message.message_id or "unknown"
                logger.debug(f"Получено сообщение из очереди: {message_id}")

                # Сохраняем для возможного последующего подтверждения
                async with self._lock:
                    if message_id in self.unacked_messages:
                        logger.warning(
                            f"Дублирующееся сообщение: {message_id}"
                        )
                    self.unacked_messages[message_id] = message

            return message

        except Exception as e:
            logger.error(f"Ошибка при получении сообщения: {e}")
            return None

    async def ack_message(
        self, message: aio_pika.abc.AbstractIncomingMessage
    ) -> bool:
        """
        Подтверждение успешной обработки сообщения.

        Args:
            message: Сообщение для подтверждения

        Returns:
            True если подтверждение успешно, False в противном случае
        """
        message_id = message.message_id or "unknown"

        try:
            await message.ack()

            # Удаляем из отслеживаемых
            async with self._lock:
                self.unacked_messages.pop(message_id, None)

            logger.debug(f"Сообщение подтверждено: {message_id}")
            return True

        except Exception as e:
            logger.error(
                f"Ошибка при подтверждении сообщения {message_id}: {e}"
            )
            return False

    async def nack_message(
        self, message: AbstractIncomingMessage, requeue: bool = False
    ) -> bool:
        """
        Отклонение сообщения.

        Args:
            message: Сообщение для отклонения
            requeue: Нужно ли возвращать сообщение в очередь

        Returns:
            True если операция успешна, False в противном случае
        """
        message_id = message.message_id or "unknown"

        try:
            await message.nack(requeue=requeue)

            # Удаляем из отслеживаемых
            async with self._lock:
                self.unacked_messages.pop(message_id, None)

            action = "возвращено в очередь" if requeue else "отклонено"
            logger.debug(f"Сообщение {action}: {message_id}")
            return True

        except Exception as e:
            logger.error(f"Ошибка при отклонении сообщения {message_id}: {e}")
            return False

    @property
    def is_connected(self) -> bool:
        """Проверяет, активно ли соединение."""
        return (
            self.connection is not None
            and not self.connection.is_closed
            and self.channel is not None
            and not self.channel.is_closed
        )


_rabbitmq_instance: RabbitMQClient | None = None


def get_rabbitmq() -> RabbitMQClient:
    """Возвращает глобальный экземпляр клиента RabbitMQ (синглтон)."""
    global _rabbitmq_instance
    if _rabbitmq_instance is None:
        _rabbitmq_instance = RabbitMQClient()
    return _rabbitmq_instance


async def close_rabbitmq() -> None:
    """Закрывает глобальное соединение с RabbitMQ."""
    global _rabbitmq_instance
    if _rabbitmq_instance is not None:
        await _rabbitmq_instance.shutdown()
        _rabbitmq_instance = None
