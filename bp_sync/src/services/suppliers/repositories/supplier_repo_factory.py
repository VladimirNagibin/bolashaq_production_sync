from types import TracebackType
from typing import Optional, Self, Type

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions.repo_exceptions import (
    DatabaseOperationError,
)
from core.logger import logger

from .column_mapping_repo import ColumnMappingRepository
from .import_config_repo import ImportConfigRepository
from .supplier_characteristic_repo import SupplierCharacteristicRepository
from .supplier_complect_repo import SupplierComplectRepository
from .supplier_product_repo import SupplierProductRepository


class RepositoryFactory:
    """Фабрика для создания репозиториев."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = logger

    @property
    def import_config(self) -> ImportConfigRepository:
        return ImportConfigRepository(self.session)

    @property
    def column_mapping(self) -> ColumnMappingRepository:
        return ColumnMappingRepository(self.session)

    @property
    def supplier_product(self) -> SupplierProductRepository:
        return SupplierProductRepository(self.session)

    @property
    def characteristic(self) -> SupplierCharacteristicRepository:
        return SupplierCharacteristicRepository(self.session)

    @property
    def complect(self) -> SupplierComplectRepository:
        return SupplierComplectRepository(self.session)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        if exc_type:
            await self.session.rollback()
            self.logger.error(
                "Transaction rolled back due to error",
                error_type=exc_type.__name__,
                error=str(exc_val),
            )
        else:
            try:
                await self.session.commit()
            except SQLAlchemyError as e:
                await self.session.rollback()
                self.logger.error(
                    "Commit failed in context manager",
                    error=str(e),
                    exc_info=True,
                )
                raise DatabaseOperationError(
                    operation="commit",
                    entity_name="Transaction",
                    detail=str(e),
                    original_error=e,
                ) from e
