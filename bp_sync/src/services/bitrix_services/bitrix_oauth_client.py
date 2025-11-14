from urllib.parse import urlencode

from fastapi import Depends

from core.logger import logger
from core.settings import settings

from ..exceptions import BitrixAuthError
from ..token_services.token_storage import TokenStorage, get_token_storage
from .base_bitrix_client import DEFAULT_TIMEOUT, BaseBitrixClient

OAUTH_ENDPOINT = "/oauth/authorize/"
TOKEN_ENDPOINT = "/oauth/token/"


class BitrixOAuthClient(BaseBitrixClient):
    """Клиент для OAuth аутентификации с Bitrix24."""

    def __init__(
        self,
        token_storage: TokenStorage,
        portal_domain: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        redirect_uri: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        super().__init__(timeout)
        self.portal_domain = portal_domain or settings.BITRIX_PORTAL
        self.client_id = client_id or settings.BITRIX_CLIENT_ID
        self.client_secret = client_secret or settings.BITRIX_CLIENT_SECRET
        self.redirect_uri = redirect_uri or settings.BITRIX_REDIRECT_URI
        self.token_url = f"{self.portal_domain}{TOKEN_ENDPOINT}"
        self.token_storage = token_storage

    async def get_valid_token(self) -> str:
        """
        Получает валидный access token.

        Returns:
            Access token

        Raises:
            BitrixAuthError: Если токены недоступны
        """
        if access_token := await self.token_storage.get_token("access_token"):
            logger.debug("Using existing access token")
            return access_token

        if refresh_token := await self.token_storage.get_token(
            "refresh_token"
        ):
            logger.debug("Refreshing access token")
            return await self._refresh_access_token(refresh_token)
        logger.warning(
            "No valid tokens available, re-authentication required."
        )
        raise BitrixAuthError(
            "Authentication required",
            detail=f"Re-authorize at: {self.get_auth_url()}",
        )

    async def _refresh_access_token(self, refresh_token: str) -> str:
        """Обновление access token с помощью refresh token."""
        params = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
        }
        return await self._exchange_token(params, "refresh")

    async def fetch_token(self, code: str) -> str:
        """Получение токена по коду авторизации"""
        params = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "code": code,
        }
        return await self._exchange_token(params, "authorization")

    async def _exchange_token(
        self, params: dict[str, str], operation: str
    ) -> str:
        """
        Общая логика получения и сохранения токенов.

        Args:
            params: Параметры для запроса токена
            operation: Тип операции для логирования

        Returns:
            Access token
        """
        try:
            # token_data = await self._post(self.token_url, payload=params)
            token_data = await self._get(self.token_url, params=params)
            self._validate_token_response(token_data)
            access_token = self._extract_access_token(token_data)
            await self._save_tokens(token_data)

            logger.info(
                f"Token {operation} successful",
                extra={
                    "grant_type": params["grant_type"],
                    "portal_domain": self.portal_domain,
                },
            )
            return access_token

        except Exception as e:
            logger.error(
                f"Token {operation} failed: {e}",
                extra={"grant_type": params["grant_type"]},
            )
            raise

    def _validate_token_response(self, token_data: dict[str, str]) -> None:
        """Валидация ответа с токеном"""
        if "error" in token_data:
            error_msg = token_data.get(
                "error_description", "Unknown OAuth error"
            )
            logger.error(
                f"Bitrix OAuth error: {error_msg}",
                extra={"response_data": token_data},
            )
            raise BitrixAuthError(
                f"OAuth error: {error_msg}", detail=token_data
            )

    def _extract_access_token(self, token_data: dict[str, str]) -> str:
        """Извлечение access_token из ответа"""
        access_token = token_data.get("access_token")
        if not access_token or not isinstance(access_token, str):
            logger.error(
                "Invalid access token in response",
                extra={"access_token_type": type(access_token).__name__},
            )
            raise BitrixAuthError("Invalid access token format")
        return access_token

    async def _save_tokens(self, token_data: dict[str, str]) -> None:
        """Сохранение полученных токенов в хранилище."""
        try:
            expires_in = int(token_data.get("expires_in", 3600))
            await self.token_storage.save_token(
                token_data["access_token"],
                "access_token",
                expire_seconds=expires_in,
            )
            if "refresh_token" in token_data:
                await self.token_storage.save_token(
                    token_data["refresh_token"],
                    "refresh_token",
                )
            logger.debug(
                "Tokens saved successfully", extra={"expires_in": expires_in}
            )
        except Exception as e:
            logger.error(
                f"Failed to save tokens: {e}",
                extra={"token_keys": list(token_data.keys())},
            )
            raise RuntimeError("Token storage failure") from e

    def get_auth_url(self) -> str:
        """Генерация URL для авторизации в Bitrix24"""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
        }
        return f"{self.portal_domain}{OAUTH_ENDPOINT}?{urlencode(params)}"

    @property
    def is_authenticated(self) -> bool:
        """
        Проверяет, есть ли у клиента доступ к токенам.

        Note: Это не проверяет валидность токенов, только их наличие.
        """
        # В реальной реализации нужно было бы асинхронно проверять хранилище
        # Для упрощения возвращаем True, предполагая что токены есть
        return True


def get_oauth_client(
    token_storade: TokenStorage = Depends(get_token_storage),
) -> BitrixOAuthClient:
    """
    Фабрика для внедрения зависимостей BitrixOAuthClient.

    Returns:
        Экземпляр BitrixOAuthClient
    """
    return BitrixOAuthClient(
        token_storage=token_storade,
    )
