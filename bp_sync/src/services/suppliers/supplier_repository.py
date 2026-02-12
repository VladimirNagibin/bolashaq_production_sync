from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import logger
from models.supplier_models import SourceColumnMapping, SourceImportConfig
from schemas.enums import SourcesProductEnum


class SupplierRepository:
    """Репозиторий для обработки товаров из внешних источников"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_supplier_config(
        self, source: SourcesProductEnum, config_name: str | None = None
    ) -> SourceImportConfig | None:
        try:
            stmt = select(SourceImportConfig).where(
                SourceImportConfig.source == source.value,
            )
            if config_name is not None:
                stmt = stmt.where(
                    SourceImportConfig.config_name == config_name
                )

            result = await self.session.execute(stmt)

            entity = result.scalar_one_or_none()
            if not entity:
                logger.debug(
                    f"{SourceImportConfig.__name__} not found: source={source}"
                )
            return entity
        except SQLAlchemyError as e:
            logger.exception(
                f"Database error fetching {SourceImportConfig.__name__} "
                f"source={source}: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database operation failed",
            ) from e

    async def get_mapping_column(
        self, config_id: UUID
    ) -> list[SourceColumnMapping] | None:
        try:
            stmt = select(SourceColumnMapping).where(
                SourceColumnMapping.config_id == config_id,
            )

            result = await self.session.execute(stmt)
            entity = result.scalars().all()
            if not entity:
                logger.debug(
                    f"{SourceColumnMapping.__name__} not found: "
                    "config_id={config_id}"
                )
            return entity  # type: ignore[no-any-return]
        except SQLAlchemyError as e:
            logger.exception(
                f"Database error fetching {SourceImportConfig.__name__} "
                f"config_id={config_id}: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database operation failed",
            ) from e
