from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from core.logger import logger
from services.bitrix_services.bitrix_oauth_client import (
    BitrixOAuthClient,
    get_oauth_client,
)
from services.exceptions import BitrixAuthError

auth_router = APIRouter()


@auth_router.get(
    "/auth/callback", summary="OAuth 2.0 Callback Handler"
)  # type: ignore
async def handle_auth_callback(
    code: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
    oauth_client: BitrixOAuthClient = Depends(get_oauth_client),
) -> JSONResponse:
    """
    Handle Bitrix24 OAuth 2.0 callback

    Processes authorization code or error returned from Bitrix24 OAuth server.
    """
    if error or error_description:
        error_msg = error_description or error or "Unknown OAuth error"
        logger.error(f"OAuth callback error: {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg
        )

    if not code:
        logger.warning(
            "Authorization callback received without code parameter"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code is required",
        )
    try:
        # Обмен кода на токены
        access_token = await oauth_client.fetch_token(code)
        logger.info("Successfully obtained access token from Bitrix24")

        # Формирование успешного ответа (без передачи самого токена)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": "Authentication completed successfully",
                "access_token_obtained": bool(access_token),
            },
        )

    except BitrixAuthError as auth_error:
        logger.error(f"Authentication failed: {str(auth_error)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(auth_error)
        )

    except Exception as e:
        logger.exception(f"Unexpected error during token exchange: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during authentication: {str(e)}",
        )
