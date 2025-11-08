from typing import Any, cast

import httpx
from fastapi import status

from core.logger import logger

from ..exceptions import BitrixApiError, BitrixAuthError

DEFAULT_TIMEOUT = 10.0
JsonResponse = dict[str, Any]


class BaseBitrixClient:
    """Базовый клиент для HTTP-запросов к Bitrix24 API."""

    def __init__(self, timeout: float = DEFAULT_TIMEOUT):
        self.timeout = timeout

    async def _process_response(
        self, response: httpx.Response
    ) -> JsonResponse:
        """
        Обрабатывает HTTP-ответ и преобразует в JSON.

        Args:
            response: Ответ от сервера

        Returns:
            JSON-ответ в виде словаря

        Raises:
            ValueError: Если ответ не является валидным JSON объектом
        """
        try:
            json_data = response.json()
            if not isinstance(json_data, dict):
                raise ValueError(
                    f"Expected JSON object, got {type(json_data).__name__}"
                )
            return cast(JsonResponse, json_data)
        except ValueError as e:
            logger.error(f"Invalid JSON response: {e}")
            raise

    async def _get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> JsonResponse:
        """
        Выполняет GET-запрос к API.

        Args:
            url: URL для запроса
            params: Параметры запроса
            headers: HTTP-заголовки

        Returns:
            JSON-ответ

        Raises:
            BitrixAuthError: Ошибки аутентификации и сетевые ошибки
            BitrixApiError: Неожиданные ошибки
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url, params=params, headers=headers or {}
                )
                return await self._process_response(response)
        except httpx.HTTPStatusError as e:
            detail = e.response.json().get("error_description", str(e))
            logger.error(
                f"HTTP error {e.response.status_code}: {detail}",
                extra={"url": url, "status_code": e.response.status_code},
            )
            raise BitrixAuthError(
                f"HTTP error {e.response.status_code}", detail=detail
            ) from e
        except httpx.RequestError as e:
            logger.error(f"Network error: {e}", extra={"url": url})
            raise BitrixAuthError("Network error during request") from e
        except Exception as e:
            logger.error(
                f"Unexpected error in GET request: {e}", extra={"url": url}
            )
            raise BitrixApiError(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="unexpected_error",
                error_description="Unexpected error during GET request",
            ) from e

    async def _post(
        self,
        url: str,
        payload: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> JsonResponse:
        """
        Выполняет POST-запрос к API.

        Args:
            url: URL для запроса
            payload: Данные для отправки
            headers: HTTP-заголовки

        Returns:
            JSON-ответ со статус-кодом

        Raises:
            BitrixApiError: Ошибки API и сетевые ошибки
        """
        try:
            request_headers = {"Content-Type": "application/json"}
            if headers:
                request_headers.update(headers)

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=request_headers,
                )
                json_data = await self._process_response(response)
                json_data["status_code"] = response.status_code
                return json_data

        except httpx.HTTPStatusError as e:
            logger.error(
                f"API HTTP error {e.response.status_code}: {e.response.text}",
                extra={"url": url, "status_code": e.response.status_code},
            )
            raise BitrixApiError(
                status_code=e.response.status_code,
                error="http_error",
                error_description=f"Bitrix API error: {e.response.text}",
            ) from e
        except httpx.RequestError as e:
            logger.error(f"Network error: {e}", extra={"url": url})
            raise BitrixApiError(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                error="network_error",
                error_description="Unable to connect to Bitrix24",
            ) from e
        except Exception as e:
            logger.error(
                f"Unexpected error in POST request: {e}", extra={"url": url}
            )
            raise BitrixApiError(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="unexpected_error",
                error_description="Unexpected error during POST request",
            ) from e
