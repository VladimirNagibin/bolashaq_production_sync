import email
import imaplib
import logging
from datetime import datetime, timedelta
from email.header import decode_header
from email.message import Message
from email.utils import parsedate_to_datetime
from typing import Any, cast

from core.settings import settings
from schemas.email_schemas import EmailMessage

logger = logging.getLogger(__name__)


class EmailClient:
    def __init__(self) -> None:
        self.connection: imaplib.IMAP4_SSL | None = None

    def connect(self) -> bool:
        """Устанавливает соединение с IMAP сервером"""
        try:
            logger.info(
                "Connecting to "
                f"{settings.EMAIL_IMAP_SERVER}:{settings.EMAIL_IMAP_PORT}"
            )
            self.connection = imaplib.IMAP4_SSL(
                settings.EMAIL_IMAP_SERVER, settings.EMAIL_IMAP_PORT
            )
            self.connection.login(
                settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD
            )
            self.connection.select(settings.EMAIL_FOLDER)
            logger.info("Successfully connected to email server")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to email server: {e}")
            return False

    def disconnect(self) -> None:
        """Закрывает соединение с IMAP сервером"""
        if self.connection:
            try:
                self.connection.close()
                self.connection.logout()
                logger.info("Disconnected from email server")
            except Exception as e:
                logger.warning(f"Error disconnecting from email server: {e}")
            finally:
                self.connection = None

    def _decode_header(self, header: str) -> str:
        """Декодирует email заголовки"""
        try:
            if not header:
                return ""

            decoded_parts = decode_header(header)
            decoded_header = ""
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        decoded_header += part.decode(encoding)
                    else:
                        decoded_header += part.decode("utf-8", errors="ignore")
                else:
                    decoded_header += part
            return decoded_header
        except Exception as e:
            logger.warning(f"Error decoding header '{header}': {e}")
            return str(header)

    def _parse_email(
        self,
        msg: Message,
        message_id: str,
    ) -> EmailMessage | None:
        """Парсит email сообщение"""
        try:
            # Получаем основные заголовки
            subject = self._decode_header(msg.get("Subject", ""))
            sender = self._decode_header(msg.get("From", ""))
            recipient = self._decode_header(msg.get("To", ""))

            # Извлекаем все заголовки
            headers: dict[str, Any] = {}
            for key, value in msg.items():
                headers[key] = self._decode_header(value)

            # Парсим дату
            date_str = msg.get("Date", "")
            try:
                received_date = parsedate_to_datetime(date_str)
            except Exception:
                received_date = datetime.now()

            # Извлекаем текст письма
            body = ""
            attachments_count = 0

            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(
                        part.get("Content-Disposition", "")
                    )

                    # Считаем вложения
                    if "attachment" in content_disposition:
                        attachments_count += 1
                        continue

                    # Извлекаем текстовое содержимое
                    if (
                        content_type == "text/plain"
                        and "attachment" not in content_disposition
                    ):
                        try:
                            payload = part.get_payload(decode=True)
                            if payload:
                                payload_bytes = cast(bytes, payload)
                                body = payload_bytes.decode(
                                    "utf-8", errors="ignore"
                                )
                                break
                        except Exception as e:
                            logger.warning(f"Error decoding text part: {e}")
                            continue
            else:
                # Простое текстовое письмо
                if msg.get_content_type() == "text/plain":
                    try:
                        payload = msg.get_payload(decode=True)
                        if payload:
                            payload_bytes = cast(bytes, payload)
                            body = payload_bytes.decode(
                                "utf-8", errors="ignore"
                            )
                    except Exception as e:
                        logger.warning(f"Error decoding simple email: {e}")

            return EmailMessage(
                message_id=(
                    message_id.decode()
                    if isinstance(message_id, bytes)
                    else str(message_id)
                ),
                subject=subject,
                body=body.strip(),
                sender=sender,
                recipient=recipient,
                received_date=received_date,
                attachments_count=attachments_count,
                headers=headers,
            )
        except Exception as e:
            logger.error(f"Error parsing email {message_id}: {e}")
            return None

    def get_new_emails(self, since_minutes: int = 60) -> list[EmailMessage]:
        """
        Получает новые письма от целевого отправителя
        """
        if not self.connection or self.connection.state != "SELECTED":
            if not self.connect():
                logger.error("Failed to connect to email server")
                return []

        emails: list[EmailMessage] = []
        try:
            # Поиск непрочитанных писем от целевого отправителя
            since_time = (
                datetime.now() - timedelta(minutes=since_minutes)
            ).strftime("%d-%b-%Y")
            search_criteria = (
                f'(UNSEEN SINCE "{since_time}" FROM '
                f'"{settings.TARGET_SENDER_EMAIL}")'
            )

            logger.debug(f"Searching emails with criteria: {search_criteria}")
            if self.connection is None:
                logger.error("Email connection is None")
                return []
            status, messages = self.connection.search(None, search_criteria)

            if status != "OK":
                logger.warning("No emails found matching criteria")
                return []

            message_ids = messages[0].split()
            logger.info(
                f"Found {len(message_ids)} new emails from target sender"
            )

            for msg_id in message_ids:
                try:
                    status, msg_data = self.connection.fetch(
                        msg_id, "(RFC822)"
                    )
                    if status != "OK":
                        logger.warning(f"Failed to fetch email {msg_id}")
                        continue

                    # email_body = msg_data[0][1]
                    email_body = self._safe_extract_email_body(
                        msg_data, msg_id
                    )
                    if email_body is None:
                        continue
                    msg = email.message_from_bytes(email_body)

                    parsed_email = self._parse_email(msg, msg_id)
                    if parsed_email:
                        emails.append(parsed_email)
                        logger.debug(
                            "Successfully parsed email: "
                            f"{parsed_email.subject}"
                        )

                except Exception as e:
                    logger.error(f"Error processing email {msg_id}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error fetching emails: {e}")

        return emails

    def _safe_extract_email_body(
        self, msg_data: Any, msg_id: str | bytes
    ) -> bytes | None:
        """
        Безопасно извлекает тело письма из IMAP ответа
        """
        try:
            # Безопасное преобразование msg_id в строку для логирования
            msg_id_str = self._safe_message_id_to_str(msg_id)

            # Проверяем что msg_data не None и не пустой
            if not msg_data:
                logger.warning(f"Empty msg_data for email {msg_id_str}")
                return None

            # Проверяем что есть хотя бы один элемент
            if len(msg_data) == 0:
                logger.warning(f"Empty msg_data list for email {msg_id_str}")
                return None

            # Проверяем что это список и есть хотя бы один элемент
            if not isinstance(msg_data, list):
                logger.warning(
                    "Invalid msg_data format for email "
                    f"{msg_id_str}: {type(msg_data)}"
                )
                return None

            first_item = msg_data[0]

            # Проверяем что первый элемент не None
            if first_item is None:
                logger.warning(
                    f"First item of msg_data is None for email {msg_id_str}"
                )
                return None

            # Обрабатываем разные форматы ответа IMAP
            if isinstance(first_item, tuple):
                # Формат: [(b'RFC822 data', b'email body data')]
                if len(first_item) >= 2 and first_item[1] is not None:
                    return first_item[1]  # type: ignore[no-any-return]
                else:
                    logger.warning(
                        "Invalid tuple structure in msg_data for email "
                        f"{msg_id_str}"
                    )
                    return None
            elif isinstance(first_item, bytes):
                # Формат: [b'email body data']
                return first_item
            else:
                logger.warning(
                    "Unexpected msg_data format for email "
                    f"{msg_id_str}: {type(first_item)}"
                )
                return None

        except Exception as e:
            logger.error(f"Error extracting email body for {msg_id_str}: {e}")
            return None

    def _safe_message_id_to_str(self, msg_id: str | bytes) -> str:
        """
        Безопасно преобразует message_id в строку для логирования

        Args:
            msg_id: ID сообщения (str или bytes)

        Returns:
            Строковое представление message_id
        """
        try:
            if isinstance(msg_id, bytes):
                # Декодируем байты в строку с обработкой ошибок
                return msg_id.decode("utf-8", errors="replace")
            else:
                return str(msg_id)
        except Exception as e:
            # Если даже преобразование не удалось, возвращаем запасной вариант
            return f"<unable to decode message_id: {e}>"

    def mark_as_read(self, message_id: str) -> bool:
        """Помечает письмо как прочитанное"""
        try:
            if self.connection:
                self.connection.store(message_id, "+FLAGS", "\\Seen")
                logger.debug(f"Marked email {message_id} as read")
                return True
        except Exception as e:
            logger.error(f"Error marking email {message_id} as read: {e}")
        return False
