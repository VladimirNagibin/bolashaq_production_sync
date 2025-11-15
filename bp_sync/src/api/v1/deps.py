from fastapi import Depends, HTTPException, status  # APIRouter
from fastapi.security import APIKeyHeader

from core.settings import settings

# from services.dependencies import request_context

# upload_codes_router = APIRouter(dependencies=[Depends(request_context)])

API_KEY_NAME = "X-API-Key"
API_KEY = settings.BITRIX_CLIENT_SECRET  # "your-api-key-here"

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


async def verify_api_key(api_key: str = Depends(api_key_header)) -> str:
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    return api_key
