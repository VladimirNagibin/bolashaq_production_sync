from datetime import date, datetime
from typing import Annotated, Any

from fastapi import Depends, HTTPException, Query, Request, status
from fastapi.security import APIKeyHeader

from core.settings import settings
from services.deals.deal_services import DealClient
from services.dependencies.dependencies import get_deal_service
from services.users_auth.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
)

from .schemas.params import CommonWebhookParams
from .schemas.response_schemas import TokenData

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
        str | None, Query(..., description="Дата в формате дд.мм.гггг")
    ] = None,
) -> date | None:
    """
    Парсит дату из формата дд.мм.гггг в объект date.
    """
    if not date_str:
        return None
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


async def get_current_user_from_cookie(
    request: Request,
) -> tuple[TokenData, dict[str, Any] | None]:
    """
    Проверяет Access Token. Если истек — пробует обновить через Refresh Token.
    """
    # 1. Пытаемся получить пользователя из Access Token
    access_token = request.cookies.get("access_token")

    if access_token:
        try:
            payload = decode_token(access_token)
            if payload and payload.get("type") == "access":
                token_role = payload.get("role")
                token_user_bitrix_id = payload.get("user_bitrix_id")
                if token_role and token_user_bitrix_id:
                    return (
                        TokenData(
                            role=str(token_role),
                            user_bitrix_id=int(token_user_bitrix_id),
                        ),
                        None,
                    )
        except Exception:
            # Токен истек или невалиден. Падаем ниже на попытку обновления.
            pass

    # 2. Если пользователь не найден через Access Token, пробуем Refresh Token

    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        # Нет токенов — редирект на логин
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/api/v1/auth/login"},
            detail="Refresh token missing",
        )

    try:
        payload = decode_token(refresh_token)
        if not payload or (payload and payload.get("type") != "refresh"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        token_user_id = payload.get("sub")
        token_role = payload.get("role")
        token_user_bitrix_id = payload.get("user_bitrix_id")
        if not token_user_id or not token_role or not token_user_bitrix_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        # 3. ПОЛУЧИЛИ НОВОГО ПОЛЬЗОВАТЕЛЯ ЧЕРЕЗ REFRESH.
        # Генерируем НОВУЮ пару токенов
        # (Refresh Token Rotation - рекомендованная практика)
        data: dict[str, Any] = {
            "sub": str(token_user_id),
            "role": str(token_role),
            "user_bitrix_id": int(token_user_bitrix_id),
        }
        new_access_token = create_access_token(data=data)
        new_refresh_token = create_refresh_token(data=data)

        new_cookies = {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
        }

        return (
            TokenData(
                role=str(token_role), user_bitrix_id=int(token_user_bitrix_id)
            ),
            new_cookies,
        )
    except Exception:
        # Refresh токен тоже невалиден — редирект на логин
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/api/v1/auth/login"},
            detail="Could not validate credentials",
        )
