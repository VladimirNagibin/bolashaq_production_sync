import time

from fastapi import Request, status
from fastapi.responses import JSONResponse

from core.logger import logger
from services.base_services.base_service import BaseEntityClient


async def handle_bitrix24_webhook(
    request: Request,
    entity_client: BaseEntityClient,
    entity_type_id: int | None = None,
) -> JSONResponse:
    """
    Обработчик вебхуков Bitrix24 для сущностей

    - Принимает webhook в формате application/x-www-form-urlencoded
    - Валидирует подпись и данные
    - Обрабатывает тестовые и продакшен сущность
    - Возвращает детализированные ответы
    """
    logger.info(
        f"Received Bitrix24 webhook request for {entity_client.entity_name}"
    )
    try:
        return await entity_client.entity_processing(request, entity_type_id)
    except Exception as e:
        logger.error(
            f"Unhandled error in {entity_client.entity_name} webhook handler: "
            f"{e}"
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "fail",
                "message": f"{entity_client.entity_name} processing failed",
                "error": str(e),
                "timestamp": time.time(),
            },
        )
