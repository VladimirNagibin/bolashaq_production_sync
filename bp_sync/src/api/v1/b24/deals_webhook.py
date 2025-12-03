from typing import Annotated

from fastapi import APIRouter, Depends, Query

from services.deals.deal_services import DealClient
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
) -> None:
    """
    Обрабатывает сделку, для которой не создаётся КП.
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
    common_params: Annotated[
        tuple[CommonWebhookParams, DealClient],
        Depends(get_deal_webhook_context),
    ],
    products: Annotated[str, Query(..., description="Список продуктов")],
    products_origin: Annotated[
        str, Query(..., description="Оригинальный список продуктов")
    ],
) -> None:
    """
    Устанавливает список продуктов в текстовое поле сделки.
    """
    params, deal_client = common_params
    await deal_client.set_products_string_field(
        params.user_id, params.deal_id, products, products_origin
    )


@deals_webhook_router.post(
    "/deal-set-stage-status",
    summary="Set stage and status deals",
    description="Set stage and status deals.",
    responses=RESPONSES_WEBHOOK,
)  # type: ignore
@handle_deal_webhook_logic
async def deals_set_stage_status(
    common_params: Annotated[
        tuple[CommonWebhookParams, DealClient],
        Depends(get_deal_webhook_context),
    ],
    deal_stage: Annotated[int, Query(..., description="Стадия сделки")],
    deal_status: Annotated[str, Query(..., description="Статус сделки")],
    doc_update: Annotated[
        int | None,
        Query(
            ..., description="Флаг обновления изображения(1-обновление, 0-нет)"
        ),
    ] = None,
    doc_id: Annotated[
        int | None, Query(..., description="Ссылка на изображение")
    ] = None,
) -> None:
    """
    Устанавливает этап и статус сделки.
    """
    params, deal_client = common_params
    await deal_client.set_stage_status_deal(
        params.deal_id,
        deal_stage,
        deal_status,
        doc_update=doc_update,
        doc_id=doc_id,
    )
