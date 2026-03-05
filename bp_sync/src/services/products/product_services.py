from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from core.logger import logger
from core.settings import settings
from models.product_models import Product as ProductDB
from schemas.enums import EntityTypeAbbr
from schemas.product_schemas import ListProductEntity, ProductEntityCreate
from services.users.user_services import UserClient

from ..base_services.base_service import BaseEntityClient
from ..exceptions import BitrixApiError, ConflictException, CyclicCallException
from .product_bitrix_services import (
    ProductBitrixClient,
)
from .product_repository import ProductRepository


class ProductClient(
    BaseEntityClient[
        ProductDB,
        ProductRepository,
        ProductBitrixClient,
    ]
):
    def __init__(
        self,
        product_bitrix_client: ProductBitrixClient,
        product_repo: ProductRepository,
        user_client: UserClient | None = None,
    ):
        super().__init__()
        self._bitrix_client = product_bitrix_client
        self._repo = product_repo

        if user_client is not None:
            self._repo.set_user_client(user_client)

    @property
    def entity_name(self) -> str:
        return "product"

    @property
    def bitrix_client(self) -> ProductBitrixClient:
        return self._bitrix_client

    @property
    def repo(self) -> ProductRepository:
        return self._repo

    @property
    def webhook_config(self) -> dict[str, Any]:
        return settings.web_hook_config_product  # type: ignore

    async def load_products_entity_from_bitrix(
        self,
        owner_id: int,
        owner_type: EntityTypeAbbr = EntityTypeAbbr.DEAL,
    ) -> None:
        """
        Синхронизирует товары сущности из Битрикс24 в локальную базу данных.
        Сравнивает товары в Битрикс и БД, добавляет новые/обновляет
        существующие и удаляет устаревшие.
        """
        logger.info(
            (
                f"Starting product sync from Bitrix for {owner_type.value} "
                f"ID={owner_id}"
            ),
            extra={"owner_id": owner_id, "owner_type": owner_type.value},
        )
        try:
            # 1. Получаем данные из Битрикс и локальной БД
            products_from_b24 = await self._fetch_products_from_bitrix(
                owner_id, owner_type
            )
            products_from_db = await self._fetch_products_from_db(
                owner_id, owner_type
            )

            # 2. Определяем, какие товары нужно синхронизировать и удалить
            b24_product_ids = {p.product_id for p in products_from_b24.result}
            db_product_ids = {p.product_id for p in products_from_db.result}

            # 3. Синхронизируем товары, пришедшие из Битрикс
            await self._sync_products_from_b24_to_db(
                products_from_b24.result, owner_id, owner_type
            )

            # 4. Удаляем товары, которых больше нет в Битрикс
            obsolete_product_ids = db_product_ids - b24_product_ids
            if obsolete_product_ids:
                await self._delete_obsolete_products_from_db(
                    obsolete_product_ids, owner_id, owner_type
                )

            logger.info(
                f"Successfully synced products for {owner_type.value} "
                f"ID={owner_id}. Processed: {len(products_from_b24.result)}, "
                "Deleted: {len(obsolete_product_ids)}",
                extra={
                    "owner_id": owner_id,
                    "owner_type": owner_type.value,
                    "processed_count": len(products_from_b24.result),
                    "deleted_count": len(obsolete_product_ids),
                },
            )
        except BitrixApiError as e:
            logger.error(
                (
                    "Bitrix API error during product sync for "
                    f"{owner_type.value} ID={owner_id}: {e.detail}"
                ),
                extra={"owner_id": owner_id, "owner_type": owner_type.value},
                exc_info=True,
            )
            raise
        except Exception as e:
            logger.exception(
                (
                    "An unexpected error occurred during product sync for "
                    f"{owner_type.value} ID={owner_id}"
                ),
                extra={"owner_id": owner_id, "owner_type": owner_type.value},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    f"Failed to sync products for {owner_type.value} "
                    f"ID={owner_id}"
                ),
            ) from e

    async def _fetch_products_from_bitrix(
        self, owner_id: int, owner_type: EntityTypeAbbr
    ) -> ListProductEntity:
        """
        Вспомогательный метод для получения товаров из Битрикс с логированием.
        """
        logger.debug(
            (
                f"Fetching products from Bitrix for {owner_type.value} "
                f"ID={owner_id}"
            ),
            extra={"owner_id": owner_id, "owner_type": owner_type.value},
        )
        return await self.bitrix_client.get_entity_products(
            owner_id, owner_type
        )

    async def _fetch_products_from_db(
        self, owner_id: int, owner_type: EntityTypeAbbr
    ) -> ListProductEntity:
        """
        Вспомогательный метод для получения товаров из локальной БД с
        логированием.
        """
        logger.debug(
            (
                f"Fetching products from local DB for {owner_type.value} "
                f"ID={owner_id}"
            ),
            extra={"owner_id": owner_id, "owner_type": owner_type.value},
        )
        return await self.repo.get_entity_products(owner_id, owner_type)

    async def _sync_products_from_b24_to_db(
        self,
        products_from_b24: list[ProductEntityCreate],
        owner_id: int,
        owner_type: EntityTypeAbbr,
    ) -> None:
        """
        Синхронизирует список товаров из Битрикс в БД.
        Для каждого товара сначала пытается импортировать сам товар, а затем
        создает/обновляет его связь с сущностью.
        """
        for product_entity_data in products_from_b24:
            try:
                # Убеждаемся, что сам товар существует в нашей БД
                await self.import_from_bitrix(product_entity_data.product_id)
                # Создаем или обновляем связь товара с сущностью
                await self.repo.create_or_update_product_in_entity(
                    product_entity_data
                )
                logger.debug(
                    (
                        f"Synced product {product_entity_data.product_id} for "
                        f"{owner_type.value} ID={owner_id}"
                    ),
                    extra={
                        "owner_id": owner_id,
                        "owner_type": owner_type.value,
                        "product_id": product_entity_data.product_id,
                    },
                )
            except (CyclicCallException, ConflictException) as e:
                # Эти ошибки ожидаемы и не являются сбоями синхронизации
                logger.warning(
                    (
                        "Could not sync product "
                        f"{product_entity_data.product_id} for "
                        f"{owner_type.value} ID={owner_id}: {e.detail}"
                    ),
                    extra={
                        "owner_id": owner_id,
                        "owner_type": owner_type.value,
                        "product_id": product_entity_data.product_id,
                    },
                )
            except Exception as e:
                logger.error(
                    (
                        "Failed to sync product "
                        f"{product_entity_data.product_id} for "
                        f"{owner_type.value} ID={owner_id}: {str(e)}"
                    ),
                    extra={
                        "owner_id": owner_id,
                        "owner_type": owner_type.value,
                        "product_id": product_entity_data.product_id,
                    },
                    exc_info=True,
                )
                # Решаем, прерывать ли всю синхронизацию из-за одного товара.
                # В данном случае, лучше логировать ошибку и продолжать.
                continue

    async def _delete_obsolete_products_from_db(
        self,
        product_ids_to_delete: set[int],
        owner_id: int,
        owner_type: EntityTypeAbbr,
    ) -> None:
        """Удаляет список устаревших товаров из сущности в локальной БД."""
        logger.info(
            (
                f"Deleting {len(product_ids_to_delete)} obsolete products for "
                f"{owner_type.value} ID={owner_id}"
            ),
            extra={
                "owner_id": owner_id,
                "owner_type": owner_type.value,
                "product_ids_to_delete": list(product_ids_to_delete),
            },
        )
        for product_id in product_ids_to_delete:
            try:
                await self.repo.delete_product_from_entity(
                    owner_id, owner_type, product_id
                )
                logger.debug(
                    (
                        f"Deleted obsolete product {product_id} for "
                        f"{owner_type.value} ID={owner_id}"
                    ),
                    extra={
                        "owner_id": owner_id,
                        "owner_type": owner_type.value,
                        "product_id": product_id,
                    },
                )
            except Exception as e:
                logger.error(
                    (
                        f"Failed to delete obsolete product {product_id} for "
                        f"{owner_type.value} ID={owner_id}: {str(e)}"
                    ),
                    extra={
                        "owner_id": owner_id,
                        "owner_type": owner_type.value,
                        "product_id": product_id,
                    },
                    exc_info=True,
                )
                continue

    async def load_products_entity_to_bitrix(
        self,
        owner_id: int,
        owner_type: EntityTypeAbbr = EntityTypeAbbr.DEAL,
    ) -> None:
        """
        Загружает (перезаписывает) товары сущности из локальной базы данных в
        Битрикс24.
        """
        logger.info(
            (
                f"Starting product upload to Bitrix for {owner_type.value} "
                f"ID={owner_id}"
            ),
            extra={"owner_id": owner_id, "owner_type": owner_type.value},
        )
        try:
            products_from_db = await self.repo.get_entity_products(
                owner_id, owner_type
            )
            await self.bitrix_client.set_entity_products(
                owner_id, owner_type, products_from_db
            )
            logger.info(
                (
                    f"Successfully uploaded {len(products_from_db.result)} "
                    f"products to Bitrix for {owner_type.value} ID={owner_id}"
                ),
                extra={
                    "owner_id": owner_id,
                    "owner_type": owner_type.value,
                    "uploaded_count": len(products_from_db.result),
                },
            )
        except BitrixApiError as e:
            logger.error(
                (
                    "Bitrix API error during product upload for "
                    f"{owner_type.value} ID={owner_id}: {e.detail}"
                ),
                extra={"owner_id": owner_id, "owner_type": owner_type.value},
                exc_info=True,
            )
            raise
        except Exception as e:
            logger.exception(
                (
                    f"An unexpected error occurred during product upload for "
                    f"{owner_type.value} ID={owner_id}"
                ),
                extra={"owner_id": owner_id, "owner_type": owner_type.value},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    f"Failed to upload products for {owner_type.value} "
                    f"ID={owner_id}"
                ),
            ) from e

    async def product_processing(self, request: Request) -> JSONResponse:
        """
        Основной метод обработки вебхука товаров
        """
        try:
            logger.info("Starting product processing webhook")

            webhook_payload = await self.webhook_service.process_webhook(
                request
            )

            if not webhook_payload or not webhook_payload.entity_id:
                logger.warning("Webhook received but no product ID found")
                return self._success_response(
                    "Webhook received but no product ID found"
                )

            product_id = webhook_payload.entity_id
            logger.info(f"Processing product ID: {product_id}")

            success = await self.bitrix_client.transform_product_fields(
                product_id
            )
            await self.import_from_bitrix(product_id)
            if success:
                logger.info(f"Successfully processed product ID: {product_id}")
                return self._success_response(
                    f"Successfully processed product ID: {product_id}"
                )
            else:
                logger.error(f"Failed to process product ID: {product_id}")
                return self._error_response(
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                    f"Failed to process product ID: {product_id}",
                    "error",
                )

        except Exception as e:
            logger.error(
                f"Error in product_processing: {str(e)}", exc_info=True
            )
            return self._error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                f"Error in product_processing: {str(e)}",
                "error",
            )

    def _success_response(self, message: str, event: str = "") -> JSONResponse:
        """Успешный JSON response"""
        response_data = {"status": "success", "message": message}
        if event:
            response_data["event"] = event

        return JSONResponse(
            status_code=status.HTTP_200_OK, content=response_data
        )

    def _error_response(
        self, status_code: int, message: str, error_type: str
    ) -> JSONResponse:
        """Ответ с ошибкой"""
        return JSONResponse(
            status_code=status_code,
            content={
                "status": "error",
                "message": message,
                "error_type": error_type,
            },
        )
