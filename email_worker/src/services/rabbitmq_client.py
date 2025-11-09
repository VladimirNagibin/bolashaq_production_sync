import json
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


class RabbitMQClient:
    def __init__(
        self,
        exchange_name: str | None = None,
        queue_name: str | None = None,
    ) -> None:
        self.connection: AbstractConnection | None = None
        self.channel: AbstractChannel | None = None
        self.exchange: AbstractExchange | None = None
        self.dlx_exchange: AbstractExchange | None = None
        self.queue: AbstractQueue | None = None
        self.dlq: AbstractQueue | None = None
        self.exchange_name: str = exchange_name or settings.RABBIT_EXCHANGE
        self.queue_name: str = queue_name or settings.RABBIT_EMAIL_QUEUE
        self._lock = Lock()
        self.unacked_messages: dict[str, AbstractIncomingMessage] = {}
        self._is_shutting_down = False

    async def startup(self) -> bool:
        """Инициализация подключения и объявление RabbitMQ объектов."""

        if self._is_shutting_down:
            logger.warning("Попытка инициализации во время завершения работы")
            return False

        try:
            await self._initialize_connection()
            await self._initialize_channel()
            await self._initialize_exchanges()
            await self._initialize_queues()

            async with self._lock:
                self.unacked_messages.clear()

            logger.info("RabbitMQ клиент успешно инициализирован")
            return True
        except AMQPConnectionError as e:
            logger.error(f"Ошибка подключения к RabbitMQ: {e}")
            return False
        except Exception as e:
            logger.error(f"Неожиданная ошибка при инициализации RabbitMQ: {e}")
            return False

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
            name=self.exchange_name,
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

    async def send_email_message(
        self, email_data: dict[str, Any]
    ) -> tuple[dict[str, Any], HTTPStatus]:
        """Отправляет сообщение о письме в RabbitMQ"""
        try:
            await self.ensure_connection()

            if not self.exchange:
                raise RuntimeError("Exchange не инициализирован")

            message_body = json.dumps(
                email_data, default=str, ensure_ascii=False
            )
            message_id = str(uuid.uuid4())
            message = Message(
                body=message_body.encode("utf-8"),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                message_id=message_id,
            )

            if not self.exchange:
                raise RuntimeError("Exchange не инициализирован")

            await self.exchange.publish(
                message=message,
                routing_key=self.queue_name,
            )

            logger.debug(
                "Email message sent to RabbitMQ: "
                f"{email_data.get('message_id')}"
            )
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
