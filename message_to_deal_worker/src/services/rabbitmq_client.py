import json
from asyncio import Lock

import aio_pika
from aio_pika import ExchangeType
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
from services.message_handler import MessageHandler


class RabbitMQConsumer:
    def __init__(
        self,
        handler: MessageHandler,
        exchange_name: str | None = None,
        queue_name: str | None = None,
        max_retries: int | None = None,
        retry_delay: int | None = None,
    ):
        self.handler = handler
        self.connection: AbstractConnection | None = None
        self.channel: AbstractChannel | None = None
        self.exchange: AbstractExchange | None = None
        self.dlx_exchange: AbstractExchange | None = None
        self.delay_exchange: AbstractExchange | None = None
        self.queue: AbstractQueue | None = None
        self.delay_queue: AbstractQueue | None = None
        self.dlq: AbstractQueue | None = None

        self.exchange_name: str = exchange_name or settings.RABBIT_EXCHANGE
        self.queue_name: str = queue_name or settings.RABBIT_EMAIL_QUEUE
        self.max_retries: int = max_retries or settings.MAX_RETRIES
        self.retry_delay: int = retry_delay or settings.RETRY_DELAY_MS

        self._lock = Lock()
        self._is_shutting_down = False

    async def startup(self) -> bool:
        """Инициализирует подключение и объявляет RabbitMQ объекты.

        Returns:
            True если инициализация успешна, иначе False
        """
        if self._is_shutting_down:
            logger.warning("Попытка инициализации во время завершения работы")
            return False

        try:
            await self._initialize_connection()
            await self._initialize_channel()
            await self._initialize_exchanges()
            await self._initialize_queues()

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

        # Exchange для отложенных сообщений
        self.delay_exchange = await self.channel.declare_exchange(
            name="delay_exchange",
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

        if not self.delay_exchange:
            raise RuntimeError("Отложенный exchange не инициализирован")

        # Dead Letter Queue
        self.dlq = await self.channel.declare_queue(
            name="dead_letter_queue",
            durable=True,
        )
        await self.dlq.bind(self.dlx_exchange)

        # Очередь для отложенных сообщений
        self.delay_queue = await self.channel.declare_queue(
            name="delay_queue",
            durable=True,
            arguments={
                "x-message-ttl": self.retry_delay,
                "x-dead-letter-exchange": self.exchange.name,
                "x-dead-letter-routing-key": self.queue_name,
            },
        )
        await self.delay_queue.bind(self.delay_exchange, routing_key="delay")

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
                self.delay_exchange = None
                self.delay_queue = None
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

    async def consume(self) -> None:
        """Запускает потребление сообщений из очереди."""
        logger.info(
            f"Запуск потребления сообщений из очереди: {self.queue_name}"
        )
        if not self.queue:
            logger.error("Очередь не инициализирована")
            return

        try:
            async with self.queue.iterator() as queue_iter:
                async for message in queue_iter:
                    await self.process_message(message)

        except Exception as e:
            logger.error(f"Ошибка в цикле потребления сообщений: {e}")
            # Можно добавить логику переподключения

    async def process_message(self, message: AbstractIncomingMessage) -> None:
        """Обрабатывает одно сообщение из очереди.

        Args:
            message: Входящее сообщение
        """
        message_id = message.message_id or str(message.delivery_tag)
        retry_count = self._get_retry_count(message)

        try:
            logger.debug(
                f"Обработка сообщения: {message_id}, "
                f"попытка: {retry_count + 1}"
            )

            payload = json.loads(message.body.decode("utf-8"))
            payload["message_id"] = message_id

            if await self.handler.handle_message(payload):
                await message.ack()
                logger.info(f"Сообщение {message_id} успешно обработано")
            else:
                await self._handle_processing_failure(
                    message, retry_count, message_id
                )

        except json.JSONDecodeError as e:
            logger.error(f"Невалидный JSON в сообщении {message_id}: {e}")
            await message.nack(requeue=False)
        except Exception as e:
            logger.error(
                f"Неожиданная ошибка обработки сообщения {message_id}: {e}"
            )
            await self._handle_unexpected_error(
                message, retry_count, message_id
            )

    def _get_retry_count(self, message: AbstractIncomingMessage) -> int:
        """Получает счетчик попыток из заголовков сообщения.

        Args:
            message: Входящее сообщение

        Returns:
            Количество предыдущих попыток обработки
        """
        if not message.headers:
            return 0

        retry_count_value = message.headers.get("x-retry-count")

        # Безопасное преобразование различных типов в int
        if retry_count_value is None:
            return 0

        try:
            if isinstance(retry_count_value, (int, float)):
                return int(retry_count_value)
            elif isinstance(retry_count_value, (str, bytes)):
                # Для строковых значений пытаемся преобразовать в int
                return int(retry_count_value)
            else:
                # Для других типов (datetime, Decimal и т.д.) логируем и
                # возвращаем 0
                logger.warning(
                    f"Неподдерживаемый тип для retry_count: "
                    f"{type(retry_count_value)}. Значение: {retry_count_value}"
                )
                return 0
        except (ValueError, TypeError) as e:
            logger.warning(
                "Ошибка преобразования retry_count "
                f"'{retry_count_value}' в int: {e}"
            )
            return 0

    async def _handle_processing_failure(
        self,
        message: AbstractIncomingMessage,
        retry_count: int,
        message_id: str,
    ) -> None:
        """Обрабатывает неудачную обработку сообщения."""
        if retry_count < self.max_retries:
            await self._requeue_with_delay(message, retry_count + 1)
            logger.warning(
                f"Обработка сообщения {message_id} не удалась, "
                "запланирована повторная попытка "
                f"{retry_count + 1}/{self.max_retries}"
            )
        else:
            await message.nack(requeue=False)
            logger.error(
                f"Сообщение {message_id} превысило максимальное количество "
                f"попыток ({self.max_retries}), перемещено в DLQ"
            )

    async def _handle_unexpected_error(
        self,
        message: AbstractIncomingMessage,
        retry_count: int,
        message_id: str,
    ) -> None:
        """Обрабатывает неожиданные ошибки при обработке сообщения."""
        if retry_count < self.max_retries:
            await self._requeue_with_delay(message, retry_count + 1)
            logger.warning(
                f"Сообщение {message_id} завершилось с неожиданной ошибкой, "
                "запланирована повторная попытка "
                f"{retry_count + 1}/{self.max_retries}"
            )
        else:
            await message.nack(requeue=False)
            logger.error(
                f"Сообщение {message_id} превысило максимальное количество "
                f"попыток после неожиданной ошибки, перемещено в DLQ"
            )

    async def _requeue_with_delay(
        self,
        message: AbstractIncomingMessage,
        new_retry_count: int,
    ) -> None:
        """Повторно ставит сообщение в очередь с задержкой.

        Args:
            message: Сообщение для повторной обработки
            new_retry_count: Новое значение счетчика попыток
        """
        if not self.channel or not self.delay_exchange:
            logger.error(
                "Канал или exchange не доступны для повторной очереди"
            )
            await message.nack(requeue=False)
            return

        try:
            # Создаем новое сообщение с обновленными заголовками
            headers = message.headers.copy() if message.headers else {}
            headers["x-retry-count"] = new_retry_count

            # Публикуем сообщение в delay_exchange
            await self.delay_exchange.publish(
                aio_pika.Message(
                    body=message.body,
                    headers=headers,
                    delivery_mode=message.delivery_mode,
                    message_id=message.message_id,
                    correlation_id=message.correlation_id,
                ),
                routing_key="delay",
            )

            # Подтверждаем оригинальное сообщение
            await message.ack()
            logger.debug(
                f"Сообщение {message.message_id} поставлено в очередь "
                f"с задержкой {self.retry_delay}ms"
            )

        except Exception as e:
            logger.error(
                f"Не удалось поставить сообщение {message.message_id} "
                f"в очередь: {e}"
            )
            # Если не удалось поставить в очередь, отправляем в DLQ
            await message.nack(requeue=False)
