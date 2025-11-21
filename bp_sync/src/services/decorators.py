from functools import wraps
from typing import Any, Callable, TypeVar

from fastapi import HTTPException, status

from core.logger import logger

from .exceptions import BitrixApiError, BitrixAuthError

# Более простая аннотация
AsyncFunc = TypeVar("AsyncFunc", bound=Callable[..., Any])


def handle_bitrix_errors() -> Callable[[AsyncFunc], AsyncFunc]:
    """Декоратор для обработки ошибок Bitrix24 API."""

    def decorator(func: AsyncFunc) -> AsyncFunc:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
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
                )

        return wrapper  # type: ignore

    return decorator
