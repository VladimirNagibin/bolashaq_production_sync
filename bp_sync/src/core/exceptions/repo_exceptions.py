from typing import Any
from uuid import UUID

from fastapi import HTTPException, status


class RepositoryError(Exception):
    """Базовое исключение репозитория."""

    def __init__(self, message: str, original_error: Exception | None = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class EntityNotFoundError(RepositoryError):
    """Сущность не найдена."""

    def __init__(
        self,
        entity_name: str,
        entity_id: str | UUID | None = None,
        **filters: Any,
    ):
        self.entity_name = entity_name
        self.entity_id = entity_id
        self.filters = filters
        message = f"{entity_name} not found"
        if entity_id:
            message += f" with id={entity_id}"
        elif filters:
            filter_str = ", ".join(f"{k}={v}" for k, v in filters.items())
            message += f" with filters: {filter_str}"
        super().__init__(message)

    def to_http(self) -> HTTPException:
        """Конвертировать в HTTPException для FastAPI."""
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=self.message
        )


class DuplicateEntityError(RepositoryError):
    """Дубликат сущности."""

    def __init__(self, entity_name: str, **fields: Any):
        self.entity_name = entity_name
        self.fields = fields
        field_str = ", ".join(f"{k}={v}" for k, v in fields.items())
        message = f"{entity_name} already exists with {field_str}"
        super().__init__(message)

    def to_http(self) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=self.message
        )


class DatabaseOperationError(RepositoryError):
    """Ошибка операции с БД."""

    def __init__(
        self,
        operation: str,
        entity_name: str,
        detail: str = "",
        original_error: Exception | None = None,
    ):
        self.operation = operation
        self.entity_name = entity_name
        self.detail = detail
        message = f"Database {operation} failed for {entity_name}"
        if detail:
            message += f": {detail}"
        super().__init__(message, original_error)

    def to_http(self) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database operation failed: {self.operation}",
        )


class InvalidConfigurationError(RepositoryError):
    """Неверная конфигурация импорта."""

    def __init__(self, source: str, reason: str):
        self.source = source
        self.reason = reason
        message = (
            f"Invalid import configuration for source '{source}': {reason}"
        )
        super().__init__(message)

    def to_http(self) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=self.message
        )


class BusinessLogicError(RepositoryError):
    """Ошибка бизнес-логики."""

    def __init__(self, message: str):
        super().__init__(message)

    def to_http(self) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=self.message,
        )
