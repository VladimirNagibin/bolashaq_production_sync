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
from ..exceptions import BitrixApiError, ProductTransformationError
from ..file_download_service import FileDownloadService
from .product_transformation_service import ProductTransformationService


class ProductBitrixClient(
    BaseBitrixEntityClient[ProductCreate, ProductUpdate]
):
    entity_name = "product"  # "catalog.product" crm = False
    create_schema = ProductCreate
    update_schema = ProductUpdate

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.file_download_service = FileDownloadService()
        self.transformation_service = ProductTransformationService(
            file_download_service=self.file_download_service
        )

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
        return await self.get(entity_id=product_id)  # , crm=False)

    @handle_bitrix_errors()
    async def set_entity_products(
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
                await self.set_entity_products(
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

    async def transform_product_fields(self, product_id: int) -> bool:
        """
        Преобразование полей товара

        Args:
            product_id: ID товара в Битрикс24

        Returns:
            bool: Успешность преобразования
        """
        try:
            logger.info(
                f"Starting field transformation for product {product_id}"
            )

            # Получаем данные товара
            product_data = await self.get(product_id)
            product_data_dict = await self._get_product_data(product_id)
            if not product_data or not product_data_dict:
                logger.error(f"Product {product_id} not found or empty result")
                return False

            text_fields, image_fields = (
                await self.transformation_service.transform_product_fields(
                    product_data=product_data,
                    product_id=product_id,
                    product_data_dict=product_data_dict,
                )
            )

            # Обновляем текстовые поля
            if text_fields:
                logger.info(
                    f"Updating {len(text_fields)} text fields for product "
                    f"{product_id}"
                )
                text_fields["external_id"] = product_id
                product_update = ProductUpdate(**text_fields)
                await self.update(product_update)

            # Обновляем изображение
            if image_fields:
                logger.info(f"Updating image for product {product_id}")
                success = await self._update_product(product_id, image_fields)
                if not success:
                    logger.error(
                        f"Failed to update image for product {product_id}"
                    )
                    return False

            if not text_fields and not image_fields:
                logger.info(f"No fields to update for product {product_id}")

            logger.info(f"Successfully transformed product {product_id}")
            return True

        except ProductTransformationError as e:
            logger.error(f"Transformation error for product {product_id}: {e}")
            return False
        except Exception as e:
            logger.error(
                f"Unexpected error transforming product {product_id}: {e}",
                exc_info=True,
            )
            return False

    async def _get_product_data(
        self, product_id: int
    ) -> dict[str, Any] | None:
        """Получение данных товара по ID"""
        try:
            result = await self.bitrix_client.call_api(
                "crm.product.get", {"id": product_id}
            )
            if result:
                return result.get("result", None)  # type:ignore[no-any-return]
            return None
        except Exception as e:
            logger.error(f"Error getting product {product_id} data: {str(e)}")
            return None

    async def _update_product(
        self, product_id: int, fields: dict[str, Any]
    ) -> bool:
        """
        Обновление товара в Битрикс24

        Args:
            product_id: ID товара
            fields: Поля для обновления

        Returns:
            bool: Успешность обновления
        """
        try:
            logger.debug(
                f"Updating product {product_id} with fields: "
                f"{list(fields.keys())}"
            )
            payload: dict[str, Any] = {"id": product_id, "fields": fields}

            response = await self.bitrix_client.call_api(
                "crm.product.update", payload
            )

            if response.get("result"):
                logger.debug(f"Successfully updated product {product_id}")
                return True
            else:
                logger.error(
                    "Bitrix API error updating product "
                    f"{product_id}: {response}"
                )
                return False

        except Exception as e:
            logger.error(f"Error updating product {product_id}: {str(e)}")
            return False
