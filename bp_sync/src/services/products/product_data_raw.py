from typing import Any

from core.logger import logger

from ..bitrix_services.bitrix_api_client import BitrixAPIClient


class ProductRawDataService:
    """
    Сервис для низкоуровневой работы с сырыми данными товаров в Bitrix

    Отвечает за:
    - Прямое получение данных товара из API
    - Прямое обновление полей товара
    - Не содержит бизнес-логики, только CRUD операции
    """

    def __init__(self, bitrix_client: BitrixAPIClient):
        self.bitrix_client = bitrix_client

    async def get(self, product_id: int) -> dict[str, Any] | None:
        """
        Получение сырых данных товара по ID

        Returns:
            dict: Сырые данные из Bitrix API или None при ошибке
        """
        return await self.call_api("crm.product.get", {"id": product_id})

    async def update(self, product_id: int, fields: dict[str, Any]) -> bool:
        """
        Обновление сырых полей товара

        Args:
            product_id: ID товара
            fields: Словарь полей для обновления

        Returns:
            bool: Успешность обновления
        """
        response = await self.call_api(
            "crm.product.update", {"id": product_id, "fields": fields}
        )
        if response:
            logger.info(
                f"Successfully updated raw data for product {product_id}"
            )
            return True
        return False

    async def get_field(self, product_id: int, field_name: str) -> Any:
        """Получение конкретного поля товара"""
        data = await self.get(product_id)
        if data:
            return data.get(field_name)
        return None

    async def update_field(
        self, product_id: int, field_name: str, value: Any
    ) -> bool:
        """Обновление конкретного поля товара"""
        return await self.update(product_id, {field_name: value})

    async def call_api(
        self, method: str, params: dict[str, Any]
    ) -> dict[str, Any] | None:
        """
        Отправка запроса к API

        Returns:
            dict: Сырые данные из Bitrix API или None при ошибке
        """
        try:
            logger.debug(
                f"Start request {method}, params: {list(params.keys())}"
            )

            response = await self.bitrix_client.call_api(method, params)

            if response and "result" in response:
                return response["result"]  # type: ignore[no-any-return]

            error_msg = (
                response.get("error_description", "Unknown error")
                if response
                else "No response"
            )
            logger.warning(
                f"FaiFailedl request {method}, params {params}: {error_msg}"
            )
            return None

        except Exception as e:
            logger.error(
                f"Error request {method}, params: {params}: {e}", exc_info=True
            )
            return None
