from typing import Any
from uuid import UUID

from sqlalchemy import and_, delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# from core.logger import logger
from core.exceptions.repo_exceptions import (
    DuplicateEntityError,
    EntityNotFoundError,
)
from models.supplier_models import SupplierProduct
from schemas.enums import SourcesProductEnum
from schemas.supplier_schemas import (
    SupplierCharacteristicUpdate,
    SupplierComplectUpdate,
    SupplierProductCreate,
    SupplierProductDetail,
    SupplierProductUpdate,
)

from .base_repository import BaseRepository
from .supplier_characteristic_repo import SupplierCharacteristicRepository
from .supplier_complect_repo import SupplierComplectRepository


class SupplierProductRepository(BaseRepository[SupplierProduct]):
    """Репозиторий для работы с товарами поставщиков."""

    model = SupplierProduct

    def __init__(self, session: AsyncSession):
        super().__init__(session, entity_name="SupplierProduct")

    async def create(
        self,
        product_data: SupplierProductCreate,
        characteristics: list[SupplierCharacteristicUpdate] | None = None,
        complects: list[SupplierComplectUpdate] | None = None,
    ) -> SupplierProductDetail:
        """Создать товар поставщика с характеристиками и комплектующими."""
        self.logger.info(
            "Creating supplier product",
            extra={
                "source": product_data.source.value,
                "code": product_data.code,
            },
        )

        # Проверка на дубликат
        if product_data.code:
            existing = await self.get_by_source_code(
                product_data.source, product_data.code
            )
            if existing:
                raise DuplicateEntityError(
                    "SupplierProduct",
                    source=product_data.source.value,
                    code=product_data.code,
                )
        if product_data.external_id:
            existing = await self.get_by_source_external_id(
                product_data.source, product_data.external_id
            )
            if existing:
                raise DuplicateEntityError(
                    "SupplierProduct",
                    source=product_data.source.value,
                    external_id=product_data.external_id,
                )

        # Создаём товар
        product = self.model(**product_data.model_dump(exclude_unset=True))
        self.session.add(product)
        await self._flush("create_product")

        # Добавляем характеристики
        if characteristics:
            char_repo = SupplierCharacteristicRepository(self.session)
            await char_repo.create_bulk(product.id, characteristics)

        # Добавляем комплектующие
        if complects:
            comp_repo = SupplierComplectRepository(self.session)
            await comp_repo.create_bulk(product.id, complects)

        await self._commit("create_product")

        # Получаем полный товар со всеми связями
        result = await self.get_with_relations(product.id)

        self.logger.info(
            "Supplier product created successfully",
            extra={"product_id": str(product.id)},
        )

        return result

    async def get_with_relations(
        self, product_id: UUID
    ) -> SupplierProductDetail | None:
        """Получить товар со всеми связями."""
        self.logger.info(
            "Fetching supplier product with relations",
            extra={"product_id": str(product_id)},
        )

        stmt = (
            select(self.model)
            .where(self.model.id == product_id)
            .options(
                selectinload(self.model.characteristics),
                selectinload(self.model.complects),
            )
        )

        result = await self._execute_query(
            stmt,
            operation="get_product_with_relations",
            product_id=str(product_id),
        )

        product = result.scalar_one_or_none()

        if not product:
            self.logger.warning(
                "Supplier product not found",
                extra={"product_id": str(product_id)},
            )
            return None

        self.logger.info(
            "Supplier product fetched successfully",
            extra={
                "product_id": str(product_id),
                "characteristics_count": len(product.characteristics),
                "complects_count": len(product.complects),
            },
        )

        return SupplierProductDetail.model_validate(product)

    async def get_by_source_code(
        self, source: SourcesProductEnum, code: str
    ) -> SupplierProductCreate | None:
        """Получить товар по источнику и коду."""
        self.logger.info(
            "Fetching product by source and code",
            extra={"source": source.value, "code": code},
        )

        stmt = select(self.model).where(
            and_(self.model.source == source.value, self.model.code == code)
        )

        result = await self._execute_query(
            stmt,
            operation="get_product_by_source_code",
            source=source.value,
            code=code,
        )

        product = result.scalar_one_or_none()

        if product:
            return SupplierProductCreate.model_validate(product)
        return None

    async def get_by_source_external_id(
        self,
        source: SourcesProductEnum,
        external_id: int,
    ) -> SupplierProductCreate | None:
        """Получить товар по источнику и коду."""
        self.logger.info(
            "Fetching product by source and external_id",
            extra={
                "source": source.value,
                "external_id": external_id,
            },
        )

        stmt = select(self.model).where(
            and_(
                self.model.source == source.value,
                self.model.external_id == external_id,
            )
        )

        result = await self._execute_query(
            stmt,
            operation="get_product_by_source_external_id",
            source=source.value,
            external_id=external_id,
        )

        product = result.scalar_one_or_none()

        if product:
            return SupplierProductCreate.model_validate(product)
        return None

    async def update(
        self, product_id: UUID, product_data: SupplierProductUpdate
    ) -> SupplierProductDetail:
        """Обновить товар поставщика."""
        self.logger.info(
            "Updating supplier product", extra={"product_id": str(product_id)}
        )

        existing = await self.get_by_id(product_id)
        if not existing:
            raise EntityNotFoundError("SupplierProduct", product_id)

        update_data = product_data.model_dump(
            exclude_unset=True, exclude_none=True
        )
        if not update_data:
            return await self.get_with_relations(product_id)

        stmt = (
            update(self.model)
            .where(self.model.id == product_id)
            .values(**update_data)
            .returning(self.model)
        )

        result = await self._execute_query(
            stmt, operation="update_product", product_id=str(product_id)
        )

        updated = result.scalar_one()
        await self._commit("update_product")

        self.logger.info(
            "Supplier product updated successfully",
            extra={"product_id": str(product_id)},
        )
        return await self.get_with_relations(updated.id)

    async def delete(self, product_id: UUID) -> bool:
        """Удалить товар поставщика."""
        self.logger.info(
            "Deleting supplier product", extra={"product_id": str(product_id)}
        )

        existing = await self.get_by_id(product_id)
        if not existing:
            raise EntityNotFoundError("SupplierProduct", product_id)

        stmt = delete(self.model).where(self.model.id == product_id)
        await self._execute_query(
            stmt, operation="delete_product", product_id=str(product_id)
        )

        await self._commit("delete_product")

        self.logger.info(
            "Supplier product deleted successfully",
            extra={"product_id": str(product_id)},
        )
        return True

    async def get_unprocessed(
        self, limit: int = 100, source: SourcesProductEnum | None = None
    ) -> list[SupplierProductCreate]:
        """Получить необработанные товары."""
        self.logger.info(
            "Fetching unprocessed products",
            extra={
                "limit": limit,
                "source": source.value if source else "all",
            },
        )

        stmt = (
            select(self.model)
            .where(self.model.is_validated.is_(False))
            .order_by(self.model.created_at)
            .limit(limit)
        )

        if source:
            stmt = stmt.where(self.model.source == source.value)

        result = await self._execute_query(
            stmt, operation="get_unprocessed_products"
        )

        products = result.scalars().all()

        self.logger.info(
            "Fetched unprocessed products", extra={"count": len(products)}
        )

        return [SupplierProductCreate.model_validate(p) for p in products]

    async def mark_as_processed(
        self, product_id: UUID, internal_product_id: UUID | None = None
    ) -> SupplierProductCreate:
        """Отметить товар как обработанный."""
        self.logger.info(
            "Marking product as processed",
            extra={
                "product_id": str(product_id),
                "internal_product_id": (
                    str(internal_product_id) if internal_product_id else None
                ),
            },
        )

        values: dict[str, Any] = {"is_validated": True}
        if internal_product_id:
            values["product_id"] = internal_product_id

        stmt = (
            update(self.model)
            .where(self.model.id == product_id)
            .values(**values)
            .returning(self.model)
        )

        result = await self._execute_query(
            stmt, operation="mark_as_processed", product_id=str(product_id)
        )

        updated = result.scalar_one_or_none()

        if not updated:
            raise EntityNotFoundError("SupplierProduct", product_id)

        await self._commit("mark_as_processed")

        self.logger.info(
            "Product marked as processed",
            extra={"product_id": str(product_id)},
        )
        return SupplierProductCreate.model_validate(updated)

    async def get_by_filters(
        self,
        skip: int = 0,
        limit: int = 100,
        source: SourcesProductEnum | None = None,
        is_validated: bool | None = None,
        should_export: bool | None = None,
        search: str | None = None,
    ) -> list[SupplierProductCreate]:
        """Получить товары с фильтрацией и поиском."""
        self.logger.info(
            "Fetching products with filters",
            extra={
                "skip": skip,
                "limit": limit,
                "source": source.value if source else None,
                "is_validated": is_validated,
                "search": search,
            },
        )

        stmt = select(self.model)

        if source:
            stmt = stmt.where(self.model.source == source.value)
        if is_validated is not None:
            stmt = stmt.where(self.model.is_validated == is_validated)
        if should_export is not None:
            stmt = stmt.where(self.model.should_export_to_crm == should_export)
        if search:
            stmt = stmt.where(
                or_(
                    self.model.name.ilike(f"%{search}%"),
                    self.model.code.ilike(f"%{search}%"),
                    self.model.article.ilike(f"%{search}%"),
                )
            )

        stmt = (
            stmt.order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await self._execute_query(
            stmt, operation="get_products_by_filters"
        )
        products = result.scalars().all()

        return [SupplierProductCreate.model_validate(p) for p in products]

    async def count_by_filters(
        self,
        source: SourcesProductEnum | None = None,
        is_validated: bool | None = None,
        should_export: bool | None = None,
        search: str | None = None,
    ) -> int:
        """Подсчитать количество товаров по фильтрам."""
        from sqlalchemy import func

        stmt = select(func.count()).select_from(self.model)

        if source:
            stmt = stmt.where(self.model.source == source.value)
        if is_validated is not None:
            stmt = stmt.where(self.model.is_validated == is_validated)
        if should_export is not None:
            stmt = stmt.where(self.model.should_export_to_crm == should_export)
        if search:
            stmt = stmt.where(
                or_(
                    self.model.name.ilike(f"%{search}%"),
                    self.model.code.ilike(f"%{search}%"),
                    self.model.article.ilike(f"%{search}%"),
                )
            )

        result = await self._execute_query(
            stmt, operation="count_products_by_filters"
        )
        return int(result.scalar_one())
