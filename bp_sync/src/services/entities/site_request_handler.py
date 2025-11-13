from collections import defaultdict
from typing import TYPE_CHECKING, Any

from fastapi import HTTPException, status

from core.logger import logger
from schemas.deal_schemas import DealUpdate
from schemas.enums import EntityTypeAbbr, StageSemanticEnum
from schemas.product_schemas import ListProductEntity, ProductEntityCreate

from ..exceptions import BitrixApiError

if TYPE_CHECKING:
    from .entities_bitrix_services import EntitiesBitrixClient

MANAGERS = {33, 35, 13, 37}  # Maylen, Azamat
DEFAULT_DEAL_TITLE = "Запрос цены с сайта"


class SiteRequestHandler:
    """
    Обработчик событий с сайта для создания сделок в Bitrix24.

    Обеспечивает:
    - Поиск/создание контактов и компаний по телефону
    - Распределение сделок между менеджерами по загрузке
    - Добавление товаров к сделкам
    - Обработку ошибок и логирование
    """

    def __init__(self, entities_bitrix_client: "EntitiesBitrixClient"):
        """
        Инициализация обработчика.

        Args:
            entities_bitrix_client: Клиент для работы с сущностями Bitrix24
        """
        self.entities_bitrix_client = entities_bitrix_client

    async def handle_request_price(
        self,
        phone: str,
        product_id: int,
        product_name: str | None = None,
        name: str | None = None,
        comment: str | None = None,
        message_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Обрабатывает запрос цены с сайта.

        Args:
            phone: Телефон клиента
            product_id: XML_ID товара
            product_name: Название товара (опционально)
            name: Имя клиента (опционально)
            comment: Комментарий к заявке
            message_id: ID сообщения для отслеживания

        Returns:
            dict: Результат обработки с деталями операции

        Raises:
            HTTPException: При критических ошибках обработки
        """
        logger.info(
            "Обработка запроса цены",
            extra={
                "phone": phone,
                "product_id": product_id,
                "message_id": message_id,
            },
        )
        try:
            deal_id = await self._create_deal(phone, name, comment, message_id)
            if not deal_id:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Не удалось создать сделку",
                )

            result: dict[str, Any] = {
                "success": True,
                "deal_id": deal_id,
                "message": "Запрос успешно обработан",
            }

            product_added = await self._add_product_to_deal(
                deal_id, product_id, product_name=product_name
            )
            if product_added:
                result["product_added"] = True
                result["product_id"] = product_id
            else:
                result["product_added"] = False
                result["warning"] = "Не удалось добавить товар к сделке"

            if not product_added and product_name:
                comment_added = await self._add_deal_comment(
                    deal_id, product_name, comment
                )
                if comment_added:
                    result["product_name_added"] = True

            logger.info(
                "Запрос цены успешно обработан",
                extra={"deal_id": deal_id, "result": result},
            )
            if await self._add_timeline_comment_to_deal(
                deal_id,
                self._get_complex_comment(
                    product_name if product_name else "", comment
                ),
            ):
                result["timeline_comment_added"] = True
            else:
                result["timeline_comment_added"] = False

            return result

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Критическая ошибка при обработке запроса цены",
                extra={
                    "phone": phone,
                    "product_id": product_id,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Внутренняя ошибка при обработке запроса",
            )

    async def _create_deal(
        self,
        phone: str,
        name: str | None = None,
        comment: str | None = None,
        message_id: str | None = None,
    ) -> int | None:
        """
        Создает сделку в Bitrix24.

        Args:
            phone: Телефон клиента
            name: Имя клиента
            comment: Комментарий
            message_id: ID сообщения

        Returns:
            int: ID созданной сделки или None при ошибке
        """
        try:
            result_entity = await self._get_entity_by_phone(phone, name)
            entity_type, entity_id, assigned_id = result_entity

            if not entity_id or not assigned_id:
                logger.error("Не удалось определить сущность или менеджера")
                return None

            # Формируем заголовок сделки
            title = (
                f"{DEFAULT_DEAL_TITLE} #{message_id}"
                if message_id
                else DEFAULT_DEAL_TITLE
            )

            deal_data: dict[str, Any] = {
                "title": title,
                entity_type: entity_id,
                "assigned_by_id": assigned_id,
                "comments": comment,
            }
            deal_update = DealUpdate(**deal_data)
            deal_client = self.entities_bitrix_client.deal_bitrix_client
            deal_id = await deal_client.create(deal_update)

            logger.info(
                "Сделка успешно создана",
                extra={
                    "deal_id": deal_id,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "manager_id": assigned_id,
                },
            )

            return deal_id

        except BitrixApiError as e:
            logger.error(
                "Ошибка Bitrix API при создании сделки",
                extra={"error": str(e), "phone": phone},
            )
            return None
        except Exception as e:
            logger.error(
                "Неожиданная ошибка при создании сделки",
                extra={"error": str(e), "phone": phone},
                exc_info=True,
            )
            return None

    async def _get_entity_by_phone(
        self, phone: str, name: str | None = None
    ) -> tuple[str, int, int]:
        """
        Находит или создает контакт/компанию по телефону.

        Args:
            phone: Телефон для поиска
            name: Имя для создания нового контакта

        Returns:
            tuple: (тип_сущности, id_сущности, id_менеджера)
        """
        method = "crm.duplicate.findbycomm"
        params: dict[str, Any] = {"type": "PHONE", "values": [phone]}
        fail_result: tuple[str, int, int] = ("", 0, 0)
        try:
            bitrix_client = (
                self.entities_bitrix_client.deal_bitrix_client.bitrix_client
            )
            result = await bitrix_client.call_api(method, params)
            entities = result.get("result", {})

            if isinstance(entities, dict):
                contact_ids = entities.get("CONTACT", [])
                if contact_ids:
                    contact_id = int(contact_ids[0])
                    assigned_id = await self._get_assigned_contact(contact_id)
                    if assigned_id:
                        return "contact_id", contact_id, assigned_id

                company_ids = entities.get("COMPANY", [])
                if company_ids:
                    company_id = int(company_ids[0])
                    assigned_id = await self._get_assigned_company(company_id)
                    if assigned_id:
                        return "company_id", company_id, assigned_id

            assigned_id = await self._get_free_manager()
            if not assigned_id:
                logger.error("Не удалось найти свободного менеджера")
                return fail_result

            method = "crm.contact.add"
            params_contact: dict[str, Any] = {
                "fields": {
                    "NAME": name,
                    "ASSIGNED_BY_ID": assigned_id,
                    "PHONE": [{"VALUE": phone, "VALUE_TYPE": "WORK"}],
                }
            }

            result = await bitrix_client.call_api(method, params_contact)
            contact_id = result.get("result")  # type: ignore[assignment]
            if contact_id:
                return "contact_id", int(contact_id), assigned_id
            else:
                logger.error("Не удалось создать контакт")
                return fail_result

        except BitrixApiError as e:
            logger.error(
                "Ошибка Bitrix API при поиске/создании сущности",
                extra={"error": str(e), "phone": phone},
            )
            return fail_result
        except Exception as e:
            logger.error(
                "Неожиданная ошибка при поиске/создании сущности",
                extra={"error": str(e), "phone": phone},
                exc_info=True,
            )
            return fail_result

    async def _get_free_manager(self) -> int:
        """
        Находит менеджера с наименьшим количеством активных сделок.

        Returns:
            int: ID менеджера с минимальной загрузкой

        Raises:
            ValueError: Если нет доступных менеджеров
        """
        if not MANAGERS:
            raise ValueError("Список менеджеров пуст")

        # Получаем все активные сделки для указанных менеджеров
        filter_entity: dict[str, Any] = {
            "STAGE_SEMANTIC_ID": StageSemanticEnum.PROSPECTIVE.value,
            "ASSIGNED_BY_ID": list(MANAGERS),
        }
        select = ["ID", "ASSIGNED_BY_ID"]

        try:
            # Получаем список сделок
            deal_bitrix_client = self.entities_bitrix_client.deal_bitrix_client
            deals_response = await deal_bitrix_client.list(
                select=select, filter_entity=filter_entity
            )

            # Считаем количество сделок для каждого менеджера
            manager_deal_count: dict[int, int] = defaultdict(int)

            for deal in deals_response.result:
                manager_id = getattr(deal, "assigned_by_id", None)
                if manager_id and manager_id in MANAGERS:
                    manager_deal_count[manager_id] += 1

            # Добавляем менеджеров без сделок (счетчик = 0)
            for manager_id in MANAGERS:
                if manager_id not in manager_deal_count:
                    manager_deal_count[manager_id] = 0

            if not manager_deal_count:
                raise ValueError("Не удалось получить данные о менеджерах")

            # Находим менеджера с минимальным количеством сделок
            min_manager_id = min(
                manager_deal_count.items(), key=lambda x: x[1]
            )[0]

            logger.info(
                (
                    f"Выбран менеджер {min_manager_id} с "
                    f"{manager_deal_count[min_manager_id]} активными сделками"
                ),
                extra={
                    "manager_id": min_manager_id,
                    "deal_count": manager_deal_count[min_manager_id],
                    "total_managers": len(manager_deal_count),
                    "managers_load": dict(manager_deal_count),
                },
            )

            return min_manager_id

        except Exception as e:
            logger.error(
                "Неожиданная ошибка при выборе менеджера",
                extra={"error": str(e)},
                exc_info=True,
            )
        return next(iter(MANAGERS))

    async def _get_assigned_contact(self, contact_id: int) -> int:
        """
        Получает ID ответственного менеджера контакта.

        Args:
            contact_id: ID контакта

        Returns:
            int: ID менеджера или 0 при ошибке
        """
        try:
            contact_client = self.entities_bitrix_client.contact_bitrix_client
            contact = await contact_client.get(contact_id)
            return int(contact.assigned_by_id) if contact else 0
        except Exception as e:
            logger.error(
                "Ошибка при получении менеджера контакта",
                extra={"contact_id": contact_id, "error": str(e)},
            )
            return 0

    async def _get_assigned_company(self, company_id: int) -> int:
        """
        Получает ID ответственного менеджера компании.

        Args:
            company_id: ID компании

        Returns:
            int: ID менеджера или 0 при ошибке
        """
        try:
            company_client = self.entities_bitrix_client.company_bitrix_client
            company = await company_client.get(company_id)
            return int(company.assigned_by_id) if company else 0
        except Exception as e:
            logger.error(
                "Ошибка при получении менеджера компании",
                extra={"company_id": company_id, "error": str(e)},
            )
            return 0

    async def _add_product_to_deal(
        self,
        deal_id: int,
        product_xml_id: int,
        quantity: int = 0,
        price: float | None = None,
        discount: float | None = None,
        product_name: str | None = None,
    ) -> bool:
        """
        Добавляет товар к сделке по XML_ID товара

        Args:
            deal_id: ID сделки
            product_xml_id: XML_ID товара
            quantity: Количество товара (по умолчанию 0)
            price: Цена товара (если None - берется из карточки товара)
            discount: Скидка на товар

        Returns:
            bool: True если товар успешно добавлен
        """
        try:
            product = await self._find_product_by_xml_id(str(product_xml_id))
            if not product:
                logger.warning(
                    "Товар не найден",
                    extra={
                        "product_xml_id": product_xml_id,
                        "deal_id": deal_id,
                    },
                )
                return False

            result = await self._add_product_to_deal_internal(
                deal_id=deal_id,
                product_id=product["ID"],
                product_name=product.get(
                    "NAME", product_name if product_name else "Товар"
                ),
                quantity=quantity,
                price=price or product.get("PRICE", 0),
                discount=discount,
            )

            if result:
                logger.info(
                    "Товар успешно добавлен к сделке",
                    extra={
                        "deal_id": deal_id,
                        "product_xml_id": product_xml_id,
                        "product_id": product["ID"],
                        "quantity": quantity,
                    },
                )
            else:
                logger.warning(
                    "Не удалось добавить товар к сделке",
                    extra={"deal_id": deal_id, "product_id": product["ID"]},
                )

            return result

        except Exception as e:
            logger.error(
                "Ошибка при добавлении товара к сделке",
                extra={
                    "deal_id": deal_id,
                    "product_xml_id": product_xml_id,
                    "error": str(e),
                },
                exc_info=True,
            )
            return False

    async def _find_product_by_xml_id(
        self, xml_id: str
    ) -> dict[str, Any] | None:
        """
        Находит товар по XML_ID.

        Args:
            xml_id: XML_ID товара

        Returns:
            dict: Данные товара или None если не найден
        """
        try:
            deal_bitrix_client = self.entities_bitrix_client.deal_bitrix_client
            method = "crm.product.list"
            params = deal_bitrix_client._prepare_params(
                select=["ID", "NAME", "PRICE", "XML_ID"],
                filter={"XML_ID": xml_id},
            )

            response = await deal_bitrix_client.bitrix_client.call_api(
                method, params
            )
            products_data = response.get("result", {})
            products: list[dict[str, Any]] = []
            if isinstance(products_data, dict) and "products" in products_data:
                products = products_data["products"]
            elif isinstance(products_data, list):
                products = products_data

            if products and len(products) > 0:
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

    async def _add_product_to_deal_internal(
        self,
        deal_id: int,
        product_id: int,
        product_name: str,
        quantity: int = 0,
        price: float = 0,
        discount: float | None = None,
    ) -> bool:
        """
        Внутренний метод добавления товара к сделке.

        Args:
            deal_id: ID сделки
            product_id: ID товара
            product_name: Название товара
            quantity: Количество
            price: Цена
            discount: Скидка

        Returns:
            bool: True если операция успешна
        """
        try:
            product_data: dict[str, Any] = {
                "owner_id": deal_id,
                "owner_type": EntityTypeAbbr.DEAL,
                "product_id": product_id,
                "product_name": product_name,
                "quantity": quantity,
                "price": price,
            }
            if discount is not None:
                product_data["discount_sum"] = discount

            products = ListProductEntity(
                result=[ProductEntityCreate(**product_data)]
            )
            result = await self._set_product_rows(
                owner_id=deal_id,
                owner_type=EntityTypeAbbr.DEAL,
                products=products,
            )

            success = bool(result.count_products)

            if not success:
                logger.warning(
                    "Не удалось добавить товарные позиции",
                    extra={"deal_id": deal_id, "product_id": product_id},
                )

            return success

        except BitrixApiError as e:
            logger.error(
                "Ошибка Bitrix API при добавлении товара",
                extra={
                    "deal_id": deal_id,
                    "product_id": product_id,
                    "error": str(e),
                },
            )
            return False
        except Exception as e:
            logger.error(
                "Неожиданная ошибка при добавлении товара",
                extra={
                    "deal_id": deal_id,
                    "product_id": product_id,
                    "error": str(e),
                },
                exc_info=True,
            )
            return False

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
            ListProductEntity: Результат операции

        Raises:
            BitrixApiError: При ошибке API Bitrix
        """
        logger.debug(
            "Добавление товарных позиций",
            extra={"owner_type": owner_type, "owner_id": owner_id},
        )
        bitrix_client = (
            self.entities_bitrix_client.deal_bitrix_client.bitrix_client
        )
        # Формируем параметры запроса
        params: dict[str, Any] = {
            "ownerId": owner_id,
            "ownerType": owner_type.value,
            "productRows": products.to_bitrix_dict(),
        }
        response = await bitrix_client.call_api(
            "crm.item.productrow.set", params=params
        )

        # Проверяем ответ
        if (
            not (entity_data := response.get("result"))
            or "productRows" not in entity_data
        ):
            error_msg = (
                f"Не удалось добавить товарные позиции для "
                f"{owner_type.value} ID={owner_id}"
            )
            logger.error(error_msg)
            raise BitrixApiError(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error_description=error_msg,
            )
        logger.debug(
            "Товарные позиции успешно добавлены",
            extra={
                "owner_type": owner_type,
                "owner_id": owner_id,
                "products_count": len(entity_data["productRows"]),
            },
        )

        return ListProductEntity(result=entity_data["productRows"])

    async def _add_deal_comment(
        self, deal_id: int, product_name: str, comment: str | None = None
    ) -> bool:
        """
        Добавляет комментарий к сделке.

        Args:
            deal_id: ID сделки
            product_name: Название товара
            comment: Дополнительный комментарий

        Returns:
            bool: True если комментарий успешно добавлен
        """
        try:
            deal_data: dict[str, Any] = {
                "external_id": deal_id,
                "comments": self._get_complex_comment(product_name, comment),
            }

            deal_update = DealUpdate(**deal_data)
            await self.entities_bitrix_client.deal_bitrix_client.update(
                deal_update
            )

            logger.debug(
                "Комментарий добавлен к сделке", extra={"deal_id": deal_id}
            )

            return True

        except BitrixApiError as e:
            logger.error(
                "Ошибка Bitrix API при добавлении комментария",
                extra={"deal_id": deal_id, "error": str(e)},
            )
            return False
        except Exception as e:
            logger.error(
                "Неожиданная ошибка при добавлении комментария",
                extra={"deal_id": deal_id, "error": str(e)},
                exc_info=True,
            )
            return False

    def _get_complex_comment(
        self, product_name: str, comment: str | None = None
    ) -> str:
        comments: list[str] = []
        if comment:
            comments.append(comment)
        comments.append(f"Товар: {product_name}")
        return "\n".join(comments)

    async def _add_timeline_comment_to_deal(
        self, deal_id: int, message: str
    ) -> bool:
        """
        Добавляет комментарий в ленту временной шкалы сделки.

        Args:
            deal_id: ID сделки
            message: Текст сообщения

        Returns:
            bool: True если сообщение успешно добавлено
        """
        try:
            method = "crm.timeline.comment.add"
            params: dict[str, Any] = {
                "fields": {
                    "ENTITY_ID": deal_id,
                    "ENTITY_TYPE": "deal",
                    "COMMENT": message,
                }
            }

            bitrix_client = (
                self.entities_bitrix_client.deal_bitrix_client.bitrix_client
            )
            response = await bitrix_client.call_api(method, params)

            if response.get("result"):
                logger.info(
                    "Сообщение добавлено в ленту сделки",
                    extra={"deal_id": deal_id, "message_length": len(message)},
                )
                return True
            else:
                logger.error(
                    "Ошибка при добавлении сообщения в ленту сделки",
                    extra={"deal_id": deal_id, "response": response},
                )
                return False

        except Exception as e:
            logger.error(
                "Неожиданная ошибка при добавлении сообщения в ленту сделки",
                extra={"deal_id": deal_id, "error": str(e)},
                exc_info=True,
            )
            return False
