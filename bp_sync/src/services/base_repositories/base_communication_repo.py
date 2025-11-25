from collections.abc import Awaitable
from typing import Any, Callable, Optional, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from models.bases import IntIdEntity
from schemas.base_schemas import BaseCreateSchema, BaseUpdateSchema
from schemas.enums import COMMUNICATION_TYPES, EntityType

from .base_repository import BaseRepository
from .communications_service import CommunicationService

SchemaTypeCreate = TypeVar("SchemaTypeCreate", bound=BaseCreateSchema)
SchemaTypeUpdate = TypeVar("SchemaTypeUpdate", bound=BaseUpdateSchema)
ModelType = TypeVar("ModelType", bound=IntIdEntity)
ExternalIdType = TypeVar("ExternalIdType", int, str)


class EntityWithCommunicationsRepository(
    BaseRepository[
        ModelType, SchemaTypeCreate, SchemaTypeUpdate, ExternalIdType
    ]
):
    """Базовый репозиторий для сущностей с коммуникациями"""

    entity_type: EntityType
    communication_service: CommunicationService

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.communication_service = CommunicationService(session)

    async def _handle_communications(
        self, entity: Any, data: Any, is_update: bool = False
    ) -> None:
        """Обработчик коммуникаций для create/update операций"""
        for field, comm_type in COMMUNICATION_TYPES.items():
            if comms := getattr(data, field, None):
                if is_update:
                    await self._update_communications(entity, comm_type, comms)
                else:
                    await self._create_communications(entity, comm_type, comms)

    async def _create_communications(
        self, entity: Any, comm_type: Any, comms: list[Any]
    ) -> None:
        """Создает каналы связи для сущности"""
        for comm_schema in comms:
            await self.communication_service.create_communication_channel(
                entity_type=self.entity_type,
                entity_id=entity.external_id,
                comm_schema=comm_schema,
                comm_type=comm_type,
            )

    async def _update_communications(
        self, entity: Any, comm_type: Any, comms: list[Any]
    ) -> None:
        """Обновляет каналы связи для сущности"""
        await self.communication_service.update_communications(
            entity_type=self.entity_type,
            entity_id=entity.external_id,
            comm_type=comm_type,
            new_comms=comms,
        )

    async def _delete_entity_communications(self, external_id: int) -> None:
        """Удаляет все коммуникации сущности"""
        await self.communication_service.delete_communications(
            entity_type=self.entity_type, entity_id=external_id
        )

    async def create(
        self,
        data: SchemaTypeCreate,
        pre_commit_hook: Optional[Callable[..., Awaitable[None]]] = None,
        post_commit_hook: Optional[Callable[..., Awaitable[None]]] = None,
    ) -> ModelType:
        """Создает сущность с обработкой коммуникаций в одной транзакции"""

        async def _combined_pre_commit_hook(
            obj: ModelType, data: SchemaTypeCreate
        ) -> None:
            if pre_commit_hook:
                await pre_commit_hook(obj, data)
            await self._handle_communications(obj, data, is_update=True)

        entity = await super().create(
            data,
            pre_commit_hook=_combined_pre_commit_hook,
            post_commit_hook=post_commit_hook,
        )
        return entity

    async def update(
        self,
        data: SchemaTypeUpdate | SchemaTypeCreate,
        pre_commit_hook: Optional[Callable[..., Awaitable[None]]] = None,
        post_commit_hook: Optional[Callable[..., Awaitable[None]]] = None,
    ) -> ModelType:
        """Обновляет сущность с обработкой коммуникаций в одной транзакции"""

        async def _combined_pre_commit_hook(
            obj: ModelType, data: SchemaTypeUpdate
        ) -> None:
            if pre_commit_hook:
                await pre_commit_hook(obj, data)
            await self._handle_communications(obj, data, is_update=True)

        entity = await super().update(
            data,
            pre_commit_hook=_combined_pre_commit_hook,
            post_commit_hook=post_commit_hook,
        )
        return entity

    async def delete(
        self,
        external_id: ExternalIdType,
        pre_delete_hook: Optional[Callable[..., Awaitable[None]]] = None,
    ) -> bool:
        """Удаляет сущность и её коммуникации в одной транзакции"""

        async def _combined_pre_delete_hook(id: int) -> None:
            if pre_delete_hook:
                await pre_delete_hook(id)
            await self._delete_entity_communications(id)

        return await super().delete(
            external_id,  # type: ignore[arg-type]
            pre_delete_hook=_combined_pre_delete_hook,
        )
