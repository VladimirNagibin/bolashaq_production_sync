from http import HTTPStatus
from typing import Any

import aiohttp

from core.logger import logger
from core.settings import settings

TIMEOUT = 30


class SiteRequestService:
    """Сервис для работы с внешним API сайта."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: int = TIMEOUT,
    ):
        """
        Args:
            base_url: Базовый URL API
            api_key: Ключ API (опционально)
            timeout: Таймаут запросов в секундах
        """
        self.base_url = base_url or settings.SITE_API_BASE_URL
        self.api_key = api_key or settings.SITE_API_KEY
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> "SiteRequestService":
        """Контекстный менеджер."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):  # type: ignore
        """Закрытие контекста."""
        await self.close()

    async def _ensure_session(self) -> None:
        """Создает сессию, если она не существует."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=self.timeout)

    async def close(self) -> None:
        """Закрывает сессию"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    async def send_request(
        self,
        endpoint: str,
        params: dict[str, Any],
    ) -> tuple[bool, dict[str, Any] | None]:
        """
        Отправляет GET запрос к API.

        Args:
            endpoint: Эндпоинт API
            params: Параметры запроса

        Returns:
            Кортеж (успех, данные ответа)
        """
        await self._ensure_session()

        if not self.session:
            logger.error("Сессия не инициализирована")
            return False, None

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:

            # Добавляем API ключ если есть
            # if self.api_key:
            #    params['api_key'] = self.api_key

            logger.info(f"Отправка запроса к {url} с параметрами: {params}")

            async with self.session.get(url, params=params) as response:
                response_text = await response.text()

                if response.status == HTTPStatus.OK:
                    try:
                        result = await response.json()
                        success = result.get("success", False)

                        if success:
                            logger.info(f"Запрос успешно обработан: {result}")
                        else:
                            logger.warning(
                                f"Запрос завершился с ошибкой: {result}"
                            )

                        return success, result
                    except ValueError as e:
                        logger.error(f"Ошибка парсинга JSON ответа: {e}")
                        return False, None
                else:
                    logger.error(
                        f"HTTP ошибка {response.status}: {response_text}"
                    )
                    return False, None

        except aiohttp.ClientError as e:
            logger.error(f"Сетевая ошибка при отправке запроса: {e}")
            return False, None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при отправке запроса: {e}")
            return False, None
