import time
from typing import Any
from urllib.parse import unquote

from fastapi import Request
from pydantic import ValidationError

from core.logger import logger
from core.settings import settings
from schemas.webhook_schemas import BitrixWebhookAuth, BitrixWebhookPayload

from ..exceptions import WebhookSecurityError, WebhookValidationError


class WebhookService:
    """
    Сервис для обработки и валидации вебхуков Bitrix24.

    Обеспечивает:
    - Парсинг form-data в структурированный объект
    - Валидацию безопасности (токены, временные метки)
    - Проверку разрешенных событий
    """

    def __init__(
        self,
        allowed_events: set[str] | None = None,
        expected_tokens: dict[str, str] | None = None,
        max_age: int | None = None,
    ) -> None:
        """
        Инициализация сервиса вебхуков.

        Args:
            allowed_events: Множество разрешенных событий
            expected_tokens: Словарь токенов приложений и доменов
            max_age: Максимальный возраст вебхука в секундах
        """
        webhook_config = settings.web_hook_config

        self.allowed_events = allowed_events or set(
            webhook_config.get("allowed_events", [])
        )
        self.expected_tokens = expected_tokens or webhook_config.get(
            "expected_tokens", {}
        )
        self.max_age = max_age or settings.MAX_AGE_WEBHOOK

        logger.debug(
            "WebhookService initialized",
            extra={
                "allowed_events_count": len(self.allowed_events),
                "expected_tokens_count": len(self.expected_tokens),
                "max_age": self.max_age,
            },
        )

    async def process_webhook(self, request: Request) -> BitrixWebhookPayload:
        """
        Основной метод обработки входящего вебхука.

        Args:
            request: Входящий HTTP запрос

        Returns:
            Валидированный и обработанный payload вебхука

        Raises:
            WebhookValidationError: Ошибка валидации данных
            WebhookSecurityError: Ошибка безопасности
        """
        logger.debug("Starting webhook processing")

        try:
            # Получаем и парсим данные
            payload = await self._parse_webhook_data(request)

            # Валидируем вебхук
            validated_payload = await self._validate_webhook(payload)

            logger.info(
                "Webhook processed successfully",
                extra={
                    "event": validated_payload.event,
                    "entity_id": validated_payload.entity_id,
                    "domain": validated_payload.auth.domain,
                },
            )

            return validated_payload

        except (WebhookValidationError, WebhookSecurityError):
            raise
        except Exception as e:
            logger.error(
                "Unexpected error during webhook processing",
                extra={"error": str(e), "error_type": type(e).__name__},
            )
            raise WebhookValidationError(
                f"Webhook processing failed: {e}"
            ) from e

    async def _parse_webhook_data(
        self, request: Request
    ) -> BitrixWebhookPayload:
        """
        Парсит form-data и создает объект вебхука.

        Args:
            request: Входящий HTTP запрос

        Returns:
            Структурированный payload вебхука

        Raises:
            WebhookValidationError: Ошибка парсинга или валидации данных
        """
        parsed_body: dict[str, Any] = {}

        try:
            form_data = await request.form()
            parsed_body = dict(form_data)

            # Преобразуем плоскую структуру во вложенную
            structured_data = self._parse_flat_to_nested(parsed_body)

            logger.debug(
                "Webhook data parsed successfully",
                extra={"fields_count": len(structured_data)},
            )

            return BitrixWebhookPayload(**structured_data)

        except ValidationError as e:
            logger.error(
                "Webhook data validation failed",
                extra={
                    "errors": e.errors(),
                    "body_preview": str(parsed_body)[:200],
                },
            )
            raise WebhookValidationError(
                f"Invalid webhook data structure: {e}"
            ) from e
        except Exception as e:
            logger.error(
                "Failed to parse webhook data", extra={"error": str(e)}
            )
            raise WebhookValidationError("Failed to parse webhook data") from e

    def _parse_flat_to_nested(
        self, flat_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Преобразует плоскую структуру form-data во вложенный словарь.

        Поддерживает ключи вида:
        - data[FIELDS][ID] -> data: {FIELDS: {ID: value}}
        - auth[domain] -> auth: {domain: value}

        Args:
            flat_data: Плоский словарь form-data

        Returns:
            Вложенный словарь структурированных данных
        """
        result: dict[str, Any] = {}

        for key, value in flat_data.items():
            # Декодируем URL-encoded ключи
            decoded_key = unquote(key)

            if self._is_nested_key(decoded_key):
                self._process_nested_key(decoded_key, value, result)
            else:
                result[decoded_key] = value

        return result

    def _is_nested_key(self, key: str) -> bool:
        """
        Проверяет, является ли ключ вложенным (содержит квадратные скобки).

        Args:
            key: Ключ для проверки

        Returns:
            True если ключ содержит вложенность
        """
        return "[" in key and "]" in key

    def _process_nested_key(
        self, key: str, value: Any, result: dict[str, Any]
    ) -> None:
        """
        Обрабатывает вложенные ключи вида data[FIELDS][ID].

        Args:
            key: Вложенный ключ
            value: Значение
            result: Результирующий словарь для заполнения
        """
        parts = key.replace("]", "").split("[")
        current_level = result

        for i, part in enumerate(parts):
            if not part:  # Пропускаем пустые части
                continue

            is_last_part = i == len(parts) - 1

            if is_last_part:
                # Последняя часть - устанавливаем значение
                current_level[part] = value
            else:
                # Промежуточная часть - создаем/получаем вложенный словарь
                if part not in current_level:
                    current_level[part] = {}
                elif not isinstance(current_level[part], dict):
                    # Конфликт типов - перезаписываем значением словарем
                    logger.warning(
                        f"Type conflict for key '{key}', part '{part}'. "
                        f"Overwriting with dict."
                    )
                    current_level[part] = {}

                current_level = current_level[part]

    async def _validate_webhook(
        self, payload: BitrixWebhookPayload
    ) -> BitrixWebhookPayload:
        """
        Выполняет полную валидацию вебхука.

        Args:
            payload: Распаршенный payload вебхука

        Returns:
            Валидированный payload

        Raises:
            WebhookValidationError: Ошибка валидации данных
            WebhookSecurityError: Ошибка безопасности
        """
        logger.debug("Starting webhook validation")

        # Проверка события
        self._validate_event(payload.event)

        # Проверка безопасности
        self._validate_security(payload.auth, payload.ts)

        logger.debug("Webhook validation completed successfully")
        return payload

    def _validate_event(self, event: str) -> None:
        """
        Проверяет, разрешено ли событие вебхука.

        Args:
            event: Событие для проверки

        Raises:
            WebhookValidationError: Событие не разрешено
        """
        if event not in self.allowed_events:
            logger.warning(
                "Webhook event not allowed",
                extra={
                    "event": event,
                    "allowed_events": list(self.allowed_events),
                },
            )
            raise WebhookValidationError(
                f"Event '{event}' is not allowed. "
                f"Allowed events: {', '.join(sorted(self.allowed_events))}"
            )

        logger.debug(f"Event validated: {event}")

    def _validate_security(
        self, auth: BitrixWebhookAuth, timestamp: str
    ) -> None:
        """
        Выполняет проверки безопасности вебхука.

        Args:
            auth: Данные аутентификации
            timestamp: Временная метка

        Raises:
            WebhookSecurityError: Ошибка безопасности
        """
        logger.debug("Starting security validation")

        # Проверка токена
        if not self._verify_token(auth):
            logger.warning(
                "Invalid webhook token",
                extra={
                    "domain": auth.domain,
                    "application_token": (
                        auth.application_token[:8] + "..."
                        if auth.application_token
                        else None
                    ),
                },
            )
            raise WebhookSecurityError("Invalid webhook token")

        # Проверка временной метки
        if not self._verify_timestamp(timestamp):
            logger.warning(
                "Webhook timestamp validation failed",
                extra={"timestamp": timestamp, "max_age": self.max_age},
            )
            raise WebhookSecurityError(
                "Webhook timestamp is invalid or too old"
            )

        logger.debug("Security validation completed successfully")

    def _verify_token(self, auth: BitrixWebhookAuth) -> bool:
        """
        Проверяет валидность токена вебхука.

        Args:
            auth: Данные аутентификации

        Returns:
            True если токен валиден
        """
        if not auth.application_token:
            logger.debug("Missing application token")
            return False

        expected_domain = self.expected_tokens.get(auth.application_token)
        is_valid = bool(expected_domain == auth.domain)

        if not is_valid:
            logger.debug(
                "Token verification failed",
                extra={
                    "expected_domain": expected_domain,
                    "actual_domain": auth.domain,
                    "token_found": (
                        auth.application_token in self.expected_tokens
                    ),
                },
            )

        return is_valid

    def _verify_timestamp(self, timestamp: str) -> bool:
        """
        Проверяет свежесть вебхука по временной метке.

        Args:
            timestamp: Временная метка в строковом формате

        Returns:
            True если временная метка валидна
        """
        try:
            timestamp_int = int(timestamp)
            current_time = int(time.time())
            age = current_time - timestamp_int

            # Проверяем что временная метка не в будущем и не слишком старая
            is_valid = age >= 0 and age <= self.max_age

            if not is_valid:
                logger.debug(
                    "Timestamp validation failed",
                    extra={
                        "timestamp": timestamp_int,
                        "current_time": current_time,
                        "age": age,
                        "max_age": self.max_age,
                    },
                )

            return is_valid

        except (ValueError, TypeError) as e:
            logger.debug(
                "Invalid timestamp format",
                extra={"timestamp": timestamp, "error": str(e)},
            )
            return False


# Фабрика для dependency injection
def get_webhook_service() -> WebhookService:
    """Создает и возвращает экземпляр WebhookService."""
    return WebhookService()
