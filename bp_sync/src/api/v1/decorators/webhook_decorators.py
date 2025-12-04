import functools
from typing import Any, Callable, Coroutine

from fastapi import HTTPException, status

from core.logger import logger
from services.exceptions import BaseAppException

from ..schemas.response_schemas import ErrorResponse, SuccessResponse

RESPONSES_WEBHOOK: dict[int | str, dict[str, Any]] | None = {
    200: {
        "model": SuccessResponse,
        "description": "Сделка успешно обработана",
    },
    401: {
        "model": ErrorResponse,
        "description": "Неверные учетные данные",
    },
    404: {"model": ErrorResponse, "description": "Сделка не найдена"},
    500: {
        "model": ErrorResponse,
        "description": "Внутренняя ошибка сервера",
    },
}


# Декоратор для централизации логики вебхуков
def handle_deal_webhook_logic(
    func: Callable[..., Any],
) -> Callable[..., Coroutine[Any, Any, SuccessResponse]]:
    """
    Декоратор для обработки логики вебхуков сделок.
    Централизует логирование и обработку ошибок.
    """

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> SuccessResponse:
        # Извлекаем параметры для логирования
        try:
            deal_id = _get_deal_id_from_kwargs(kwargs)
        except Exception:
            deal_id = "N/A"
        endpoint_name = func.__name__
        logger.info(
            f"Webhook '{endpoint_name}' started for Deal ID: {deal_id}"
        )
        try:
            # Вызываем основную функцию (сервисный слой)
            await func(*args, **kwargs)

            logger.info(
                f"Webhook '{endpoint_name}' finished successfully for Deal "
                f"ID: {deal_id}"
            )
            return SuccessResponse(
                message=f"Сделка с ID={deal_id} успешно обработана."
            )

        except BaseAppException as e:
            # Позволяем глобальному обработчику исключений FastAPI обработать.
            # Он преобразует BaseAppException в корректный ErrorResponse.
            logger.warning(
                f"Webhook '{endpoint_name}' failed for Deal ID: {deal_id}. "
                f"Reason: {e.message}"
            )
            raise

        except HTTPException:
            # Если уже было вызвано HTTPException (например, в зависимостях),
            # просто пробрасываем его дальше.
            raise

        except Exception as e:
            # Логируем любую непредвиденную ошибку с полным трейсбеком.
            logger.exception(
                f"An unexpected error occurred in webhook '{endpoint_name}' "
                f"for Deal ID: {deal_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Внутренняя ошибка сервера при обработке сделки.",
            ) from e

    return wrapper


def _get_deal_id_from_kwargs(kwargs: dict[Any, Any]) -> str:
    """
    Безопасно извлекает 'deal_id' из kwargs.
    Поддерживает два сценария:
    1. `deal_id` является прямым аргументом.
    2. `deal_id` является атрибутом первого элемента кортежа `common_params`.
    """
    # Сценарий 1: deal_id является прямым аргументом
    if "deal_id" in kwargs:
        return str(kwargs["deal_id"])

    # Сценарий 2: deal_id находится в common_params
    common_params = kwargs.get("common_params")
    if (
        isinstance(common_params, (list, tuple))
        and len(common_params) > 0
        and hasattr(common_params[0], "deal_id")
    ):
        return str(common_params[0].deal_id)
    # Если ничего не найдено, возвращаем значение по умолчанию
    return "N/A"
