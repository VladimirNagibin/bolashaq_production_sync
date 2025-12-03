from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from core.logger import logger
from services.deals.deal_services import DealClient
from services.dependencies.dependencies import (
    get_deal_service,
)
from services.dependencies.dependencies_repo import request_context
from services.exceptions import BaseAppException

from ..deps import verify_incoming_webhook_token
from ..schemas.response_schemas import ErrorResponse, SuccessResponse

deals_webhook_router = APIRouter(
    prefix="/deals-webhook",
    dependencies=[
        Depends(request_context),
        Depends(verify_incoming_webhook_token),
    ],
)


@deals_webhook_router.get(
    "/deals-without-offer",
    summary="Handel deals without offer",
    description="Set fields and move deals without offer.",
    responses={
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
    },
)  # type: ignore
async def deals_without_offer(
    user_id: Annotated[
        str, Query(..., description="ID пользователя из шаблона")
    ],
    deal_id: Annotated[str, Query(..., description="ID сделки")],
    deal_client: DealClient = Depends(get_deal_service),
) -> SuccessResponse:
    try:
        await deal_client.handle_deal_without_offer(user_id, deal_id)
        return SuccessResponse(
            message=(
                f"Deal with ID={deal_id} successfully processed without offer"
            )
        )
    except BaseAppException as e:
        logger.error(f"Error processing deal with ID={deal_id}: {e}")
        raise
    except HTTPException as e:
        logger.error(f"Error processing deal with ID={deal_id}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error processing deal with ID={deal_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера при обработке сделки.",
        ) from e


@deals_webhook_router.get(
    "/deals-set-products-string-field",
    summary="Set deals products in string field",
    description="Set deals products in string field.",
    responses={
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
    },
)  # type: ignore
async def deals_set_products_string_field(
    user_id: Annotated[
        str, Query(..., description="ID пользователя из шаблона")
    ],
    deal_id: Annotated[str, Query(..., description="ID сделки")],
    products: Annotated[str, Query(..., description="Список продуктов")],
    deal_client: DealClient = Depends(get_deal_service),
) -> SuccessResponse:
    try:
        await deal_client.set_products_string_field(user_id, deal_id, products)
        return SuccessResponse(
            message=(
                f"Deal with ID={deal_id} successfully processed without offer"
            )
        )
    except BaseAppException as e:
        logger.error(f"Error processing deal with ID={deal_id}: {e}")
        raise
    except HTTPException as e:
        logger.error(f"Error processing deal with ID={deal_id}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error processing deal with ID={deal_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера при обработке сделки.",
        ) from e


@deals_webhook_router.get(
    "/deal-set-stage-status",
    summary="Set stage and status deals",
    description="Set stage and status deals.",
    responses={
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
    },
)  # type: ignore
async def deals_set_stage_status(
    deal_id: Annotated[str, Query(..., description="ID сделки")],
    deal_stage: Annotated[int, Query(..., description="Стадия сделки")],
    deal_status: Annotated[str, Query(..., description="Статус сделки")],
    user_id: Annotated[
        str | None, Query(..., description="ID пользователя из шаблона")
    ] = None,
    deal_client: DealClient = Depends(get_deal_service),
) -> SuccessResponse:
    try:
        await deal_client.set_stage_status_deal(
            deal_id, deal_stage, deal_status
        )
        return SuccessResponse(
            message=(
                f"Deal with ID={deal_id} successfully set stage and status to "
                f"{deal_stage} and {deal_status}"
            )
        )
    except BaseAppException as e:
        logger.error(f"Error processing deal with ID={deal_id}: {e}")
        raise
    except HTTPException as e:
        logger.error(f"Error processing deal with ID={deal_id}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error processing deal with ID={deal_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера при обработке сделки.",
        ) from e
