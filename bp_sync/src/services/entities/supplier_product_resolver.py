from typing import TYPE_CHECKING, Any

from api.v1.schemas.site_request import ProductItem, SiteRequestPayload
from core.logger import logger
from core.settings import settings
from schemas.enums import (
    EntityTypeAbbr,
    SourcesProductEnum,
    TypeEvent,
)
from schemas.product_schemas import (
    ListProductEntity,
    ProductEntityCreate,
    ProductUpdate,
)
from schemas.supplier_schemas import (
    SupplierProductCreate,
    SupplierProductUpdate,
)

from ..exceptions import BitrixApiError

if TYPE_CHECKING:
    from .entities_services import EntityClient

USER_LOADER_PRODUCT = 37


class SupplierProductResolver:
    def __init__(self, entity_client: "EntityClient"):
        self.entity_client = entity_client

    async def process_deal_products(
        self,
        deal_id: int,
        payload: SiteRequestPayload,
        result: dict[str, Any],
    ) -> None:
        """
        Обрабатывает добавление товаров к сделке.

        Args:
            deal_id: ID сделки
            payload: Данные запроса
            result: Словарь результата для обновления
        """
        if payload.type_event == TypeEvent.REQUEST_PRICE:
            await self._add_single_product(deal_id, payload, result)
        elif payload.type_event in (
            TypeEvent.ORDER,
            TypeEvent.REQUEST_PRICE_LABSET,
        ):
            await self._add_multiple_products(deal_id, payload, result)
        else:
            logger.warning(
                "Неизвестный тип события",
                extra={"type_event": payload.type_event, "deal_id": deal_id},
            )
            result["warning"] = (
                f"Неизвестный тип события: {payload.type_event}"
            )

    async def _add_single_product(
        self,
        deal_id: int,
        payload: SiteRequestPayload,
        result: dict[str, Any],
    ) -> None:
        """Добавляет один товар к сделке."""
        # TODO: load Matest product as supplier_product and then
        # find by external supplier code
        product_added = None
        if payload.product_id:
            product_added = await self._add_product_by_xml_id(
                deal_id=deal_id,
                xml_id=payload.product_id,
                product_name=payload.product,
            )

        if product_added:
            result["product_added"] = True
            result["product_id"] = payload.product_id
        else:
            result["product_added"] = False
            result["warning"] = "Не удалось добавить товар к сделке"

            # Добавляем название товара в комментарий
            # if payload.product:
            #     await self._add_product_name_comment(
            #         deal_id=deal_id,
            #         product_name=payload.product,
            #         comment=payload.comment,
            #         bin_company=payload.bin_company,
            #     )
            #     result["product_name_added"] = True

    async def _add_multiple_products(
        self,
        deal_id: int,
        payload: SiteRequestPayload,
        result: dict[str, Any],
    ) -> None:
        """Добавляет несколько товаров к сделке."""
        products = payload.products
        if not products:
            result["warning"] = "Не указаны товары"
            return

        product_entities = await self._prepare_product_entities(
            deal_id=deal_id,
            products=products,
            type_event=payload.type_event,
        )

        if not product_entities:
            result["warning"] = "Не найдено ни одного товара"
            result["products_added"] = 0
            return

        success = await self._save_product_rows(
            owner_id=deal_id,
            products=product_entities,
        )

        result["products_added"] = len(product_entities) if success else 0

    async def _prepare_product_entities(
        self,
        deal_id: int,
        products: list[ProductItem],
        type_event: str,
    ) -> list[ProductEntityCreate]:
        """Подготавливает список товарных позиций для добавления."""
        entities: list[ProductEntityCreate] = []

        for product in products:
            bitrix_product = await self._resolve_bitrix_product(
                product, type_event
            )
            if not bitrix_product:
                logger.warning(
                    "Товар не найден, пропускаем",
                    extra={
                        "product_xml_id": product.product_id,
                        "deal_id": deal_id,
                    },
                )
                continue

            product_name = bitrix_product.get(
                "NAME",
                product.product or "Товар",
            )
            entity_product_data: dict[str, Any] = {
                "owner_id": deal_id,
                "owner_type": EntityTypeAbbr.DEAL,
                "product_id": bitrix_product["ID"],
                "product_name": product_name,
                "quantity": product.quantity,
                "price": product.price,
                "tax_included": True,
                "tax_rate": settings.DEFAULT_TAX_RATE,
            }
            entity = ProductEntityCreate(**entity_product_data)
            entities.append(entity)

        return entities

    async def _resolve_bitrix_product(
        self, product: ProductItem, type_event: str
    ) -> dict[str, Any] | None:
        """
        Возвращает товар из Битрикс по данным переданного продукта
        и типу события.
        """
        if type_event == TypeEvent.ORDER:
            return await self._find_product_by_xml_id(str(product.product_id))

        if type_event == TypeEvent.REQUEST_PRICE_LABSET:
            return await self._resolve_labset_product(product)

        raise ValueError(f"Unsupported type_event: {type_event}")

    async def _resolve_labset_product(
        self, product: Any
    ) -> dict[str, Any] | None:
        """
        Ищет товар LABSET через поставщика и при необходимости создаёт
        в Битрикс.
        """
        source = SourcesProductEnum.LABSET
        supplier_repo = (
            self.entity_client.supplier_client.supplier_product_repo
        )
        supplier_product = await supplier_repo.get_by_source_external_id(
            source, product.product_id
        )

        if not supplier_product:
            # TODO: создать новый товар в системе поставщика или Битрикс
            logger.warning(
                "Товар поставщика LABSET не найден, "
                "создание пока не реализовано",
                extra={"external_id": product.product_id},
            )
            return None

        return await self._find_or_create_product(supplier_product)

    async def _add_product_by_xml_id(
        self,
        deal_id: int,
        xml_id: int,
        product_name: str | None = None,
        quantity: int = 1,
        price: float | None = None,
    ) -> bool:
        """
        Добавляет товар к сделке по XML_ID.

        Args:
            deal_id: ID сделки
            xml_id: XML_ID товара
            product_name: Название товара
            quantity: Количество
            price: Цена (если None - берется из карточки)

        Returns:
            bool: True если товар успешно добавлен
        """
        try:
            product = await self._find_product_by_xml_id(str(xml_id))

            if not product:
                logger.warning(
                    "Товар не найден по XML_ID",
                    extra={"xml_id": xml_id, "deal_id": deal_id},
                )
                return False

            entity_product_data: dict[str, Any] = {
                "owner_id": deal_id,
                "owner_type": EntityTypeAbbr.DEAL,
                "product_id": product["ID"],
                "product_name": product.get("NAME", product_name or "Товар"),
                "quantity": quantity,
                "price": price or product.get("PRICE", 0),
                "tax_included": True,
                "tax_rate": settings.DEFAULT_TAX_RATE,
            }

            entity = ProductEntityCreate(**entity_product_data)

            success = await self._save_product_rows(
                owner_id=deal_id,
                products=[entity],
            )

            if success:
                logger.info(
                    "Товар успешно добавлен к сделке",
                    extra={
                        "deal_id": deal_id,
                        "xml_id": xml_id,
                        "product_id": product["ID"],
                        "quantity": quantity,
                    },
                )

            return success

        except Exception as e:
            logger.error(
                "Ошибка при добавлении товара",
                extra={
                    "deal_id": deal_id,
                    "xml_id": xml_id,
                    "error": str(e),
                },
                exc_info=True,
            )
            return False

    async def _find_product_by_xml_id(
        self,
        xml_id: str,
    ) -> dict[str, Any] | None:
        """
        Находит товар по XML_ID.

        Args:
            xml_id: XML_ID товара

        Returns:
            dict | None: Данные товара или None если не найден
        """
        try:
            deal_client = self.entity_client.bitrix_client.deal_bitrix_client
            params = deal_client._prepare_params(
                select=["ID", "NAME", "PRICE", "XML_ID"],
                filter={"XML_ID": xml_id},
            )

            response = await deal_client.bitrix_client.call_api(
                "crm.product.list",
                params,
            )

            products_data = response.get("result", {})
            products = self._extract_products_list(products_data)

            if products:
                product = products[0]
                return {
                    "ID": product.get("ID"),
                    "NAME": product.get("NAME"),
                    "PRICE": product.get("PRICE", 0),
                    "XML_ID": product.get("XML_ID", xml_id),
                }

            logger.debug("Товар не найден", extra={"xml_id": xml_id})
            return None

        except BitrixApiError as e:
            logger.error(
                "Ошибка Bitrix API при поиске товара",
                extra={"xml_id": xml_id, "error": str(e)},
            )
            return None
        except Exception as e:
            logger.error(
                "Неожиданная ошибка при поиске товара",
                extra={"xml_id": xml_id, "error": str(e)},
                exc_info=True,
            )
            return None

    async def _find_or_create_product(
        self,
        supplier_product: SupplierProductCreate,
    ) -> dict[str, Any] | None:
        result: dict[str, Any] = {}
        product_client = self.entity_client.supplier_client.product_client

        if product_id := supplier_product.product_id:
            product = await product_client.repo.get_product_with_properties(
                product_id
            )
            if not product:
                return None
            return {"ID": product.external_id, "NAME": product.name}
        else:
            if not supplier_product.name:
                return None

            product_create = ProductUpdate(name=supplier_product.name)
            product_bitrix_client = (
                self.entity_client.bitrix_client.product_bitrix_client
            )
            product_id = await product_bitrix_client.create(product_create)
            if product_id:
                # mapping bitrix_product and supplier_product
                product, _ = await product_client.import_from_bitrix(
                    product_id
                )
                supplier_product_repo = (
                    self.entity_client.supplier_client.supplier_product_repo
                )
                await supplier_product_repo.update(
                    supplier_product.id,
                    SupplierProductUpdate(product_id=product.id),
                )
                await product_bitrix_client.send_message_b24(
                    USER_LOADER_PRODUCT,
                    (
                        "Need no update supplier product "
                        f"id: {supplier_product.external_id}, "
                        f"source: {supplier_product.source}"
                        f"name: {supplier_product.name}"
                    ),
                )
                return {"ID": product_id, "NAME": supplier_product.name}
        return result

    def _extract_products_list(
        self,
        products_data: dict[str, Any] | list[Any],
    ) -> list[dict[str, Any]]:
        """Извлекает список товаров из ответа API."""
        if isinstance(products_data, dict) and "products" in products_data:
            return products_data["products"]  # type: ignore[no-any-return]
        if isinstance(products_data, list):
            return products_data
        return []

    async def _save_product_rows(
        self,
        owner_id: int,
        products: list[ProductEntityCreate],
        owner_type: EntityTypeAbbr = EntityTypeAbbr.DEAL,
    ) -> bool:
        """
        Устанавливает товарные позиции в сущность CRM.
        Перезаписывает все существующие товарные позиции.

        Args:
            owner_id: ID сделки
            products: Список товарных позиций

        Returns:
            bool: True если успешно сохранено
        """
        try:
            product_list = ListProductEntity(result=products)
            bitrix_client = self.entity_client.bitrix_client
            bitrix_api_client = bitrix_client.deal_bitrix_client.bitrix_client

            params: dict[str, Any] = {
                "ownerId": owner_id,
                "ownerType": owner_type.value,
                "productRows": product_list.to_bitrix_dict(),
            }

            response = await bitrix_api_client.call_api(
                "crm.item.productrow.set",
                params=params,
            )

            entity_data = response.get("result", {})
            success = bool(entity_data.get("productRows"))

            if success:
                logger.debug(
                    "Товарные позиции сохранены",
                    extra={
                        "deal_id": owner_id,
                        "count": len(products),
                    },
                )
            else:
                logger.warning(
                    "Не удалось сохранить товарные позиции",
                    extra={"deal_id": owner_id},
                )

            return success

        except BitrixApiError as e:
            logger.error(
                "Ошибка Bitrix API при сохранении товаров",
                extra={"deal_id": owner_id, "error": str(e)},
            )
            return False
        except Exception as e:
            logger.error(
                "Неожиданная ошибка при сохранении товаров",
                extra={"deal_id": owner_id, "error": str(e)},
                exc_info=True,
            )
            return False
