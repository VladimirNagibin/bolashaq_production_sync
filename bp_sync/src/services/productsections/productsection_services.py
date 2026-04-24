import time
from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import logger
from core.settings import settings
from models.productsection_models import Productsection as ProductsectionDB
from schemas.productsection_schemas import Productsection, ProductsectionUpdate

from ..base_repositories.base_repository import BaseRepository
from ..bitrix_services.bitrix_api_client import BitrixAPIClient
from ..bitrix_services.webhook_service import WebhookService
from ..exceptions import ConflictException


class ProductsectionClient(
    BaseRepository[ProductsectionDB, Productsection, Productsection, int]
):

    model = ProductsectionDB
    schema_update_class = ProductsectionUpdate

    def __init__(
        self,
        bitrix_client: BitrixAPIClient,
        session: AsyncSession,
    ) -> None:
        super().__init__(session)
        self.bitrix_client = bitrix_client
        self._webhook_service: WebhookService | None = None

    @property
    def webhook_service(self) -> WebhookService:
        """Сервис для обработки вебхуков с индивидуальной конфигурацией"""
        if self._webhook_service is None:
            self._webhook_service = WebhookService(
                **settings.web_hook_config_productsection
            )
        return self._webhook_service

    async def import_from_bitrix(
        self, start: int = 0
    ) -> tuple[list[ProductsectionDB], int, int]:
        """Импортирует все разделы из Bitrix"""
        productsections, next, total = (
            await self._fetch_bitrix_productsections(start)
        )
        results: list[ProductsectionDB] = []

        for sect in productsections:
            try:
                department = await self._create_or_update(sect)
                if department:
                    results.append(department)
            except Exception as e:
                logger.error(
                    f"Error processing department {sect.external_id}: {str(e)}"
                )

        return results, next, total

    async def _create_or_update(
        self, data: Productsection
    ) -> ProductsectionDB | None:
        """Создает или обновляет запись подразделения"""
        try:
            return await self.create(data=data)
        except ConflictException:
            return await self.update(data=data)

    async def _fetch_bitrix_productsections(
        self, start: int = 0
    ) -> tuple[list[Productsection], int, int]:
        """Получает список подразделений из Bitrix API"""
        response = await self.bitrix_client.call_api(
            "crm.productsection.list", params={"start": start}
        )
        next = response.get("next", 0)
        total = response.get("total", 0)
        if not response.get("result"):
            logger.warning("No sections received from Bitrix")
            return [], next, total

        return (
            [Productsection(**sect) for sect in response["result"]],
            next,
            total,
        )

    async def _get_bitrix_productsection(
        self, productsection_id: int
    ) -> Productsection | None:
        """Получает подразделение из Bitrix API"""
        response = await self.bitrix_client.call_api(
            "crm.productsection.get", params={"id": productsection_id}
        )
        productsection_response = response.get("result")
        if not productsection_response:
            logger.warning(f"Section {productsection_id} not found in Bitrix")
            return None
        return Productsection(**productsection_response)

    async def create_in_bitrix(
        self, data: Productsection
    ) -> Productsection | None:
        params: dict[str, Any] = {
            "fields": data.model_dump(
                by_alias=True,
                exclude_unset=True,
                exclude_none=True,
            )
        }
        response = await self.bitrix_client.call_api(
            "crm.productsection.add", params=params
        )
        if not response.get("result"):
            logger.warning("No departments received from Bitrix")
            return None
        data.external_id = int(response.get("result"))  # type:ignore[arg-type]
        return data

    async def create_in_bitrix_and_db(
        self, data: Productsection
    ) -> ProductsectionDB | None:
        productsection = await self.create_in_bitrix(data)
        if not productsection:
            return None
        return await self._create_or_update(productsection)

    async def productsection_processing(
        self, request: Request
    ) -> JSONResponse:
        """
        Основной метод обработки вебхука секции товаров
        """
        try:
            logger.info("Starting productsection processing webhook")

            webhook_payload = await self.webhook_service.process_webhook(
                request
            )

            if not webhook_payload or not webhook_payload.entity_id:
                logger.warning("Webhook received but no product ID found")
                return self._success_response(
                    "Webhook received but no product ID found",
                    webhook_payload.event if webhook_payload else "--",
                )

            productsection_id = webhook_payload.entity_id
            logger.info(f"Processing product ID: {productsection_id}")
            if webhook_payload.event == "ONCRMPRODUCTSECTIONDELETE":
                await self.set_deleted_in_bitrix(productsection_id)
                return self._success_response(
                    "Product is deleted in Bitrix", webhook_payload.event
                )
            productsection_schema = await self._get_bitrix_productsection(
                productsection_id
            )
            if productsection_schema:
                await self._create_or_update(productsection_schema)
            logger.info(
                "Successfully processed productsection ID: "
                f"{productsection_id}"
            )
            return self._success_response(
                f"Successfully processed product ID: {productsection_id}",
                webhook_payload.event,
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

    def _success_response(self, message: str, event: str) -> JSONResponse:
        """Успешный ответ"""
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": message,
                "event": event,
                "timestamp": time.time(),
            },
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
                "timestamp": time.time(),
            },
        )

    async def get_sections_review_data(
        self, section_data: list[dict[str, Any]]
    ) -> dict[str, Any]:
        try:
            # 1. Получаем все разделы (активные)
            all_sections = await self.get_entities(
                ["external_id", "name", "section_id"]
            )

            # 2. Формируем карту для быстрого поиска
            sections_map = {s.external_id: s for s in all_sections}

            # 3. Формируем список корневых и словарь детей
            # {parent_id: [children]}
            roots: list[dict[str, Any]] = []
            # parent_external_id -> list of sections
            children_map: dict[int, list[dict[str, Any]]] = {}

            for s in all_sections:
                if s.section_id is None:
                    roots.append({"id": s.external_id, "name": s.name})
                else:
                    if s.section_id not in children_map:
                        children_map[s.section_id] = []
                    children_map[s.section_id].append(
                        {"id": s.external_id, "name": s.name}
                    )

            # 4. Вычисляем начальные значения (Defaults)
            # Ищем элемент internal_section_id в review_data
            selected_root_id = None
            selected_child_id = None
            selected_child_name = None
            selected_root_name = None
            # Пытаемся найти ID текущего раздела
            current_section_id = None
            for item in section_data:
                if item.get("field_name") == "internal_section_id":
                    # Приоритет новому значению, иначе текущему
                    val = (
                        item.get("new_value")
                        if item.get("new_value") is not None
                        else item.get("current_product_value")
                    )
                    if val:
                        try:
                            current_section_id = int(val)
                        except (ValueError, TypeError):
                            pass
                    self._update_id_to_name("new_value", item, sections_map)
                    self._update_id_to_name("old_value", item, sections_map)
                    self._update_id_to_name(
                        "current_product_value", item, sections_map
                    )

                    break

            # Если ID найден, находим родителя и ребенка
            if current_section_id and current_section_id in sections_map:
                current_section = sections_map[current_section_id]
                selected_child_id = current_section.external_id

                # Ищем родителя
                if (
                    current_section.section_id
                    and current_section.section_id in sections_map
                ):
                    parent = sections_map[current_section.section_id]
                    selected_root_id = parent.external_id
                    selected_root_name = parent.name
                    selected_child_name = current_section.name
                else:
                    selected_root_id = selected_child_id
                    selected_child_id = None

            # Формируем данные для фронтенда (дерево)
            # Структура: { root_id: [child1, child2] }
            category_tree = {}
            for root in roots:
                category_tree[root["id"]] = children_map.get(root["id"], [])

            return {
                "category_roots": roots,
                "category_children_map": category_tree,  # Словарь детей
                "selected_root_id": selected_root_id,
                "selected_child_id": selected_child_id,
                "selected_child_name": selected_child_name,
                "selected_root_name": selected_root_name,
            }
        except Exception as e:
            logger.error(f"{e}")
            return {}

    def _update_id_to_name(
        self,
        field_name: str,
        data: dict[str, Any],
        sections_map: dict[int, Any],
    ) -> None:
        value = data.get(field_name)
        if not value:
            return
        try:
            value_int = int(value)
            category = sections_map.get(value_int)
            if category:
                data[field_name] = category.name
        except (ValueError, TypeError):
            pass
        return

    async def get_catalog_hierarchy_text(self) -> str:
        data = await self.get_sections_review_data([])
        roots = data.get("category_roots", [])
        children_map = data.get("category_children_map", {})

        lines: list[str] = []
        for root in roots:
            root_id = root["id"]
            root_name = root["name"]
            lines.append(f"- {root_name} (ID: {root_id})")
            children = children_map.get(root_id, [])
            for child in children:
                lines.append(f"  - {child['name']} (ID: {child['id']})")
        return "\n".join(lines)

    async def handle_section_review(
        self,
        form_value: str,
        current_value: int | None,
        section_value: int | None,
        subsection_value: int | None,
    ) -> int | None:
        try:
            all_sections = await self.get_entities(
                ["external_id", "name", "section_id"]
            )

            sections_map = {s.external_id: s for s in all_sections}

            if current_value:
                current_section = sections_map.get(current_value)
                if current_section and current_section.name == form_value:
                    return None
            if subsection_value:
                new_section = sections_map.get(subsection_value)
                if new_section and new_section.name == form_value:
                    return subsection_value
            for section in all_sections:
                if section.name == form_value:
                    if section.section_id is not None:
                        return int(section.external_id)
            product_section_data: dict[str, Any] = {
                "name": form_value,
                "catalog_id": 25,
                "section_id": section_value,
            }
            create_product_section = Productsection(**product_section_data)
            new_product_section = await self.create_in_bitrix_and_db(
                create_product_section
            )
            if new_product_section:
                return int(new_product_section.external_id)
            return None
        except Exception:
            return None
