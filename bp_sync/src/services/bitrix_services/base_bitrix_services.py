from typing import Any, Generic, Type, TypeVar

from fastapi import status

from core.logger import logger
from core.settings import settings
from schemas.base_schemas import (
    CommonFieldMixin,
    ListResponseSchema,
)

from ..decorators import handle_bitrix_errors
from ..exceptions import BitrixApiError
from .bitrix_api_client import BitrixAPIClient

SchemaTypeCreate = TypeVar("SchemaTypeCreate", bound=CommonFieldMixin)
SchemaTypeUpdate = TypeVar("SchemaTypeUpdate", bound=CommonFieldMixin)


class BaseBitrixEntityClient(Generic[SchemaTypeCreate, SchemaTypeUpdate]):
    """Базовый клиент для работы с сущностями Bitrix"""

    entity_name: str
    create_schema: Type[SchemaTypeCreate]
    update_schema: Type[SchemaTypeUpdate]

    def __init__(self, bitrix_client: BitrixAPIClient):
        self.bitrix_client = bitrix_client

    def _get_method(
        self,
        action: str,
        entity_type_id: int | None = None,
        crm: bool = True,
    ) -> str:
        """
        Формирует имя метода API.

        Args:
            action: Действие (add, get, update, delete, list)
            entity_type_id: ID типа сущности для универсальных методов
            crm: Является ли сущность CRM-сущностью

        Returns:
            Имя метода API
        """
        prefix = "crm." if crm else ""

        if entity_type_id:
            return f"{prefix}item.{action}"
        else:
            return f"{prefix}{self.entity_name}.{action}"

    def _prepare_params(
        self,
        entity_id: int | str | None = None,
        data: Any = None,
        entity_type_id: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Подготавливает параметры для API-запроса.

        Args:
            entity_id: ID сущности
            data: Данные для создания/обновления
            entity_type_id: ID типа сущности
            **kwargs: Дополнительные параметры

        Returns:
            Параметры запроса
        """
        # params = kwargs.copy()
        params = {k: v for k, v in kwargs.items() if v is not None}
        if entity_id is not None:
            params["id"] = entity_id

        if data is not None:
            params["fields"] = data.to_bitrix_dict()

        if entity_type_id:
            params["entityTypeId"] = entity_type_id

        return params

    def _handle_response(
        self,
        response: dict[str, Any],
        action: str,
        entity_id: int | str | None = None,
        entity_type_id: int | None = None,
        crm: bool = True,
    ) -> Any:
        """
        Обрабатывает ответ API.

        Args:
            response: Ответ API
            action: Выполненное действие
            entity_id: ID сущности
            entity_type_id: ID типа сущности
            crm: Тип сущности

        Returns:
            Результат обработки

        Raises:
            BitrixApiError: При ошибках API
        """
        result = response.get("result")

        # Для универсальных методов (crm.item.*) данные находятся внутри 'item'
        if entity_type_id and action in {"add", "get"}:
            result = result.get("item") if result else None

        if not crm and action in {"add", "get"}:
            result = result.get("product") if result else None

        if not result:
            error = response.get("error", "Unknown error")
            error_description = response.get(
                "error_description", "Unknown error"
            )
            entity_ref = f"ID={entity_id}" if entity_id else ""
            logger.error(
                f"Failed to {action} {self.entity_name} {entity_ref}: {error}",
                extra={
                    "action": action,
                    "entity": self.entity_name,
                    "entity_id": entity_id,
                    "error": error,
                    "error_description": error_description,
                },
            )

            if action == "get":
                raise BitrixApiError(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error=(
                        f"Failed to {action} {self.entity_name} {entity_ref}: "
                        f"{error}"
                    ),
                    error_description=error_description,
                )

            raise BitrixApiError(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error=f"{action}_{self.entity_name}_failed",
                error_description=f"Failed to {action} {self.entity_name}",
            )

        return result

    @handle_bitrix_errors()
    async def create(
        self,
        data: SchemaTypeUpdate,
        entity_type_id: int | None = None,
        crm: bool = True,
    ) -> int | None:
        """Создание новой сущности"""
        entity_title = getattr(data, "title", "")
        logger.info(
            f"Creating new {self.entity_name}: {entity_title}",
            extra={"entity_type_id": entity_type_id, "crm": crm},
        )
        method = self._get_method("add", entity_type_id, crm)
        params = self._prepare_params(data=data, entity_type_id=entity_type_id)

        response = await self.bitrix_client.call_api(
            method=method, params=params
        )
        result = self._handle_response(response, "add")
        created_id = result["id"] if entity_type_id else result
        logger.info(
            (
                f"{self.entity_name.capitalize()} created successfully: "
                f"ID={created_id}"
            ),
            extra={"entity_id": created_id},
        )
        return created_id  # type: ignore[no-any-return]

    @handle_bitrix_errors()
    async def get(
        self,
        entity_id: int | str,
        entity_type_id: int | None = None,
        crm: bool = True,
    ) -> SchemaTypeCreate:
        """Получение сущности по ID"""
        logger.debug(
            f"Fetching {self.entity_name} ID={entity_id}",
            extra={"entity_id": entity_id, "entity_type_id": entity_type_id},
        )

        method = self._get_method("get", entity_type_id, crm)
        params = self._prepare_params(
            entity_id=entity_id,
            entity_type_id=entity_type_id,
        )
        response = await self.bitrix_client.call_api(
            method=method, params=params
        )
        result = self._handle_response(
            response,
            "get",
            entity_id,
            entity_type_id,
            crm,
        )
        return self.create_schema(**result)  # type: ignore[no-any-return]

    @handle_bitrix_errors()
    async def update(
        self,
        data: SchemaTypeUpdate | SchemaTypeCreate,
        entity_type_id: int | None = None,
        crm: bool = True,
    ) -> bool:
        """Обновление сущности"""
        if not data.external_id:
            logger.error("Update failed: Missing entity ID")
            raise ValueError(
                f"{self.entity_name.capitalize()} ID is required for update"
            )

        entity_id = data.external_id
        logger.info(
            f"Updating {self.entity_name} ID={entity_id}",
            extra={"entity_id": entity_id, "entity_type_id": entity_type_id},
        )

        method = self._get_method("update", entity_type_id, crm)
        params = self._prepare_params(
            entity_id=entity_id, data=data, entity_type_id=entity_type_id
        )
        response = await self.bitrix_client.call_api(
            method=method, params=params
        )
        # Для универсальных методов возвращается объект, для обычных - булево
        if entity_type_id:
            success = bool(response.get("result", {}).get("item"))
        else:
            success = response.get("result") is True

        if success:
            logger.info(
                (
                    f"{self.entity_name.capitalize()} updated successfully: "
                    f"ID={entity_id}"
                ),
                extra={"entity_id": entity_id},
            )
        else:
            error = response.get("error", "unknown_error")
            logger.error(
                f"Failed to update {self.entity_name} ID={entity_id}: {error}",
                extra={"entity_id": entity_id, "error": error},
            )

        return success

    @handle_bitrix_errors()
    async def delete(
        self,
        entity_id: int | str,
        entity_type_id: int | None = None,
        crm: bool = True,
    ) -> bool:
        """Удаление сущности по ID"""
        logger.info(
            f"Deleting {self.entity_name} ID={entity_id}",
            extra={"entity_id": entity_id, "entity_type_id": entity_type_id},
        )

        method = self._get_method("delete", entity_type_id, crm)
        params = self._prepare_params(
            entity_id=entity_id, entity_type_id=entity_type_id
        )

        response = await self.bitrix_client.call_api(
            method=method, params=params
        )
        if entity_type_id:
            # Для универсальных методов (crm.item.delete)
            # Успешный ответ может содержать пустой массив в result
            success = "result" in response and response["result"] is not False
        else:
            # Для стандартных методов
            success = response.get("result") is True

        if success:
            logger.info(
                (
                    f"{self.entity_name.capitalize()} deleted successfully: "
                    f"ID={entity_id}"
                ),
                extra={"entity_id": entity_id},
            )
        else:
            error = response.get("error", "unknown_error")
            logger.error(
                f"Failed to delete {self.entity_name} ID={entity_id}: {error}",
                extra={"entity_id": entity_id, "error": error},
            )
        return success

    @handle_bitrix_errors()
    async def list(
        self,
        select: list[str] | None = None,
        filter_entity: dict[str, Any] | None = None,
        order: dict[str, str] | None = None,
        start: int = 0,
        entity_type_id: int | None = None,
        crm: bool = True,
    ) -> ListResponseSchema[SchemaTypeUpdate]:
        """Список сущностей с фильтрацией

        Получает список сущностей из Bitrix24 с возможностью фильтрации,
        сортировки и постраничной выборки.

        Args:
            select: Список полей для выборки.
                - Может содержать маски:
                    '*' - все основные поля (без пользовательских и
                          множественных)
                    'UF_*' - все пользовательские поля (без множественных)
                - По умолчанию выбираются все поля ('*' + 'UF_*')
                - Доступные поля: `crm.{entity_name}.fields`
                - Пример: ["ID", "TITLE", "OPPORTUNITY"]

            filter: Фильтр для выборки сделок.
                - Формат: {поле: значение}
                - Поддерживаемые префиксы для операторов:
                    '>=' - больше или равно
                    '>'  - больше
                    '<=' - меньше или равно
                    '<'  - меньше
                    '@'  - IN (значение должно быть массивом)
                    '!@' - NOT IN (значение должно быть массивом)
                    '%'  - LIKE (поиск подстроки, % не нужен)
                    '=%' - LIKE с указанием позиции (% в начале)
                    '=%%' - LIKE с указанием позиции (% в конце)
                    '=%%%' - LIKE с подстрокой в любой позиции
                    '='  - равно (по умолчанию)
                    '!=' - не равно
                    '!'  - не равно
                - Не работает с полями типа crm_status, crm_contact ...
                - Пример: {">OPPORTUNITY": 1000, "CATEGORY_ID": 1}

            order: Сортировка результатов.
                - Формат: {поле: направление}
                - Направление: "ASC" (по возрастанию) или "DESC" (по убыванию)
                - Пример: {"TITLE": "ASC", "DATE_CREATE": "DESC"}

            start: Смещение для постраничной выборки.
                - Размер страницы фиксирован: 50 записей
                - Формула: start = (N-1) * 50, где N - номер страницы
                - Пример: для 2-й страницы передать 50

        Returns:
            ListResponseSchema: Объект с результатами выборки:
                - result: список сущностей
                - total: общее количество сущностей
                - next: смещение для следующей страницы (если есть)

        Example:
            Получить сделки с фильтрацией и сортировкой:
            ```python
            deals = await client.list(
                select=["ID", "TITLE", "OPPORTUNITY"],
                filter={
                    "CATEGORY_ID": 1,
                    ">OPPORTUNITY": 10000,
                    "<=OPPORTUNITY": 20000,
                    "@ASSIGNED_BY_ID": [1, 6]
                },
                order={"OPPORTUNITY": "ASC"},
                start=0
            )
            ```

        Bitrix API Example:
            ```bash
            curl -X POST \\
            -H "Content-Type: application/json" \\
            -H "Accept: application/json" \\
            -d '{
                "SELECT": ["ID", "TITLE", "OPPORTUNITY"],
                "FILTER": {
                    "CATEGORY_ID": 1,
                    ">OPPORTUNITY": 10000,
                    "<=OPPORTUNITY": 20000,
                    "@ASSIGNED_BY_ID": [1, 6]
                },
                "ORDER": {"OPPORTUNITY": "ASC"},
                "start": 0
            }' \\
            https://example.bitrix24.ru/rest/user_id/webhook/crm.deal.list
            ```
        """
        logger.debug(
            f"Fetching {self.entity_name} list",
            extra={
                "select_fields": len(select) if select else 0,
                "filter_count": len(filter_entity) if filter_entity else 0,
                "start": start,
                "entity_type_id": entity_type_id,
            },
        )

        method = self._get_method("list", entity_type_id, crm)
        params = self._prepare_params(
            entity_type_id=entity_type_id,
            select=select,
            filter=filter_entity,
            order=order,
            start=start,
        )
        response = await self.bitrix_client.call_api(
            method=method, params=params
        )
        result = response.get("result", {})
        # Обработка разных форматов ответа
        if entity_type_id:
            entities = result.get("items", [])
        elif not crm:
            entities = result.get("products", [])
        else:
            entities = result
        total = response.get("total", 0)
        next_page = response.get("next")
        parsed_entities = [self.update_schema(**entity) for entity in entities]
        logger.info(
            f"Fetched {len(parsed_entities)} of {total} {self.entity_name}s",
            extra={
                "fetched_count": len(parsed_entities),
                "total_count": total,
                "has_next_page": next_page is not None,
            },
        )

        return ListResponseSchema(
            result=parsed_entities,
            total=total,
            next=next_page,
        )

    def get_default_create_schema(self, external_id: int | str) -> Any:
        return self.create_schema.get_default_entity(external_id)

    @handle_bitrix_errors()
    async def send_message_b24(
        self, user_id: int, message: str, chat: bool = False
    ) -> bool:
        """Отправка сообщения пользователю в Битрикс24"""
        logger.debug(
            f"Sending message to {user_id}",
            extra={
                "user_id": user_id,
                "is_chat": chat,
                "message_length": len(message),
            },
        )
        params: dict[str, Any] = {
            "CHAT_ID" if chat else "user_id": user_id,
            "message": message,
        }
        try:
            response = await self.bitrix_client.call_api(
                "im.message.add",
                params=params,
            )
            success = bool(response.get("result", False))

            if success:
                logger.debug("Message sent successfully")
            else:
                logger.warning("Failed to send message")

            return success
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False

    def get_link(self, external_id: int | str | None) -> str:
        """Генерирует ссылку на сущность в Bitrix24."""
        return (
            f"{settings.BITRIX_PORTAL}/crm/{self.entity_name}/details/"
            f"{external_id if external_id else ''}/"
        )

    def get_formatted_link(
        self, external_id: int | str | None, titlt: str
    ) -> str:
        """Генерирует форматированную ссылку для Bitrix24."""
        return f"[url={self.get_link(external_id)}]{titlt}[/url]"

    @handle_bitrix_errors()
    async def execute_batch(
        self, commands: dict[str, Any], halt: int = 0
    ) -> Any:
        """
        Выполняет батч-запрос.

        Args:
            commands: Команды для выполнения
            halt: Останавливать ли выполнение при ошибке

        Returns:
            Результаты выполнения команд
        """
        logger.debug(
            "Executing batch request",
            extra={"command_count": len(commands), "halt": halt},
        )

        method = "batch"
        params: dict[str, Any] = {"halt": halt, "cmd": commands}
        response = await self.bitrix_client.call_api(
            method=method, params=params
        )

        return self._handle_response(response, method)

    @property
    def entity_type(self) -> str:
        """Возвращает тип сущности."""
        return self.entity_name
