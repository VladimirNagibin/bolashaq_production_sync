import email
import imaplib
import re
import ssl
import time
from contextlib import contextmanager
from datetime import datetime
from email.header import decode_header
from email.message import Message
from email.utils import parsedate_to_datetime
from typing import Any, Generator

from core.logger import logger
from core.settings import settings
from schemas.email_schemas import EmailMessage


class EmailChecker:
    def __init__(
        self,
        email_account: str | None = None,
        app_password: str | None = None,
        imap_server: str | None = None,
        port: int | None = None,
        email_folder: str | None = None,
    ):
        self.email_account = email_account or settings.EMAIL_USERNAME
        self.app_password = app_password or settings.EMAIL_PASSWORD
        self.imap_server = imap_server or settings.EMAIL_IMAP_SERVER
        self.port = port or settings.EMAIL_IMAP_PORT
        self.email_folder = email_folder or settings.EMAIL_FOLDER
        self.connection: imaplib.IMAP4_SSL | None = None
        self.processed_message_ids: set[str] = set()

    @contextmanager
    def _managed_connection(self) -> Generator[Any | None, None, None]:
        """Контекстный менеджер для управления соединением"""
        connection_established = False
        try:
            if not self.connection:
                connection_established = self.connect()
            yield self.connection if connection_established else None
        finally:
            # Не закрываем соединение, чтобы переиспользовать
            pass

    def get_new_emails(self, since_minutes: int = 60) -> list[EmailMessage]:
        """
        Получает новые письма от целевого отправителя
        """
        emails: list[EmailMessage] = []
        try:
            # Подключение к серверу
            if not self.connect() or not self.connection:
                logger.error("Failed to connect to email server")
                return emails

            search_criteria = f'UNSEEN FROM "{settings.TARGET_SENDER_EMAIL}"'

            logger.debug(f"Searching emails with criteria: {search_criteria}")
            status, messages = self.connection.search(None, search_criteria)

            if status != "OK":
                logger.warning("No emails found matching criteria")
                return emails

            message_ids = messages[0].split()
            logger.info(
                f"Found {len(message_ids)} new emails from target sender"
            )

            for msg_id in message_ids:
                try:
                    status, msg_data = self.connection.fetch(
                        msg_id, "(BODY.PEEK[])"  # "(RFC822)"
                    )
                    if status != "OK":
                        logger.warning(f"Failed to fetch email {msg_id}")
                        continue

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
            # self.disconnect()
            return emails
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
        return emails

    def connect(self) -> bool:
        if self.connection:
            try:
                # Проверяем, что соединение еще живо
                self.connection.noop()
                return True
            except Exception:
                # Соединение разорвано, закрываем и создаем новое
                self.disconnect()
        max_retries = 3
        initial_delay = 2

        for attempt in range(max_retries):
            try:
                logger.info(
                    f"Connection attempt {attempt + 1} to "
                    f"{self.imap_server}:{self.port}"
                )

                # Создаем SSL контекст
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE

                self.connection = imaplib.IMAP4_SSL(
                    self.imap_server, self.port, ssl_context=context
                )
                self.connection.socket().settimeout(30)
                self.connection.login(self.email_account, self.app_password)
                self.connection.select(self.email_folder)
                logger.info("Successfully connected to email server")
                return True

            except (ssl.SSLError, imaplib.IMAP4.error, OSError) as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")

                if attempt < max_retries - 1:
                    # Экспоненциальная задержка
                    delay = initial_delay * (2**attempt)
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                    self.disconnect()
                else:
                    logger.error("All connection attempts failed")
                    return False
            except Exception as e:
                logger.error(f"Unexpected connection error: {e}")
                return False
        return False

    def disconnect(self) -> None:
        """Закрывает соединение с IMAP сервером"""
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                pass
            try:
                self.connection.logout()
            except Exception:
                pass
            finally:
                self.connection = None
                logger.info("Отключено от email сервера")

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
            body = self._extract_email_body(msg)

            return EmailMessage(
                message_id=(
                    message_id.decode()
                    if isinstance(message_id, bytes)
                    else str(message_id)
                ),
                subject=subject,
                body=body.strip() if body else "",
                sender=sender,
                recipient=recipient,
                received_date=received_date,
                attachments_count=self._count_attachments(msg),
                headers=headers,
            )
        except Exception as e:
            logger.error(f"Error parsing email {message_id}: {e}")
            return None

    def _extract_email_body(self, msg: Message) -> str:
        """Извлекает текстовое тело письма"""
        body = ""
        html_body = ""

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                if "attachment" in content_disposition:
                    continue

                if content_type == "text/plain" and not body:
                    body = self._decode_part(part)
                elif content_type == "text/html" and not body:
                    html_body = self._decode_part(part)
        else:
            content_type = msg.get_content_type()
            if content_type == "text/plain":
                body = self._decode_part(msg)
            elif content_type == "text/html":
                html_body = self._decode_part(msg)

        # Если нашли HTML но не нашли plain text, преобразуем HTML в текст
        if not body and html_body:
            body = self._html_to_text(html_body)

        return body

    def _decode_part(self, part: Message) -> str:
        """Декодирует часть письма"""
        try:
            payload = part.get_payload(decode=True)
            if payload:
                charset = part.get_content_charset() or "utf-8"
                return payload.decode(  # type: ignore[union-attr]
                    charset, errors="ignore"
                )
        except Exception as e:
            logger.warning(f"Error decoding part: {e}")
        return ""

    def _html_to_text(self, html: str) -> str:
        """Преобразует HTML в простой текст"""
        try:
            # Удаляем HTML теги
            text = re.sub("<[^<]+?>", "", html)
            # Заменяем HTML entities
            text = text.replace("&nbsp;", " ").replace("&amp;", "&")
            text = text.replace("&lt;", "<").replace("&gt;", ">")
            text = text.replace("&quot;", '"')
            # Убираем лишние пробелы
            text = re.sub(r"\s+", " ", text).strip()
            return text
        except Exception as e:
            logger.warning(f"Error converting HTML to text: {e}")
            return html

    def _count_attachments(self, msg: Message) -> int:
        """Считает количество вложений"""
        count = 0
        if msg.is_multipart():
            for part in msg.walk():
                content_disposition = str(part.get("Content-Disposition", ""))
                if "attachment" in content_disposition:
                    count += 1
        return count

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

    def mark_as_read(self, msg_id: str) -> bool:
        try:
            if not self.connection or not self.connect():
                logger.error("Failed to connect to email server")
                return False
            self.connection.store(msg_id, "+FLAGS", "\\Seen")
            return True
        except Exception:
            return False
