import time
from functools import wraps
from inspect import iscoroutinefunction
from typing import Any, Callable, TypeVar, cast

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, NoResultFound, SQLAlchemyError

from core.logger import logger

from .exceptions import (
    BitrixApiError,
    BitrixAuthError,
    ConflictException,
    DatabaseConnectionError,
    EntityNotFoundException,
)

F = TypeVar("F", bound=Callable[..., Any])


def _is_coroutine_function(func: Callable[..., Any]) -> bool:
    """Проверяет, является ли функция асинхронной."""
    return iscoroutinefunction(func)


def handle_bitrix_errors() -> Callable[[F], F]:
    """
    Декоратор для обработки ошибок Bitrix24 API.

    Перехватывает специфичные ошибки Bitrix и общие исключения,
    логируя их и преобразуя в HTTPException для ответа API.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise
            except (BitrixAuthError, BitrixApiError) as e:
                logger.warning(f"Ошибка Bitrix API в {func.__name__}: {e}")
                raise
            except Exception as e:
                logger.exception(
                    f"Непредвиденная ошибка в {func.__name__}: {e}"
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Внутренняя ошибка сервера при вызове Bitrix24 API",
                ) from e

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except HTTPException:
                raise
            except (BitrixAuthError, BitrixApiError) as e:
                logger.warning(f"Ошибка Bitrix API в {func.__name__}: {e}")
                raise
            except Exception as e:
                logger.exception(
                    f"Непредвиденная ошибка в {func.__name__}: {e}"
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Внутренняя ошибка сервера при вызове Bitrix24 API",
                ) from e

        return cast(
            F, async_wrapper if _is_coroutine_function(func) else sync_wrapper
        )

    return decorator


def handle_db_errors(func: F) -> F:
    """
    Декоратор для обработки ошибок базы данных.

    **Важно:** Декоратор рассчитывает на то, что он применяется к методу
    класса, у которого есть атрибуты `self.session` (объект сессии SQLAlchemy)
    и `self.model` (класс модели SQLAlchemy).

    Автоматически выполняет откат транзакции (rollback) в случае ошибки.
    """

    @wraps(func)
    async def async_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        try:
            return await func(self, *args, **kwargs)
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Integrity error in {func.__name__}: {str(e)}")
            raise ConflictException(
                self.model.__name__, kwargs.get("external_id", "unknown")
            ) from e
        except NoResultFound as e:
            await self.session.rollback()
            logger.warning(f"Entity not found in {func.__name__}: {str(e)}")
            raise EntityNotFoundException(
                self.model.__name__, kwargs.get("external_id", "unknown")
            ) from e
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Database error in {func.__name__}: {str(e)}")
            raise DatabaseConnectionError(
                f"Database operation failed in {func.__name__}"
            ) from e

    @wraps(func)
    def sync_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        try:
            return func(self, *args, **kwargs)
        except IntegrityError as e:
            self.session.rollback()
            logger.error(f"Integrity error in {func.__name__}: {str(e)}")
            raise ConflictException(
                self.model.__name__, kwargs.get("external_id", "unknown")
            ) from e
        except NoResultFound as e:
            self.session.rollback()
            logger.warning(f"Entity not found in {func.__name__}: {str(e)}")
            raise EntityNotFoundException(
                self.model.__name__, kwargs.get("external_id", "unknown")
            ) from e
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Database error in {func.__name__}: {str(e)}")
            raise DatabaseConnectionError(
                f"Database operation failed in {func.__name__}"
            ) from e

    return cast(
        F, async_wrapper if _is_coroutine_function(func) else sync_wrapper
    )


def log_errors(error_message: str) -> Callable[[F], F]:
    """
    Декоратор для логирования любых исключений, возникших в функции.

    :param error_message: Шаблон сообщения для логирования ошибки.
                         Можно использовать аргументы функции через .format().
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Форматируем сообщение с аргументами функции
                formatted_message = error_message.format(*args, **kwargs)
                logger.error(f"{formatted_message}: {str(e)}", exc_info=True)
                raise

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                formatted_message = error_message.format(*args, **kwargs)
                logger.error(f"{formatted_message}: {str(e)}", exc_info=True)
                raise

        return cast(
            F, async_wrapper if _is_coroutine_function(func) else sync_wrapper
        )

    return decorator


def log_execution_time(operation_name: str) -> Callable[[F], F]:
    """
    Декоратор для измерения и логирования времени выполнения функции.

    :param operation_name: Название операции, которое будет указано в логах.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            try:
                return await func(*args, **kwargs)
            finally:
                execution_time = time.perf_counter() - start_time
                logger.info(
                    f"Operation '{operation_name}' completed in "
                    f"{execution_time:.4f} seconds",
                    extra={
                        "operation": operation_name,
                        "execution_time_seconds": execution_time,
                    },
                )

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                execution_time = time.perf_counter() - start_time
                logger.info(
                    f"Operation '{operation_name}' completed in "
                    f"{execution_time:.4f} seconds",
                    extra={
                        "operation": operation_name,
                        "execution_time_seconds": execution_time,
                    },
                )

        return cast(
            F, async_wrapper if _is_coroutine_function(func) else sync_wrapper
        )

    return decorator
