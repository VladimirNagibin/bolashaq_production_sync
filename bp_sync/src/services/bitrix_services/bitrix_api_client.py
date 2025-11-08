from typing import Any
from urllib.parse import urljoin

from fastapi import status

from core.logger import logger

from ..exceptions import BitrixApiError, BitrixAuthError
from .base_bitrix_client import DEFAULT_TIMEOUT, BaseBitrixClient
from .bitrix_oauth_client import BitrixOAuthClient

MAX_RETRIES = 2
REST_API_BASE = "/rest/"
TOKEN_ERRORS = {"expired_token", "invalid_token"}


class BitrixAPIClient(BaseBitrixClient):
    """Клиент для работы с Bitrix24 REST API."""

    def __init__(
        self,
        oauth_client: BitrixOAuthClient,
        api_base_url: str = "",
        max_retries: int = MAX_RETRIES,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        super().__init__(timeout)
        self.oauth_client = oauth_client
        self.api_base_url = (
            api_base_url or f"{oauth_client.portal_domain}{REST_API_BASE}"
        )
        self.max_retries = max_retries

    async def call_api(
        self, method: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Вызывает метод Bitrix24 API.

        Args:
            method: API метод (например 'crm.deal.list')
            params: Параметры запроса

        Returns:
            Ответ API

        Raises:
            BitrixAuthError: Ошибки аутентификации
            BitrixApiError: Ошибки API
        """
        attempt = 0

        while attempt <= self.max_retries:
            attempt += 1
            try:
                access_token = await self.oauth_client.get_valid_token()
                url = urljoin(self.api_base_url, method)
                payload = {"auth": access_token}
                if params:
                    payload.update(params)

                response = await self._post(url, payload)

                if "error" in response:
                    self._handle_api_error(response, attempt)

                if response.get("result") is not None:
                    return response
                logger.error(
                    "API response has no result",
                    extra={"method": method, "attempt": attempt},
                )
                raise BitrixApiError(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    error="missing_result",
                    error_description="API response has no result",
                )
            except BitrixAuthError as e:
                logger.warning(
                    f"Authentication error on attempt {attempt}: {e}",
                    extra={"method": method, "attempt": attempt},
                )
                if attempt > self.max_retries:
                    logger.error(
                        "Max authentication retries exceeded",
                        extra={
                            "method": method,
                            "max_retries": self.max_retries,
                        },
                    )
                    raise
                continue
        logger.error(
            "Unexpected exit from API call loop",
            extra={"method": method, "attempt": attempt},
        )
        raise BitrixAuthError("Token refresh failed after retries")

    def _handle_api_error(
        self, response: dict[str, Any], attempt: int
    ) -> None:
        """
        Обрабатывает ошибки API.

        Args:
            response: Ответ API с ошибкой
            attempt: Номер текущей попытки

        Raises:
            BitrixAuthError: Для ошибок токена
            BitrixApiError: Для других ошибок API
        """
        error_code = response.get("error", "unknown_error")
        error_desc = response.get(
            "error_description", "Unknown Bitrix API error"
        )
        if error_code in TOKEN_ERRORS and attempt <= self.max_retries:
            logger.warning(
                (
                    f"Token error detected, retrying "
                    f"(attempt {attempt}/{self.max_retries})"
                ),
                extra={"error_code": error_code},
            )
            self._invalidate_current_token()
            raise BitrixAuthError(f"Token invalid or expired: {error_code}")

        logger.error(
            f"Bitrix API error: {error_code} - {error_desc}",
            extra={
                "error_code": error_code,
                "error_description": error_desc,
                "status_code": response.get("status_code"),
            },
        )
        raise BitrixApiError(
            status_code=response.get(
                "status_code", status.HTTP_400_BAD_REQUEST
            ),
            error=error_code,
            error_description=error_desc,
        )

    def _invalidate_current_token(self) -> None:
        """Инвалидация текущего access token"""
        try:
            import asyncio

            asyncio.create_task(
                self.oauth_client.token_storage.delete_token("access_token")
            )
            logger.debug("Access token invalidation scheduled")
        except Exception as e:
            logger.warning(f"Failed to invalidate token: {e}")
