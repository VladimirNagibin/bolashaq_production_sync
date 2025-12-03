from typing import Annotated

from fastapi import APIRouter, Depends, Query

from services.deals.deal_services import DealClient
from services.dependencies.dependencies import (
    get_deal_service,
)
from services.dependencies.dependencies_repo import request_context

from ..decorators.webhook_decorators import (
    RESPONSES_WEBHOOK,
    handle_deal_webhook_logic,
)
from ..deps import get_deal_webhook_context, verify_incoming_webhook_token
from ..schemas.params import CommonWebhookParams

deals_webhook_router = APIRouter(
    prefix="/deals-webhook",
    dependencies=[
        Depends(request_context),
        Depends(verify_incoming_webhook_token),
    ],
)


@deals_webhook_router.post(
    "/deals-without-offer",
    summary="Handel deals without offer",
    description="Set fields and move deals without offer.",
    responses=RESPONSES_WEBHOOK,
)  # type: ignore
@handle_deal_webhook_logic
async def deals_without_offer(
    common_params: Annotated[
        tuple[CommonWebhookParams, DealClient],
        Depends(get_deal_webhook_context),
    ],
    # user_id: Annotated[
    #     str, Query(..., description="ID пользователя из шаблона")
    # ],
    # deal_id: Annotated[str, Query(..., description="ID сделки")],
    # deal_client: DealClient = Depends(get_deal_service),
) -> None:
    """
    Обрабатывает сделку, для которой создаётся КП.
    """
    params, deal_client = common_params
    await deal_client.handle_deal_without_offer(
        user_id=params.user_id, deal_id=params.deal_id
    )


@deals_webhook_router.post(
    "/deals-set-products-string-field",
    summary="Set deals products in string field",
    description="Set deals products in string field.",
    responses=RESPONSES_WEBHOOK,
)  # type: ignore
@handle_deal_webhook_logic
async def deals_set_products_string_field(
    user_id: Annotated[
        str, Query(..., description="ID пользователя из шаблона")
    ],
    deal_id: Annotated[str, Query(..., description="ID сделки")],
    products: Annotated[str, Query(..., description="Список продуктов")],
    products_origin: Annotated[
        str, Query(..., description="Оригинальный список продуктов")
    ],
    deal_client: DealClient = Depends(get_deal_service),
) -> None:
    """
    Устанавливает список продуктов в текстовое поле сделки.
    """
    await deal_client.set_products_string_field(
        user_id, deal_id, products, products_origin
    )


@deals_webhook_router.post(
    "/deal-set-stage-status",
    summary="Set stage and status deals",
    description="Set stage and status deals.",
    responses=RESPONSES_WEBHOOK,
)  # type: ignore
@handle_deal_webhook_logic
async def deals_set_stage_status(
    deal_id: Annotated[str, Query(..., description="ID сделки")],
    deal_stage: Annotated[int, Query(..., description="Стадия сделки")],
    deal_status: Annotated[str, Query(..., description="Статус сделки")],
    user_id: Annotated[
        str | None, Query(..., description="ID пользователя из шаблона")
    ] = None,
    deal_client: DealClient = Depends(get_deal_service),
) -> None:
    """
    Устанавливает этап и статус сделки.
    """
    await deal_client.set_stage_status_deal(deal_id, deal_stage, deal_status)
