from typing import Any

from fastapi import status

from core.logger import logger
from schemas.enums import EntityTypeAbbr
from schemas.product_schemas import (  # ProductEntityCreate,
    ListProductEntity,
    ProductCreate,
    ProductUpdate,
)

from ..bitrix_services.base_bitrix_services import BaseBitrixEntityClient
from ..decorators import handle_bitrix_errors
from ..exceptions import BitrixApiError


class ProductBitrixClient(
    BaseBitrixEntityClient[ProductCreate, ProductUpdate]
):
    entity_name = "product"  # "catalog.product" crm = False
    create_schema = ProductCreate
    update_schema = ProductUpdate

    @handle_bitrix_errors()
    async def get_entity_products(
        self,
        owner_id: int,
        owner_type: EntityTypeAbbr,
    ) -> ListProductEntity:
        """Получение товаров в сущности по ID"""
        logger.debug(
            f"Fetching products of owner type:{owner_type} ID={owner_id}"
        )
        params: dict[str, Any] = {
            "filter": {
                "=ownerType": owner_type.value,
                "=ownerId": owner_id,
            }
        }
        response = await self.bitrix_client.call_api(
            "crm.item.productrow.list",
            params=params,
        )
        if (
            not (entity_data := response.get("result"))
            or "productRows" not in entity_data
        ):
            logger.warning(
                f"Products not found for {owner_type} ID={owner_id}"
            )
            return ListProductEntity(result=[])
        return ListProductEntity(result=entity_data["productRows"])

    async def _get_product_catalog(self, product_id: int) -> ProductCreate:
        """Получение каталога товара"""
        return await self.get(entity_id=product_id, crm=False)

    @handle_bitrix_errors()
    async def _set_product_rows(
        self,
        owner_id: int,
        owner_type: EntityTypeAbbr,
        products: ListProductEntity,
    ) -> ListProductEntity:
        """
        Устанавливает товарные позиции в сущность CRM.
        Перезаписывает все существующие товарные позиции.

        Args:
            owner_id: Идентификатор объекта CRM
            owner_type: Краткий символьный код типа объекта CRM
            products: Список товарных позиций для установки

        Returns:
            Ответ от Bitrix24 API
        """
        logger.debug(f"Setting products of {owner_type} ID={owner_id}")
        # Формируем параметры запроса
        params: dict[str, Any] = {
            "ownerId": owner_id,
            "ownerType": owner_type.value,
            "productRows": products.to_bitrix_dict(),
        }
        response = await self.bitrix_client.call_api(
            "crm.item.productrow.set", params=params
        )

        # Проверяем ответ
        if (
            not (entity_data := response.get("result"))
            or "productRows" not in entity_data
        ):
            logger.error(
                f"Failed to set product rows for owner type:{owner_type} "
                f"ID={owner_id}"
            )
            raise BitrixApiError(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error_description=(
                    f"Failed to set product rows for owner type:{owner_type} "
                    f"ID={owner_id}"
                ),
            )
        return ListProductEntity(result=entity_data["productRows"])

    async def update_deal_product_from_invoice(
        self, deal_id: int, invoice_id: int
    ) -> bool:
        """
        Проверяет и обновляет товары в сделке из счёта.

        Args:
            deal_id: ID сделки
            invoice_id: ID счёта

        Returns:
            bool
        """
        try:
            deal_products = await self.get_entity_products(
                deal_id, EntityTypeAbbr.DEAL
            )
            invoice_products = await self.get_entity_products(
                invoice_id, EntityTypeAbbr.INVOICE
            )
            if not deal_products.equals_ignore_owner(invoice_products):
                logger.info(
                    f"Products not equals deal:{deal_id}, invoice:{invoice_id}"
                )
                await self._set_product_rows(
                    deal_id, EntityTypeAbbr.DEAL, invoice_products
                )
            logger.info(
                f"Successfully updated products for deal:{deal_id} "
                f"from invoice:{invoice_id}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Error updating products deal:{deal_id}, "
                f"invoice:{invoice_id}. Error: {str(e)}"
            )
            return False
