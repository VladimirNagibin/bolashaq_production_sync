from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

# from core.logger import logger
from models.supplier_models import SupplierComplect
from schemas.supplier_schemas import (
    SupplierComplectCreate,
    SupplierComplectUpdate,
)

from .base_repository import BaseRepository


class SupplierComplectRepository(BaseRepository[SupplierComplect]):
    """Репозиторий для работы с комплектующими."""

    model = SupplierComplect

    def __init__(self, session: AsyncSession):
        super().__init__(session, entity_name="SupplierComplect")

    async def get_by_product(
        self, product_id: UUID
    ) -> list[SupplierComplectCreate]:
        """Получить все комплектующие товара."""
        stmt = select(self.model).where(
            self.model.supplier_product_id == product_id
        )
        result = await self._execute_query(
            stmt, operation="get_complects_by_product"
        )
        complects = result.scalars().all()
        return [SupplierComplectCreate.model_validate(c) for c in complects]

    async def create_bulk(
        self, product_id: UUID, complects: list[SupplierComplectUpdate]
    ) -> list[SupplierComplectCreate]:
        """Создать несколько комплектующих."""
        items: list[SupplierComplect] = []
        for comp_data in complects:
            comp = self.model(
                supplier_product_id=product_id,
                **comp_data.model_dump(exclude_unset=True)
            )
            self.session.add(comp)
            items.append(comp)

        await self._flush("create_bulk_complects")
        return [SupplierComplectCreate.model_validate(c) for c in items]

    async def delete_by_product(self, product_id: UUID) -> int:
        """Удалить все комплектующие товара."""
        stmt = delete(self.model).where(
            self.model.supplier_product_id == product_id
        )
        result = await self._execute_query(
            stmt, operation="delete_complects_by_product"
        )
        await self._commit("delete_complects_by_product")
        return int(result.rowcount)
