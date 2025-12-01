from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from core.settings import settings

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
