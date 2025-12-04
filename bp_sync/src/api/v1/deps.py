from datetime import date, datetime
from typing import Annotated

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import APIKeyHeader

from core.settings import settings
from services.deals.deal_services import DealClient
from services.dependencies.dependencies import get_deal_service

from .schemas.params import CommonWebhookParams

API_KEY_NAME = "X-API-Key"
API_KEY = settings.BITRIX_CLIENT_SECRET

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


async def verify_api_key(api_key: str = Depends(api_key_header)) -> str:
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid API Key: {api_key[:3]}...",
        )
    return api_key


async def verify_incoming_webhook_token(key: str) -> None:
    if key != settings.WEB_HOOK_TOKEN_INCOMING:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid incoming webhook token: {key[:3]}...",
        )


async def get_common_webhook_params(
    user_id: Annotated[str, Query(...)],
    deal_id: Annotated[int, Query(...)],
) -> CommonWebhookParams:
    """
    Зависимость для получения общих параметров вебхука.
    """
    return CommonWebhookParams(user_id=user_id, deal_id=deal_id)


def get_deal_webhook_context(
    common_params: Annotated[
        CommonWebhookParams, Depends(get_common_webhook_params)
    ],
    deal_client: DealClient = Depends(get_deal_service),
) -> tuple[CommonWebhookParams, DealClient]:
    """
    Комбинированная зависимость, возвращающая общие параметры и клиент.
    """
    return common_params, deal_client


def parse_custom_date(
    date_str: Annotated[
        str, Query(..., description="Дата в формате дд.мм.гггг")
    ],
) -> date:
    """
    Парсит дату из формата дд.мм.гггг в объект date.
    """
    try:
        return datetime.strptime(date_str, "%d.%m.%Y").date()
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Неверный формат даты: {date_str}. "
                "Ожидается формат: дд.мм.гггг (например, 18.12.2025)"
            ),
        )
