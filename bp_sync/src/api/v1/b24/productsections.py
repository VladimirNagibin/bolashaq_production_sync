import time

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from core.logger import logger
from services.dependencies.dependencies import get_productsection_service
from services.dependencies.dependencies_repo import request_context
from services.productsections.productsection_services import (
    ProductsectionClient,
)

productsections_router = APIRouter(
    prefix="/productsections", dependencies=[Depends(request_context)]
)


@productsections_router.get(
    "/update-productsections",
    summary="Update productsections",
    description="Update productsections from Bitrix24",
)  # type: ignore
async def update_productsections(
    start: int = 0,
    productsection_client: ProductsectionClient = Depends(
        get_productsection_service
    ),
) -> JSONResponse:
    result, next, total = await productsection_client.import_from_bitrix(start)
    return JSONResponse(
        status_code=200,
        content={
            "updated": len(result),
            "next": next,
            "total": total,
        },
    )


@productsections_router.post("/process")  # type: ignore
async def handle_bitrix24_webhook_lead(
    request: Request,
    productsection_client: ProductsectionClient = Depends(
        get_productsection_service
    ),
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
        return await productsection_client.productsection_processing(request)
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
