"""
Обработчик запросов с сайта для интеграции с Bitrix24.

Модуль обеспечивает создание сделок, контактов и компаний
на основе входящих запросов с сайта.
"""

from collections import defaultdict
from typing import TYPE_CHECKING, Any

from fastapi import HTTPException, status

from api.v1.schemas.site_request import SiteRequestPayload
from core.logger import logger
from core.settings import settings
from schemas.deal_schemas import DealUpdate
from schemas.enums import EntityTypeAbbr, StageSemanticEnum, TypeEvent
from schemas.product_schemas import ListProductEntity, ProductEntityCreate

from ..exceptions import (  # ProductNotFoundError,
    BitrixApiError,
    ContactCreationError,
    DealCreationError,
    ManagerNotFoundError,
    SiteRequestProcessingError,
)

if TYPE_CHECKING:
    from .entities_bitrix_services import EntitiesBitrixClient

DEFAULT_DEAL_TITLE = "Запрос цены с сайта"
DEFAULT_TAX_RATE = 16
SITE_SOURCE = "WEB"
EVENT_SOURCE_MAPPING = {
    "order": "matest",
    "request_price": "matest",
    "request_price_labset": "labset",
}


class SiteRequestHandler:
    """
    Обработчик событий с сайта для создания сделок в Bitrix24.

    Обеспечивает:
    - Поиск/создание контактов и компаний по телефону/email
    - Распределение сделок между менеджерами по загрузке
    - Добавление товаров к сделкам
    - Обработку ошибок и логирование

    Attributes:
        entities_bitrix_client: Клиент для работы с сущностями Bitrix24
        managers: Множество ID доступных менеджеров
    """

    def __init__(
        self,
        entities_bitrix_client: "EntitiesBitrixClient",
        managers: set[int] | None = None,
    ):
        """
        Инициализация обработчика.

        Args:
            entities_bitrix_client: Клиент для работы с сущностями Bitrix24
            managers: Множество ID менеджеров (опционально)
        """
        self._bitrix_client = entities_bitrix_client
        self._managers = managers or settings.MANAGERS

    async def handle_request_price(
        self, payload: SiteRequestPayload
    ) -> dict[str, Any]:
        """
        Обрабатывает запрос цены с сайта.

        Создает сделку, привязывает контакт/компанию,
        добавляет товары и комментарии.

        Args:
            payload: Данные запроса с сайта

        Returns:
            dict: Результат обработки с деталями операции

        Raises:
            HTTPException: При критических ошибках обработки
        """
        self._log_request_start(payload)
        try:
            deal_id = await self._create_deal_from_payload(payload)

            result = self._create_success_result(deal_id)
            await self._process_deal_products(deal_id, payload, result)
            await self._add_timeline_comment(deal_id, payload)

            self._log_request_success(deal_id, result)
            return result

        except HTTPException:
            raise
        except SiteRequestProcessingError as e:
            self._log_processing_error(payload, e)
            raise self._create_internal_error() from e
        except Exception as e:
            self._log_unexpected_error(payload, e)
            raise self._create_internal_error() from e

    # ============================================
    # Создание сделки
    # ============================================

    async def _create_deal_from_payload(
        self,
        payload: SiteRequestPayload,
    ) -> int:
        """
        Создает сделку на основе данных запроса.

        Args:
            payload: Данные запроса

        Returns:
            int: ID созданной сделки

        Raises:
            DealCreationError: При ошибке создания сделки
        """
        # TODO: if bin_company not None => search company.
        # if find => check phone and added if need else next
        entity_type, entity_id, manager_id = await self._find_or_create_entity(
            phone=payload.phone,
            email=payload.email,
            name=payload.name,
        )

        if not entity_id or not manager_id:
            raise DealCreationError(
                f"Не удалось определить сущность или менеджера: "
                f"entity_id={entity_id}, manager_id={manager_id}"
            )

        deal_id = await self._create_deal_record(
            entity_type=entity_type,
            entity_id=entity_id,
            manager_id=manager_id,
            payload=payload,
        )

        if not deal_id:
            raise DealCreationError("Сделка не создана")

        return deal_id

    async def _create_deal_record(
        self,
        entity_type: str,
        entity_id: int,
        manager_id: int,
        payload: SiteRequestPayload,
    ) -> int | None:
        """
        Создает запись сделки в Bitrix24.

        Args:
            entity_type: Тип сущности (contact_id/company_id)
            entity_id: ID сущности
            manager_id: ID ответственного менеджера
            payload: Данные запроса

        Returns:
            int | None: ID созданной сделки или None при ошибке
        """
        try:
            title = self._build_deal_title(payload)
            comment = self._build_deal_comment(payload)

            deal_data = {
                "title": title,
                entity_type: entity_id,
                "assigned_by_id": manager_id,
                "comments": comment,
                "source_id": SITE_SOURCE,
            }

            deal_update = DealUpdate(**deal_data)
            deal_client = self._bitrix_client.deal_bitrix_client
            deal_id = await deal_client.create(deal_update)

            logger.info(
                "Сделка успешно создана",
                extra={
                    "deal_id": deal_id,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "manager_id": manager_id,
                    "type_event": payload.type_event,
                },
            )

            return deal_id

        except BitrixApiError as e:
            logger.error(
                "Ошибка Bitrix API при создании сделки",
                extra={"error": str(e), "phone": payload.phone},
            )
            return None
        except Exception as e:
            logger.error(
                "Неожиданная ошибка при создании сделки",
                extra={"error": str(e), "phone": payload.phone},
                exc_info=True,
            )
            return None

    def _build_deal_title(self, payload: SiteRequestPayload) -> str:
        """
        Формирует заголовок сделки.

        Args:
            payload: Данные запроса

        Returns:
            str: Заголовок сделки
        """
        source = EVENT_SOURCE_MAPPING.get(payload.type_event, "")

        if payload.message_id:
            return f"{DEFAULT_DEAL_TITLE} {source} #{payload.message_id}"

        return DEFAULT_DEAL_TITLE

    def _build_deal_comment(self, payload: SiteRequestPayload) -> str:
        """
        Формирует комментарий к сделке.

        Args:
            payload: Данные запроса

        Returns:
            str: Комментарий к сделке
        """
        parts = []

        if payload.bin_company:
            parts.append(f"БИН/компания: {payload.bin_company}")

        if payload.comment:
            parts.append(payload.comment)

        return "\n".join(parts) if parts else ""

    # ============================================
    # Поиск и создание сущностей (контакт/компания)
    # ============================================

    async def _find_or_create_entity(
        self,
        phone: str | None = None,
        email: str | None = None,
        name: str | None = None,
    ) -> tuple[str, int, int]:
        """
        Находит существующую или создает новую сущность.

        Ищет контакт/компанию по телефону или email.
        Если не найдено - создает новый контакт.

        Args:
            phone: Телефон для поиска
            email: Email для поиска
            name: Имя для создания контакта

        Returns:
            tuple: (тип_сущности, id_сущности, id_менеджера)
        """
        # TODO: Если сущность найдена по телефону, а почта есть и не прописана,
        # тогда добавить. Аналогично наоборот.

        # Поиск по телефону
        if phone:
            result = await self._search_entity_by_phone(phone)
            if result:
                return result

        # Поиск по email
        if email:
            result = await self._search_entity_by_email(email)
            if result:
                return result

        # Создание нового контакта
        return await self._create_new_contact(
            phone=phone, email=email, name=name
        )

    async def _search_entity_by_phone(
        self, phone: str
    ) -> tuple[str, int, int] | None:
        """Ищет сущность по номеру телефона."""
        return await self._search_entity_by_communication(
            comm_type="PHONE",
            value=phone,
        )

    async def _search_entity_by_email(
        self, email: str
    ) -> tuple[str, int, int] | None:
        """Ищет сущность по email."""
        return await self._search_entity_by_communication(
            comm_type="EMAIL",
            value=email,
        )

    async def _search_entity_by_communication(
        self,
        comm_type: str,
        value: str,
    ) -> tuple[str, int, int] | None:
        """
        Ищет сущность по типу коммуникации.

        Args:
            comm_type: Тип коммуникации (PHONE/EMAIL)
            value: Значение для поиска

        Returns:
            tuple | None: (тип_сущности, id_сущности, id_менеджера) или None
        """
        try:
            bitrix_client = self._get_bitrix_client()
            params = {"type": comm_type, "values": [value.split()]}

            response = await bitrix_client.call_api(
                "crm.duplicate.findbycomm",
                params,
            )
            entities = response.get("result", {})

            if not isinstance(entities, dict):
                return None

            # Приоритет: контакт -> компания
            if contact_result := await self._extract_contact_from_search(
                entities
            ):
                return contact_result

            if company_result := await self._extract_company_from_search(
                entities
            ):
                return company_result

            return None

        except BitrixApiError as e:
            logger.error(
                "Ошибка при поиске сущности",
                extra={
                    "comm_type": comm_type,
                    "value": value,
                    "error": str(e),
                },
            )
            return None
        except Exception as e:
            logger.error(
                "Неожиданная ошибка при поиске сущности",
                extra={
                    "comm_type": comm_type,
                    "value": value,
                    "error": str(e),
                },
                exc_info=True,
            )
            return None

    async def _extract_contact_from_search(
        self,
        entities: dict[str, Any],
    ) -> tuple[str, int, int] | None:
        """Извлекает контакт из результатов поиска."""
        contact_ids = entities.get("CONTACT", [])
        if not contact_ids:
            return None

        contact_id = int(contact_ids[0])
        manager_id = await self._get_contact_manager(contact_id)

        if manager_id:
            return ("contact_id", contact_id, manager_id)

        return None

    async def _extract_company_from_search(
        self,
        entities: dict[str, Any],
    ) -> tuple[str, int, int] | None:
        """Извлекает компанию из результатов поиска."""
        company_ids = entities.get("COMPANY", [])
        if not company_ids:
            return None

        company_id = int(company_ids[0])
        manager_id = await self._get_company_manager(company_id)

        if manager_id:
            return ("company_id", company_id, manager_id)

        return None

    async def _create_new_contact(
        self,
        phone: str | None = None,
        email: str | None = None,
        name: str | None = None,
    ) -> tuple[str, int, int]:
        """
        Создает новый контакт в Bitrix24.

        Args:
            phone: Телефон контакта
            email: Email контакта
            name: Имя контакта

        Returns:
            tuple: (тип_сущности, id_сущности, id_менеджера)

        Raises:
            ContactCreationError: При ошибке создания контакта
        """
        try:
            manager_id = await self._get_available_manager()

            contact_fields: dict[str, Any] = {
                "NAME": name,
                "ASSIGNED_BY_ID": manager_id,
            }

            if phone:
                contact_fields["PHONE"] = [
                    {"VALUE": phone, "VALUE_TYPE": "WORK"}
                ]

            if email:
                contact_fields["EMAIL"] = [
                    {"VALUE": email, "VALUE_TYPE": "WORK"}
                ]

            bitrix_client = self._get_bitrix_client()
            response = await bitrix_client.call_api(
                "crm.contact.add",
                {"fields": contact_fields},
            )

            contact_id = response.get("result")

            if not contact_id:
                raise ContactCreationError("Не удалось создать контакт")

            logger.info(
                "Контакт успешно создан",
                extra={
                    "contact_id": contact_id,
                    "manager_id": manager_id,
                    "phone": phone,
                    "email": email,
                },
            )

            return ("contact_id", int(contact_id), manager_id)

        except ContactCreationError:
            raise
        except BitrixApiError as e:
            logger.error(
                "Ошибка Bitrix API при создании контакта",
                extra={"error": str(e), "phone": phone},
            )
            return ("", 0, 0)
        except Exception as e:
            logger.error(
                "Неожиданная ошибка при создании контакта",
                extra={"error": str(e), "phone": phone},
                exc_info=True,
            )
            return ("", 0, 0)

    # ============================================
    # Управление менеджерами
    # ============================================

    async def _get_available_manager(self) -> int:
        """
        Находит менеджера с минимальной загрузкой.

        Returns:
            int: ID менеджера

        Raises:
            ManagerNotFoundError: Если нет доступных менеджеров
        """
        if not self._managers:
            raise ManagerNotFoundError("Список менеджеров пуст")

        try:
            manager_loads = await self._calculate_manager_loads()

            if not manager_loads:
                raise ManagerNotFoundError(
                    "Не удалось получить данные о загрузке менеджеров"
                )

            # Выбираем менеджера с минимальной загрузкой
            # manager_id = min(manager_loads, key=manager_loads.get)
            manager_id, load = min(manager_loads.items(), key=lambda x: x[1])
            # load = manager_loads[manager_id]

            logger.info(
                "Выбран менеджер с минимальной загрузкой",
                extra={
                    "manager_id": manager_id,
                    "current_load": load,
                    "total_managers": len(manager_loads),
                    "all_loads": dict(manager_loads),
                },
            )

            return manager_id

        except ManagerNotFoundError:
            raise
        except Exception as e:
            logger.error(
                "Ошибка при выборе менеджера",
                extra={"error": str(e)},
                exc_info=True,
            )
            # Возвращаем первого менеджера как fallback
            return next(iter(self._managers))

    async def _calculate_manager_loads(self) -> dict[int, int]:
        """
        Рассчитывает загрузку менеджеров (количество активных сделок).

        Returns:
            dict: Маппинг ID менеджера -> количество сделок
        """
        filter_params: dict[str, Any] = {
            "STAGE_SEMANTIC_ID": StageSemanticEnum.PROSPECTIVE.value,
            "ASSIGNED_BY_ID": list(self._managers),
        }

        deal_client = self._bitrix_client.deal_bitrix_client
        deals = await deal_client.list(
            select=["ID", "ASSIGNED_BY_ID"],
            filter_entity=filter_params,
        )

        loads: dict[int, int] = defaultdict(int)

        # Подсчет сделок по менеджерам
        for deal in deals.result:
            manager_id = getattr(deal, "assigned_by_id", None)
            if manager_id and manager_id in self._managers:
                loads[manager_id] += 1

        # Добавляем менеджеров без сделок
        for manager_id in self._managers:
            loads.setdefault(manager_id, 0)

        return loads

    # ============================================
    # Получение менеджеров сущностей
    # ============================================

    async def _get_contact_manager(self, contact_id: int) -> int:
        """Получает ID ответственного менеджера контакта."""
        try:
            contact_client = self._bitrix_client.contact_bitrix_client
            contact = await contact_client.get(contact_id)
            return int(contact.assigned_by_id) if contact else 0
        except Exception as e:
            logger.error(
                "Ошибка при получении менеджера контакта",
                extra={"contact_id": contact_id, "error": str(e)},
            )
            return 0

    async def _get_company_manager(self, company_id: int) -> int:
        """Получает ID ответственного менеджера компании."""
        try:
            company_client = self._bitrix_client.company_bitrix_client
            company = await company_client.get(company_id)
            return int(company.assigned_by_id) if company else 0
        except Exception as e:
            logger.error(
                "Ошибка при получении менеджера компании",
                extra={"company_id": company_id, "error": str(e)},
            )
            return 0

    # ============================================
    # Работа с товарами
    # ============================================

    async def _process_deal_products(
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
            if payload.product:
                await self._add_product_name_comment(
                    deal_id=deal_id,
                    product_name=payload.product,
                    comment=payload.comment,
                    bin_company=payload.bin_company,
                )
                result["product_name_added"] = True

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
        products: list[Any],
        type_event: str,
    ) -> list[ProductEntityCreate]:
        """Подготавливает список товарных позиций для добавления."""
        entities = []

        for product in products:
            bitrix_product = None
            if type_event == TypeEvent.ORDER:
                bitrix_product = await self._find_product_by_xml_id(
                    str(product.product_id)
                )
            elif type_event == TypeEvent.REQUEST_PRICE_LABSET:
                bitrix_product = None
                # TODO: реализовать поиск или создание товара при запросе
                # с labset
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

            entity = ProductEntityCreate(
                owner_id=deal_id,
                owner_type=EntityTypeAbbr.DEAL,
                product_id=bitrix_product["ID"],
                product_name=product_name,
                quantity=product.quantity,
                price=product.price,
                tax_included=True,
                tax_rate=DEFAULT_TAX_RATE,
            )
            entities.append(entity)

        return entities

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

            entity = ProductEntityCreate(
                owner_id=deal_id,
                owner_type=EntityTypeAbbr.DEAL,
                product_id=product["ID"],
                product_name=product.get("NAME", product_name or "Товар"),
                quantity=quantity,
                price=price or product.get("PRICE", 0),
                tax_included=True,
                tax_rate=DEFAULT_TAX_RATE,
            )

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
            deal_client = self._bitrix_client.deal_bitrix_client
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
            bitrix_client = self._get_bitrix_client()

            params = {
                "ownerId": owner_id,
                "ownerType": owner_type.value,
                "productRows": product_list.to_bitrix_dict(),
            }

            response = await bitrix_client.call_api(
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

    # ============================================
    # Комментарии
    # ============================================

    async def _add_product_name_comment(
        self,
        deal_id: int,
        product_name: str,
        comment: str | None,
        bin_company: str | None,
    ) -> bool:
        """Добавляет комментарий с названием товара к сделке."""
        try:
            comment_text = self._format_product_comment(
                product_name=product_name,
                comment=comment,
                bin_company=bin_company,
            )

            deal_update = DealUpdate(
                external_id=deal_id,
                comments=comment_text,
            )

            await self._bitrix_client.deal_bitrix_client.update(deal_update)

            logger.debug(
                "Комментарий с товаром добавлен",
                extra={"deal_id": deal_id},
            )

            return True

        except Exception as e:
            logger.error(
                "Ошибка при добавлении комментария",
                extra={"deal_id": deal_id, "error": str(e)},
            )
            return False

    def _format_product_comment(
        self,
        product_name: str,
        comment: str | None,
        bin_company: str | None,
    ) -> str:
        """Формирует комментарий с информацией о товаре."""
        parts = []

        if bin_company:
            parts.append(f"БИН/компания: {bin_company}")

        if comment:
            parts.append(comment)

        parts.append(f"Товар: {product_name}")

        return "\n".join(parts)

    async def _add_timeline_comment(
        self,
        deal_id: int,
        payload: SiteRequestPayload,
    ) -> bool:
        """
        Добавляет комментарий в ленту временной шкалы сделки.

        Args:
            deal_id: ID сделки
            payload: Данные запроса

        Returns:
            bool: True если комментарий добавлен
        """
        message = self._format_timeline_message(payload)

        try:
            bitrix_client = self._get_bitrix_client()

            response = await bitrix_client.call_api(
                "crm.timeline.comment.add",
                {
                    "fields": {
                        "ENTITY_ID": deal_id,
                        "ENTITY_TYPE": "deal",
                        "COMMENT": message,
                    }
                },
            )

            success = bool(response.get("result"))

            if success:
                logger.info(
                    "Комментарий добавлен в ленту сделки",
                    extra={"deal_id": deal_id},
                )
            else:
                logger.warning(
                    "Не удалось добавить комментарий в ленту",
                    extra={"deal_id": deal_id},
                )

            return success

        except Exception as e:
            logger.error(
                "Ошибка при добавлении комментария в ленту",
                extra={"deal_id": deal_id, "error": str(e)},
                exc_info=True,
            )
            return False

    def _format_timeline_message(self, payload: SiteRequestPayload) -> str:
        """Формирует сообщение для временной шкалы."""
        parts = []

        if payload.bin_company:
            parts.append(f"БИН/компания: {payload.bin_company}")

        if payload.comment:
            parts.append(payload.comment)

        if payload.product:
            parts.append(f"Товар: {payload.product}")

        return "\n".join(parts)

    # ============================================
    # Вспомогательные методы
    # ============================================

    def _get_bitrix_client(self) -> Any:
        """Возвращает клиент Bitrix API."""
        return self._bitrix_client.deal_bitrix_client.bitrix_client

    def _create_success_result(self, deal_id: int) -> dict[str, Any]:
        """Создает базовый результат успешной обработки."""
        return {
            "success": True,
            "deal_id": deal_id,
            "message": "Запрос успешно обработан",
        }

    def _create_internal_error(self) -> HTTPException:
        """Создает HTTP исключение для внутренней ошибки."""
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка при обработке запроса",
        )

    # ============================================
    # Логирование
    # ============================================

    def _log_request_start(self, payload: SiteRequestPayload) -> None:
        """Логирует начало обработки запроса."""
        logger.info(
            "Начало обработки запроса с сайта",
            extra={
                "type_event": payload.type_event,
                "phone": payload.phone if payload.phone else "-",
                "email": payload.email if payload.email else "-",
                "contact_name": payload.name if payload.name else "-",
                "message_id": (
                    payload.message_id if payload.message_id else "-"
                ),
            },
        )

    def _log_request_success(
        self,
        deal_id: int,
        result: dict[str, Any],
    ) -> None:
        """Логирует успешное завершение обработки."""
        logger.info(
            "Запрос успешно обработан",
            extra={"deal_id": deal_id, "result": result},
        )

    def _log_processing_error(
        self,
        payload: SiteRequestPayload,
        error: SiteRequestProcessingError,
    ) -> None:
        """Логирует ошибку обработки."""
        logger.error(
            "Ошибка обработки запроса",
            extra={
                "type_event": payload.type_event,
                "error": str(error),
                "error_type": type(error).__name__,
            },
            exc_info=True,
        )

    def _log_unexpected_error(
        self,
        payload: SiteRequestPayload,
        error: Exception,
    ) -> None:
        """Логирует неожиданную ошибку."""
        logger.error(
            "Критическая ошибка при обработке запроса",
            extra={
                "type_event": payload.type_event,
                "phone": payload.phone,
                "error": str(error),
                "error_type": type(error).__name__,
            },
            exc_info=True,
        )
