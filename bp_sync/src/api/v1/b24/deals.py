import time

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from core.logger import logger
from services.deals.deal_services import DealClient
from services.dependencies.dependencies import get_deal_service

deals_router = APIRouter(prefix="/deals")


@deals_router.post("/process")  # type: ignore
async def handle_bitrix24_webhook_raw(
    request: Request,
    deal_client: DealClient = Depends(get_deal_service),
) -> JSONResponse:
    """
    Обработчик вебхуков Bitrix24 для сделок

    - Принимает webhook в формате application/x-www-form-urlencoded
    - Валидирует подпись и данные
    - Обрабатывает тестовые и продакшен сделки
    - Возвращает детализированные ответы
    """
    logger.info("Received Bitrix24 webhook request")
    try:
        return await deal_client.deal_processing(request)
    except Exception as e:
        logger.error(f"Unhandled error in webhook handler: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "fail",
                "message": "Deal processing failed",
                "error": str(e),
                "timestamp": time.time(),
            },
        )
