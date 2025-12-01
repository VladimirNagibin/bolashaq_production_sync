from typing import Any

from fastapi import HTTPException, status


class BitrixAuthError(Exception):
    """Ошибка аутентификации в Bitrix24."""

    def __init__(
        self,
        message: str = "Bitrix authentication failed",
        detail: dict[Any, Any] | str | None = None,
    ):
        self.message = message
        self.detail = detail
        super().__init__(message)

    def __str__(self) -> str:
        base_msg = f"BitrixAuthError: {self.message}"
        if self.detail:
            return f"{base_msg} | Detail: {self.detail}"
        return base_msg


class BitrixApiError(HTTPException):  # type: ignore[misc]
    """Кастомное исключение для ошибок Bitrix24 API."""

    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error: str = "Unknown error",
        error_description: str = "Unknown Bitrix API error",
    ):
        super().__init__(
            status_code=status_code,
            detail={"error": error, "error_description": error_description},
        )
        self.detail: dict[str, str] = {
            "error": error,
            "error_description": error_description,
        }

    def is_bitrix_error(self, expected_error: str) -> bool:
        """Проверяет, является ли ошибка заданного типа"""
        return bool(self.detail.get("error_description") == expected_error)

    def is_not_found_error(self) -> bool:
        """Проверяет, является ли ошибка ошибкой 'Not Found'"""
        return (
            self.status_code == status.HTTP_400_BAD_REQUEST
            and self.is_bitrix_error("Not found")
        )

    def __str__(self) -> str:
        return (
            f"BitrixApiError(status_code={self.status_code}, "
            f"error='{self.detail['error']}', "
            f"description='{self.detail['error_description']}')"
        )


class ConflictException(HTTPException):  # type: ignore[misc]
    """Исключение для конфликтующих операций (HTTP 409)."""

    def __init__(self, entity: str, external_id: str | int):
        detail = f"{entity} with ID: {external_id} already exists"
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)
        self.entity = entity
        self.external_id = external_id


class CyclicCallException(Exception):
    """Исключение для обнаружения циклических вызовов."""

    def __init__(self, message: str = "Cyclic call detected"):
        self.message = message
        super().__init__(message)


class DealProcessingError(Exception):
    """Исключение для ошибок обработки сделки."""

    def __init__(
        self,
        message: str = "Deal processing failed",
        deal_id: int | None = None,
    ):
        self.message = message
        self.deal_id = deal_id
        super().__init__(
            f"{message} | Deal ID: {deal_id}" if deal_id else message
        )


class DealNotFoundError(DealProcessingError):
    """Исключение, когда сделка не найдена в Bitrix24."""

    pass


class DealNotInMainFunnelError(DealProcessingError):
    """Исключение, когда сделка не находится в основной воронке."""

    pass


class DealSyncError(DealProcessingError):
    """Исключение, возникающее при ошибке синхронизации данных сделки."""

    pass


class InvalidDealStateError(DealProcessingError):
    """Исключение для некорректного состояния сделки, требующего отката."""

    pass


class ExternalServiceError(DealProcessingError):
    """Ошибка внешнего сервиса"""

    pass


class WebhookValidationError(Exception):
    """Кастомное исключение для ошибок валидации вебхуков."""

    def __init__(
        self,
        message: str = "Webhook validation failed",
        validation_details: str | None = None,
    ):
        self.message = message
        self.validation_details = validation_details
        super().__init__(
            f"{message}: {validation_details}"
            if validation_details
            else message
        )


class WebhookSecurityError(Exception):
    """Кастомное исключение для ошибок безопасности вебхуков."""

    def __init__(
        self,
        message: str = "Webhook security violation",
        security_context: str | None = None,
    ):
        self.message = message
        self.security_context = security_context
        super().__init__(
            f"{message} | Context: {security_context}"
            if security_context
            else message
        )


class LockAcquisitionError(Exception):
    """Ошибка получения блокировки."""

    def __init__(
        self,
        resource: str = "Resource",
        message: str = "Failed to acquire lock",
    ):
        self.resource = resource
        self.message = message
        super().__init__(f"{message} for resource: {resource}")


class MaxRetriesExceededError(LockAcquisitionError):
    """Достигнуто максимальное количество попыток получения блокировки."""

    def __init__(self, resource: str = "Resource", max_retries: int = 0):
        self.max_retries = max_retries
        message = f"Maximum retries ({max_retries}) exceeded"
        super().__init__(resource, message)


def create_bitrix_api_error_from_response(
    status_code: int, response_data: dict[str, Any] | None = None
) -> BitrixApiError:
    """Создает BitrixApiError на основе ответа от API."""
    if response_data:
        error = response_data.get("error", "Unknown error")
        error_description = response_data.get(
            "error_description", "No description provided"
        )
    else:
        error = "HTTP Error"
        error_description = f"Status code: {status_code}"

    return BitrixApiError(
        status_code=status_code,
        error=error,
        error_description=error_description,
    )


def should_retry_operation(exception: Exception) -> bool:
    """
    Определяет, следует ли повторять операцию при возникновении исключения.

    Returns:
        True если операцию стоит повторить, False в противном случае
    """
    retryable_exceptions = (
        BitrixApiError,  # Некоторые ошибки API могут быть временными
        LockAcquisitionError,
    )

    if isinstance(exception, retryable_exceptions):
        # Не повторяем для определенных статус кодов
        if (
            isinstance(exception, BitrixApiError)
            and exception.status_code >= 400
        ):
            # Повторяем только для 5xx
            return bool(exception.status_code >= 500)
        return True

    return False


class TokenStorageError(Exception):
    """Базовое исключение для ошибок хранилища токенов."""

    pass


class TokenStorageConnectionError(TokenStorageError):
    """Ошибка соединения с хранилищем."""

    pass


class TokenEncryptionError(TokenStorageError):
    """Ошибка шифрования/дешифрования токена."""

    pass


class TokenNotFoundError(TokenStorageError):
    """Токен не найден в хранилище."""

    pass


class TokenCipherError(Exception):
    """Базовое исключение для ошибок шифрования токенов."""

    pass


class InvalidEncryptionKeyError(TokenCipherError):
    """Некорректный ключ шифрования."""

    pass


class TokenDecryptionError(TokenCipherError):
    """Ошибка при дешифровании токена."""

    pass


class ValidationError(Exception):
    """Кастомное исключение для ошибок валидации"""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        value: Any | None = None,
    ):
        self.message = message
        self.field = field
        self.value = value
        super().__init__(self.message)


class EntityNotFoundException(Exception):
    """Не найдена сущность в БД"""

    ...


class DatabaseConnectionError(Exception):
    """Ошибка соединения с БД"""

    ...


class BaseAppException(Exception):
    """Базовое исключение для нашего приложения."""

    def __init__(self, error_code: str, message: str):
        self.error_code = error_code
        self.message = message
        super().__init__(message)
