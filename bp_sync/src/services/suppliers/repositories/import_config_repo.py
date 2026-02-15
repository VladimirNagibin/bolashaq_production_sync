from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.exceptions.repo_exceptions import (
    DuplicateEntityError,
    EntityNotFoundError,
)
from models.supplier_models import SourceImportConfig
from schemas.enums import SourcesProductEnum
from schemas.supplier_schemas import (
    ImportColumnMappingCreate,
    ImportColumnMappingUpdate,
    ImportConfigCreate,
    ImportConfigDetail,
    ImportConfigUpdate,
)

from .base_repository import BaseRepository
from .column_mapping_repo import ColumnMappingRepository


class ImportConfigRepository(BaseRepository[SourceImportConfig]):
    """Репозиторий для работы с конфигурациями импорта."""

    model = SourceImportConfig

    def __init__(self, session: AsyncSession):
        super().__init__(session, entity_name="ImportConfig")

    async def get_by_source(
        self,
        source: SourcesProductEnum,
        config_name: str | None = None,
        active_only: bool = True,
    ) -> ImportConfigDetail | None:
        """Получить конфигурацию по источнику."""
        self.logger.info(
            "Fetching import config",
            extra={
                "source": source.value,
                "config_name": config_name,
                "active_only": active_only,
            },
        )

        stmt = select(self.model).where(self.model.source == source.value)

        if config_name is not None:
            stmt = stmt.where(self.model.config_name == config_name)

        if active_only:
            stmt = stmt.where(self.model.is_active.is_(True))

        stmt = stmt.options(selectinload(self.model.column_mappings))

        result = await self._execute_query(
            stmt,
            operation="get_config",
            source=source.value,
            config_name=config_name,
        )

        config = result.scalar_one_or_none()

        if not config:
            self.logger.warning(
                "Import config not found",
                extra={"source": source.value, "config_name": config_name},
            )
            return None

        self.logger.info(
            "Import config fetched successfully",
            extra={
                "config_id": str(config.id),
                "column_count": (
                    len(config.column_mappings)
                    if config.column_mappings
                    else 0
                ),
            },
        )
        if config:
            return ImportConfigDetail.model_validate(config)
        return None

    async def create(
        self,
        config_data: ImportConfigCreate,
        mappings: (
            list[ImportColumnMappingUpdate | ImportColumnMappingCreate] | None
        ) = None,
    ) -> ImportConfigDetail:
        """Создать конфигурацию импорта с маппингами."""
        self.logger.info(
            "Creating import config",
            extra={
                "source": config_data.source.value,
                "config_name": config_data.config_name,
            },
        )

        # Проверка на дубликат
        existing = await self.get_by_source(
            config_data.source, config_data.config_name, active_only=False
        )
        if existing:
            self.logger.warning(
                "Import config already exists",
                extra={
                    "source": config_data.source.value,
                    "config_name": config_data.config_name,
                    "existing_id": str(existing.id),
                },
            )
            raise DuplicateEntityError(
                "ImportConfig",
                source=config_data.source.value,
                config_name=config_data.config_name,
            )

        # Создаём конфиг
        config = self.model(**config_data.model_dump(exclude_unset=True))
        self.session.add(config)
        await self._flush("create_config")

        # Добавляем маппинги
        if mappings:
            column_repo = ColumnMappingRepository(session=self.session)
            await column_repo.create_bulk(config.id, mappings)

        await self._commit("create_config")

        # Получаем полную конфигурацию с маппингами
        result = await self.get_with_mappings(config.id)

        self.logger.info(
            "Import config created successfully",
            extra={"config_id": str(config.id)},
        )

        return ImportConfigDetail.model_validate(result)

    async def update(
        self, config_id: UUID, config_data: ImportConfigUpdate
    ) -> ImportConfigDetail:
        """Обновить конфигурацию импорта."""
        self.logger.info(
            "Updating import config", extra={"config_id": str(config_id)}
        )

        # Проверяем существование
        existing = await self.get_by_id(config_id)
        if not existing:
            raise EntityNotFoundError("ImportConfig", config_id)

        # Обновляем только переданные поля
        update_data = config_data.model_dump(
            exclude_unset=True, exclude_none=True
        )
        if not update_data:
            return ImportConfigDetail.model_validate(existing)

        stmt = (
            update(self.model)
            .where(self.model.id == config_id)
            .values(**update_data)
            .returning(self.model)
        )

        result = await self._execute_query(
            stmt, operation="update_config", config_id=str(config_id)
        )

        updated = result.scalar_one()
        await self._commit("update_config")

        self.logger.info(
            "Import config updated successfully",
            extra={"config_id": str(config_id)},
        )
        return ImportConfigDetail.model_validate(updated)

    async def delete(self, config_id: UUID) -> bool:
        """Удалить конфигурацию импорта."""
        self.logger.info(
            "Deleting import config", extra={"config_id": str(config_id)}
        )

        # Проверяем существование
        existing = await self.get_by_id(config_id)
        if not existing:
            raise EntityNotFoundError("ImportConfig", config_id)

        stmt = delete(self.model).where(self.model.id == config_id)
        await self._execute_query(
            stmt, operation="delete_config", config_id=str(config_id)
        )

        await self._commit("delete_config")

        self.logger.info(
            "Import config deleted successfully",
            extra={"config_id": str(config_id)},
        )

        return True

    async def get_with_mappings(
        self, config_id: UUID
    ) -> ImportConfigDetail | None:
        """Получить конфигурацию с маппингами."""
        self.logger.info(
            "Fetching import config with mappings",
            extra={"config_id": str(config_id)},
        )

        stmt = (
            select(self.model)
            .where(self.model.id == config_id)
            .options(selectinload(self.model.column_mappings))
        )

        result = await self._execute_query(
            stmt,
            operation="get_config_with_mappings",
            config_id=str(config_id),
        )

        config = result.scalar_one_or_none()

        if not config:
            self.logger.warning(
                "Config not found with mappings", config_id=str(config_id)
            )
            return None

        self.logger.info(
            "Config with mappings fetched successfully",
            extra={
                "config_id": str(config_id),
                "mapping_count": len(config.column_mappings),
            },
        )

        return ImportConfigDetail.model_validate(config)

    async def get_all(
        self, skip: int = 0, limit: int = 100, active_only: bool = False
    ) -> list[ImportConfigCreate]:
        """Получить все конфигурации с пагинацией."""
        self.logger.info(
            "Fetching all import configs", extra={"skip": skip, "limit": limit}
        )

        stmt = select(self.model).offset(skip).limit(limit)

        if active_only:
            stmt = stmt.where(self.model.is_active.is_(True))

        stmt = stmt.order_by(self.model.created_at.desc())

        result = await self._execute_query(stmt, operation="get_all_configs")
        configs = result.scalars().all()

        return [ImportConfigCreate.model_validate(c) for c in configs]
