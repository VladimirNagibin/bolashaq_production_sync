from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

# from core.logger import logger
from models.supplier_models import SupplierCharacteristic
from schemas.supplier_schemas import (
    SupplierCharacteristicCreate,
    SupplierCharacteristicUpdate,
)

from .base_repository import BaseRepository


class SupplierCharacteristicRepository(BaseRepository[SupplierCharacteristic]):
    """Репозиторий для работы с характеристиками товаров."""

    model = SupplierCharacteristic

    def __init__(self, session: AsyncSession):
        super().__init__(session, entity_name="SupplierCharacteristic")

    async def get_by_product(
        self, product_id: UUID
    ) -> list[SupplierCharacteristicCreate]:
        """Получить все характеристики товара."""
        stmt = select(self.model).where(
            self.model.supplier_product_id == product_id
        )
        result = await self._execute_query(
            stmt, operation="get_characteristics_by_product"
        )
        chars = result.scalars().all()
        return [SupplierCharacteristicCreate.model_validate(c) for c in chars]

    async def create_bulk(
        self,
        product_id: UUID,
        characteristics: list[SupplierCharacteristicUpdate],
    ) -> list[SupplierCharacteristicCreate]:
        """Создать несколько характеристик."""
        chars: list[SupplierCharacteristic] = []
        for char_data in characteristics:
            char = self.model(
                supplier_product_id=product_id,
                **char_data.model_dump(exclude_unset=True)
            )
            self.session.add(char)
            chars.append(char)

        await self._flush("create_bulk_characteristics")
        return [SupplierCharacteristicCreate.model_validate(c) for c in chars]

    async def delete_by_product(self, product_id: UUID) -> int:
        """Удалить все характеристики товара."""
        stmt = delete(self.model).where(
            self.model.supplier_product_id == product_id
        )
        result = await self._execute_query(
            stmt, operation="delete_characteristics_by_product"
        )
        await self._commit("delete_characteristics_by_product")
        return int(result.rowcount)
