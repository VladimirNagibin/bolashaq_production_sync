import time

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from core.logger import logger
from services.dependencies.dependencies import get_product_service
from services.dependencies.dependencies_repo import request_context
from services.products.product_services import ProductClient

products_router = APIRouter(
    prefix="/products", dependencies=[Depends(request_context)]
)


@products_router.post("/process")  # type: ignore
async def handle_bitrix24_webhook(
    request: Request,
    product_handler: ProductClient = Depends(get_product_service),
) -> JSONResponse:
    """
    Обработчик вебхуков Bitrix24 для товаров

    - Принимает webhook в формате application/x-www-form-urlencoded
    - Валидирует подпись и данные
    - Обрабатывает поля
    - Записывает изменённые значения
    """
    logger.info("Received Bitrix24 webhook request product")
    try:
        return await product_handler.product_processing(request)
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
