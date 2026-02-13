from typing import Sequence
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.supplier_models import SourceColumnMapping
from schemas.supplier_schemas import (
    ImportColumnMappingCreate,
    ImportColumnMappingUpdate,
)

from .base_repository import BaseRepository


class ColumnMappingRepository(BaseRepository[SourceColumnMapping]):
    """Репозиторий для работы с маппингами колонок."""

    model = SourceColumnMapping

    def __init__(self, session: AsyncSession):
        super().__init__(session, entity_name="ColumnMapping")

    async def get_by_config(
        self, config_id: UUID
    ) -> Sequence[SourceColumnMapping]:
        """Получить все маппинги для конфигурации."""
        self.logger.info(
            "Fetching column mappings", extra={"config_id": str(config_id)}
        )

        stmt = (
            select(self.model)
            .where(self.model.config_id == config_id)
            .order_by(self.model.display_order)
        )

        result = await self._execute_query(
            stmt, operation="get_mappings", config_id=str(config_id)
        )

        mappings = result.scalars().all()

        self.logger.info(
            "Fetched column mappings",
            extra={"config_id": str(config_id), "count": len(mappings)},
        )

        return mappings  # type: ignore[no-any-return]

    async def create_bulk(
        self,
        config_id: UUID,
        mappings_data: list[
            ImportColumnMappingCreate | ImportColumnMappingUpdate
        ],
    ) -> list[SourceColumnMapping]:
        """Создать несколько маппингов."""
        self.logger.info(
            "Creating bulk column mappings",
            extra={"config_id": str(config_id), "count": len(mappings_data)},
        )

        mappings: list[SourceColumnMapping] = []
        for data in mappings_data:
            mapping = SourceColumnMapping(
                config_id=config_id, **data.model_dump(exclude_unset=True)
            )
            self.session.add(mapping)
            mappings.append(mapping)

        await self._flush("create_bulk_mappings")
        await self._commit("create_bulk_mappings")

        self.logger.info(
            "Bulk column mappings created successfully",
            extra={"config_id": str(config_id), "count": len(mappings)},
        )

        return mappings

    async def delete_by_config(self, config_id: UUID) -> int:
        """Удалить все маппинги конфигурации."""
        self.logger.info(
            "Deleting all mappings for config",
            extra={"config_id": str(config_id)},
        )

        stmt = delete(SourceColumnMapping).where(
            SourceColumnMapping.config_id == config_id
        )

        result = await self._execute_query(
            stmt,
            operation="delete_mappings_by_config",
            config_id=str(config_id),
        )

        await self._commit("delete_mappings_by_config")
        deleted_count = result.rowcount

        self.logger.info(
            "Deleted mappings",
            extra={
                "config_id": str(config_id),
                "count": int(deleted_count) if deleted_count else 0,
            },
        )

        return deleted_count  # type: ignore[no-any-return]
