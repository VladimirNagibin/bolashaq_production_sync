from functools import wraps
from typing import Any, Callable, Coroutine, TypeVar, cast

from fastapi import HTTPException, status

from core.logger import logger

from .exceptions import BitrixApiError, BitrixAuthError

T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Coroutine[Any, Any, Any]])


def handle_bitrix_errors() -> Callable[[F], F]:
    """
    Декоратор для обработки ошибок при работе с Bitrix24 API.

    Returns:
        Декоратор, который обрабатывает исключения и преобразует их в
        соответствующие HTTP-ответы
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise
            except (BitrixAuthError, BitrixApiError) as e:
                logger.warning(
                    f"Bitrix API error in {func.__name__}: {e}",
                    extra={"function": func.__name__},
                )
                raise
            except Exception as e:
                logger.exception(
                    f"Unexpected error in {func.__name__}: {e}",
                    extra={
                        "function": func.__name__,
                        "error_type": type(e).__name__,
                    },
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal server error while calling Bitrix24 API",
                )

        return cast(F, wrapper)

    return decorator
