import asyncio
from datetime import datetime
from typing import Any

from core.logger import logger
from core.settings import settings

from .email_client import EmailClient
from .rabbitmq_client import RabbitMQClient


class EmailWorkerService:
    def __init__(self) -> None:
        self.email_client = EmailClient()
        self.rabbitmq_client = RabbitMQClient()
        self.is_running = False
        self.processed_count = 0
        self.error_count = 0

    async def initialize(self) -> None:
        """Инициализирует сервис"""
        logger.info("Initializing Email Worker Service...")

        # Подключаемся к почте
        if not self.email_client.connect():
            raise RuntimeError("Failed to connect to email server")

        # Подключаемся к RabbitMQ
        if not await self.rabbitmq_client.startup():
            raise RuntimeError("Failed to connect to RabbitMQ")

        logger.info("Email Worker Service initialized successfully")

    async def process_email(self, email_msg: Any) -> bool:
        """Обрабатывает одно email сообщение"""
        try:
            # Подготавливаем данные для отправки
            message_data: dict[str, Any] = {
                "type": "email_message",
                "email": email_msg.dict(),
                "processed_at": datetime.now().isoformat(),
                "source": "email_worker_service",
            }

            # Отправляем в RabbitMQ
            success = await self.rabbitmq_client.send_email_message(
                message_data
            )

            if success:
                # Помечаем письмо как прочитанное
                self.email_client.mark_as_read(email_msg.message_id)

                self.processed_count += 1
                logger.info(
                    "Email processed and sent to RabbitMQ: "
                    f"{email_msg.subject}",
                    extra={
                        "message_id": email_msg.message_id,
                        "subject": (
                            email_msg.subject[:50] + "..."
                            if len(email_msg.subject) > 50
                            else email_msg.subject
                        ),
                        "sender": email_msg.sender,
                    },
                )
                return True
            else:
                self.error_count += 1
                logger.error(
                    f"Failed to send email to RabbitMQ: {email_msg.message_id}"
                )
                return False

        except Exception as e:
            self.error_count += 1
            logger.error(f"Error processing email {email_msg.message_id}: {e}")
            return False

    async def check_emails(self) -> None:
        """Проверяет и обрабатывает новые письма"""
        try:
            logger.debug("Checking for new emails...")

            # Получаем новые письма
            new_emails = self.email_client.get_new_emails(
                since_minutes=settings.EMAIL_CHECK_INTERVAL // 60
            )

            if not new_emails:
                logger.debug("No new emails found")
                return

            logger.info(f"Found {len(new_emails)} new emails to process")

            # Обрабатываем каждое письмо
            processed_count = 0
            for email_msg in new_emails:
                if await self.process_email(email_msg):
                    processed_count += 1

            logger.info(
                f"Successfully processed {processed_count} out of "
                f"{len(new_emails)} emails"
            )

        except Exception as e:
            logger.error(f"Error in email check cycle: {e}")

    async def run(self) -> None:
        """Запускает основной цикл работы сервиса"""
        self.is_running = True
        logger.info("Email Worker Service started")

        try:
            await self.initialize()

            # Основной цикл
            while self.is_running:
                try:
                    await self.check_emails()
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")

                # Ждем перед следующей проверкой
                logger.debug(
                    f"Waiting {settings.EMAIL_CHECK_INTERVAL} "
                    "seconds before next check..."
                )
                await asyncio.sleep(settings.EMAIL_CHECK_INTERVAL)

        except asyncio.CancelledError:
            logger.info("Email worker cancelled")
        except Exception as e:
            logger.error(f"Email worker stopped with error: {e}")
        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        """Корректное завершение работы сервиса"""
        self.is_running = False
        logger.info("Shutting down Email Worker Service...")

        self.email_client.disconnect()
        await self.rabbitmq_client.shutdown()

        logger.info(
            f"Service statistics: {self.processed_count} processed, "
            f"{self.error_count} errors"
        )
        logger.info("Email Worker Service stopped")

    def stop(self) -> None:
        """Останавливает сервис"""
        logger.info("Received stop signal")
        self.is_running = False
