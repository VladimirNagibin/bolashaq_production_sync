from typing import Any
from uuid import UUID

from sqlalchemy import and_, delete, insert, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, selectinload

# from core.logger import logger
from core.exceptions.repo_exceptions import (
    DuplicateEntityError,
    EntityNotFoundError,
)
from models.supplier_models import SupplierProduct, SupplierProductChangeLog
from schemas.enums import SourceKeyField, SourcesProductEnum
from schemas.supplier_schemas import (
    SupplierCharacteristicUpdate,
    SupplierComplectUpdate,
    SupplierProductCreate,
    SupplierProductDetail,
    SupplierProductUpdate,
)

from .base_repository import BaseRepository
from .change_log_repo import ChangeLogRepository
from .supplier_characteristic_repo import SupplierCharacteristicRepository
from .supplier_complect_repo import SupplierComplectRepository


class SupplierProductRepository(BaseRepository[SupplierProduct]):
    """Репозиторий для работы с товарами поставщиков."""

    model = SupplierProduct

    def __init__(self, session: AsyncSession):
        super().__init__(session, entity_name="SupplierProduct")
        self._characteristic_repo: SupplierCharacteristicRepository | None = (
            None
        )
        self._complect_repo: SupplierComplectRepository | None = None
        self._change_log_repo: ChangeLogRepository | None = None

    @property
    def characteristic_repo(self) -> SupplierCharacteristicRepository:
        if not self._characteristic_repo:
            self._characteristic_repo = SupplierCharacteristicRepository(
                self.session
            )
        return self._characteristic_repo

    @property
    def complect_repo(self) -> SupplierComplectRepository:
        if not self._complect_repo:
            self._complect_repo = SupplierComplectRepository(self.session)
        return self._complect_repo

    @property
    def change_log_repo(self) -> ChangeLogRepository:
        if not self._change_log_repo:
            self._change_log_repo = ChangeLogRepository(self.session)
        return self._change_log_repo

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
            await self.characteristic_repo.create_bulk(
                product.id, characteristics
            )

        # Добавляем комплектующие
        if complects:
            await self.complect_repo.create_bulk(product.id, complects)

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
        self,
        product_id: UUID,
        product_data: SupplierProductUpdate,
        characteristics: list[SupplierCharacteristicUpdate] | None = None,
        complects: list[SupplierComplectUpdate] | None = None,
        is_unlinked: bool = False,
    ) -> SupplierProductDetail:
        """Обновить товар поставщика."""
        self.logger.info(
            "Updating supplier product", extra={"product_id": str(product_id)}
        )

        existing = await self.get_by_id(product_id)
        if not existing:
            raise EntityNotFoundError("SupplierProduct", product_id)

        if characteristics is not None:
            await self.characteristic_repo.delete_by_product(product_id)

        if complects is not None:
            await self.complect_repo.delete_by_product(product_id)

        update_data = product_data.model_dump(
            exclude_unset=True, exclude_none=True
        )
        if is_unlinked:
            update_data["product_id"] = None

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

        # Добавляем характеристики
        if characteristics:
            await self.characteristic_repo.create_bulk(
                product_id, characteristics
            )

        # Добавляем комплектующие
        if complects:
            await self.complect_repo.create_bulk(product_id, complects)

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
        limit: int = 10000,
        source: SourcesProductEnum | None = None,
        is_validated: bool | None = None,
        should_export: bool | None = None,
        external_ids: list[int] | None = None,
        codes: list[str] | None = None,
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
        if external_ids is not None and external_ids:
            stmt = stmt.where(self.model.external_id.in_(external_ids))
        if codes is not None and codes:
            stmt = stmt.where(self.model.code.in_(codes))

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

    async def create_products(
        self,
        products: list[SupplierProductCreate],
        key_field: SourceKeyField,
        batch_size: int = 1000,
        skip_duplicate_check: bool = False,
    ) -> list[SupplierProductDetail]:
        """
        Пакетное создание товаров поставщиков.

        Args:
            products: Список товаров для создания
            batch_size: Размер батча для вставки
            skip_duplicate_check: Пропустить проверку на дубликаты
            (для ускорения)

        Returns:
            List[SupplierProductDetail]: Созданные товары
        """
        if not products:
            self.logger.info("No products to create")
            return []

        self.logger.info(
            f"Batch creating {len(products)} supplier products",
            extra={
                "batch_size": batch_size,
                "skip_duplicate_check": skip_duplicate_check,
            },
        )

        created_products: list[SupplierProductDetail] = []

        try:
            # Проверка на дубликаты (опционально)
            if not skip_duplicate_check:
                products = await self._filter_duplicates(products, key_field)

            # Разбиваем на батчи для оптимизации
            for i in range(0, len(products), batch_size):
                batch = products[i : i + batch_size]

                # Преобразуем схемы в словари для вставки
                batch_dicts: list[dict[str, Any]] = []
                for product in batch:
                    product_dict = product.model_dump(exclude_unset=True)
                    # Добавляем обязательные поля
                    # product_dict.setdefault("is_validated", False)
                    # product_dict.setdefault("should_export_to_crm", False)
                    batch_dicts.append(product_dict)

                # Выполняем массовую вставку
                stmt = (
                    insert(self.model)
                    .values(batch_dicts)
                    .returning(self.model)
                )
                result = await self._execute_query(
                    stmt,
                    operation="batch_create_products",
                    batch_num=i // batch_size + 1,
                    batch_size=len(batch),
                )

                inserted_rows = result.scalars().all()

                # Преобразуем в детальные схемы
                for row in inserted_rows:
                    created_products.append(
                        SupplierProductDetail.model_validate(row)
                    )

                # Сбрасываем после каждого батча для получения ID
                await self._flush(
                    f"batch_create_products_batch_{i//batch_size + 1}"
                )

                self.logger.debug(
                    f"Created batch {i//batch_size + 1}: "
                    f"{len(inserted_rows)} products"
                )

            # Финальный коммит
            await self._commit("batch_create_products")

            self.logger.info(
                f"Successfully created {len(created_products)} products in "
                f"{(len(products) + batch_size - 1) // batch_size} batches"
            )

        except Exception as e:
            await self.session.rollback()
            self.logger.error(
                f"Failed to batch create products: {str(e)}", exc_info=True
            )
            raise

        return created_products

    async def update_products(
        self,
        products: list[SupplierProductUpdate],
        key_field: SourceKeyField,
        source: SourcesProductEnum,
        batch_size: int = 1000,
        update_existing_only: bool = True,
    ) -> list[SupplierProductDetail]:
        """
        Пакетное обновление товаров поставщиков.

        Args:
            products: Список товаров для обновления
            batch_size: Размер батча для обновления
            update_existing_only: Обновлять только существующие записи

        Returns:
            List[SupplierProductDetail]: Обновленные товары
        """
        if not products:
            self.logger.info("No products to update")
            return []

        self.logger.info(
            f"Batch updating {len(products)} supplier products",
            extra={
                "batch_size": batch_size,
                "update_existing_only": update_existing_only,
            },
        )

        updated_products = []
        # failed_updates = []

        try:
            # Получаем существующие товары для проверки
            existing_map = await self._get_existing_products_map(
                products, key_field, source
            )

            # Разбиваем на батчи
            for i in range(0, len(products), batch_size):
                batch = products[i : i + batch_size]
                batch_updates: list[dict[str, Any]] = []

                for product_update in batch:
                    # Пропускаем если товар не существует
                    if (
                        f"ext:{product_update.external_id}" not in existing_map
                        and update_existing_only
                    ):
                        self.logger.debug(
                            "Skipping update for non-existent product",
                            extra={"external_id": product_update.external_id},
                        )
                        continue

                    # Формируем данные для обновления
                    update_data = product_update.model_dump(
                        exclude_unset=True, exclude_none=True
                    )
                    # Определяем условие для обновления
                    if (
                        key_field == SourceKeyField.EXTERNAL_ID
                        and product_update.external_id
                    ):
                        where_clause = (
                            self.model.external_id
                            == product_update.external_id
                        )
                    elif (
                        key_field == SourceKeyField.CODE
                        and product_update.code
                    ):
                        where_clause = self.model.code == product_update.code
                    else:
                        self.logger.warning(
                            "Skipping update: no identifier provided",
                            extra={"product": product_update.model_dump()},
                        )
                        continue

                    # Добавляем обновление в батч
                    batch_updates.append(
                        {"where": where_clause, "values": update_data}
                    )

                if not batch_updates:
                    continue

                # Выполняем обновления в батче
                batch_updated = await self._execute_batch_updates(
                    batch_updates, batch_num=i // batch_size + 1
                )

                updated_products.extend(batch_updated)

                self.logger.debug(
                    f"Updated batch {i//batch_size + 1}: "
                    f"{len(batch_updated)} products"
                )

            # Получаем полные данные обновленных товаров
            result = []
            for product in updated_products:
                detail = await self.get_with_relations(product.id)
                if detail:
                    result.append(detail)

            # Финальный коммит
            await self._commit("batch_update_products")

            self.logger.info(
                f"Successfully updated {len(result)} products in "
                f"{(len(products) + batch_size - 1) // batch_size} batches"
            )

        except Exception as e:
            await self.session.rollback()
            self.logger.error(
                f"Failed to batch update products: {str(e)}", exc_info=True
            )
            raise

        return result

    async def upsert_products(
        self,
        products: list[SupplierProductCreate],
        key_field: SourceKeyField,
        source: SourcesProductEnum,
        key_fields: list[str] | None = None,
        batch_size: int = 1000,
    ) -> list[SupplierProductDetail]:
        """
        Пакетное создание или обновление товаров (upsert).

        Args:
            products: Список товаров для upsert
            key_fields: Поля для определения уникальности
                (по умолчанию ['source', 'external_id'])
            batch_size: Размер батча

        Returns:
            List[SupplierProductDetail]: Созданные/обновленные товары
        """
        if not products:
            return []

        if key_fields is None:
            key_fields = ["source", "external_id"]

        self.logger.info(
            f"Batch upserting {len(products)} products",
            extra={"key_fields": key_fields},
        )

        # Разделяем на создание и обновление
        to_create = []
        to_update = []

        # Получаем существующие записи
        existing_map = await self._get_products_map_by_keys(
            products, key_fields, source
        )

        for product in products:
            key = self._build_composite_key(product, key_fields)
            if key in existing_map:
                # Существующий товар - готовим обновление
                # existing = existing_map[key]
                update_data = SupplierProductUpdate(
                    external_id=product.external_id,
                    code=product.code,
                    **product.model_dump(
                        exclude={"source", "external_id", "code"},
                        exclude_unset=True,
                    ),
                )
                to_update.append(update_data)
            else:
                # Новый товар
                to_create.append(product)

        self.logger.debug(
            f"Upsert split: {len(to_create)} to create, "
            f"{len(to_update)} to update"
        )

        # Выполняем создание и обновление
        created = await self.create_products(
            to_create, batch_size, skip_duplicate_check=True
        )
        updated = await self.update_products(to_update, batch_size, source)

        return created + updated

    async def _filter_duplicates(
        self,
        products: list[SupplierProductCreate],
        key_field: SourceKeyField,
    ) -> list[SupplierProductCreate]:
        """Фильтрация дубликатов перед созданием."""

        unique_products: list[SupplierProductCreate] = []
        seen_keys: set[str] = set()

        for product in products:
            # Проверяем по source + code или source + external_id
            if key_field == SourceKeyField.EXTERNAL_ID:
                key = f"{product.source.value}:ext:{product.external_id}"
            elif key_field == SourceKeyField.CODE:
                key = f"{product.source.value}:code:{product.code}"
            else:
                # Нет уникального идентификатора - пропускаем
                self.logger.warning(
                    "Skipping product without unique identifier",
                    extra={"product": product.model_dump()},
                )
                continue

            if key in seen_keys:
                self.logger.debug(f"Duplicate product skipped: {key}")
                continue

            # Проверяем существование в БД
            existing = None
            if key_field == SourceKeyField.EXTERNAL_ID:
                existing = await self.get_by_source_external_id(
                    product.source, product.external_id
                )
            elif key_field == SourceKeyField.CODE and product.code:
                existing = await self.get_by_source_code(
                    product.source, product.code
                )

            if not existing:
                unique_products.append(product)
                seen_keys.add(key)

        return unique_products

    async def _get_existing_products_map(
        self,
        products: list[SupplierProductUpdate],
        key_field: SourceKeyField,
        source: SourcesProductEnum,
    ) -> dict[str, SupplierProductUpdate]:
        """Получение карты существующих товаров по идентификаторам."""

        external_ids: list[int] = []
        codes: list[str] = []

        for product in products:
            if key_field == SourceKeyField.EXTERNAL_ID and product.external_id:
                external_ids.append(product.external_id)
            elif key_field == SourceKeyField.CODE and product.code:
                codes.append(product.code)

        if not external_ids and not codes:
            return {}

        # Формируем запрос для получения существующих товаров
        filters: dict[str, Any] = {"source": source}
        if external_ids:
            filters["external_ids"] = external_ids
        if codes:
            filters["codes"] = codes

        existing = await self.get_by_filters(**filters)

        # Создаем карту для быстрого доступа
        existing_map: dict[str, SupplierProductUpdate] = {}
        for product in existing:
            if product.external_id:
                existing_map[f"ext:{product.external_id}"] = product
            if product.code:
                existing_map[f"code:{product.code}"] = product

        return existing_map

    async def _get_products_map_by_keys(
        self,
        products: list[SupplierProductCreate],
        key_fields: list[str],
        source: SourcesProductEnum,
    ) -> dict[str, SupplierProductCreate]:
        """Получение карты товаров по составным ключам."""

        # Собираем все значения ключей
        filters: dict[str, Any] = {"source": source}

        if "external_id" in key_fields:
            external_ids = [p.external_id for p in products if p.external_id]
            if external_ids:
                filters["external_ids"] = external_ids

        if "code" in key_fields:
            codes = [p.code for p in products if p.code]
            if codes:
                filters["codes"] = codes

        if not filters:
            return {}

        # Получаем существующие записи
        existing = await self.get_by_filters(**filters)

        # Строим карту по составному ключу
        existing_map = {}
        for product in existing:
            key = self._build_composite_key(product, key_fields)
            existing_map[key] = product

        return existing_map

    def _build_composite_key(
        self,
        product: SupplierProductCreate | SupplierProduct,
        key_fields: list[str],
    ) -> str:
        """Построение составного ключа из указанных полей."""

        key_parts = []
        for field in key_fields:
            value = getattr(product, field, None)
            if value is not None:
                if field == "source" and hasattr(value, "value"):
                    value = value.value
                key_parts.append(f"{field}:{value}")

        return "|".join(key_parts)

    async def _execute_batch_updates(
        self,
        updates: list[dict[str, Any]],
        batch_num: int,
    ) -> list[SupplierProduct]:
        """Выполнение пакетных обновлений."""

        updated_rows = []

        for update_item in updates:
            try:
                stmt = (
                    update(self.model)
                    .where(update_item["where"])
                    .values(**update_item["values"])
                    .returning(self.model)
                )

                result = await self._execute_query(
                    stmt, operation="batch_update", batch_num=batch_num
                )

                updated = result.scalar_one_or_none()
                if updated:
                    updated_rows.append(updated)

            except Exception as e:
                self.logger.error(
                    f"Failed to update product in batch {batch_num}: {str(e)}",
                    extra={"update_data": update_item["values"]},
                )
                continue

        return updated_rows

    async def bulk_delete(
        self,
        product_ids: list[UUID] | None = None,
        source: SourcesProductEnum | None = None,
        older_than_days: int | None = None,
    ) -> int:
        """
        Массовое удаление товаров.

        Args:
            product_ids: Список ID для удаления
            source: Источник для удаления
            older_than_days: Удалить записи старше N дней

        Returns:
            int: Количество удаленных записей
        """

        stmt = delete(self.model)

        if product_ids:
            stmt = stmt.where(self.model.id.in_(product_ids))
        elif source:
            stmt = stmt.where(self.model.source == source.value)
        elif older_than_days:
            from datetime import datetime, timedelta

            # from sqlalchemy import func

            cutoff_date = datetime.now() - timedelta(days=older_than_days)
            stmt = stmt.where(self.model.created_at < cutoff_date)
        else:
            raise ValueError("No delete criteria provided")

        result = await self._execute_query(
            stmt,
            operation="bulk_delete",
            product_ids=product_ids,
            source=source.value if source else None,
        )

        deleted_count = result.rowcount
        await self._commit("bulk_delete")

        self.logger.info(
            f"Bulk deleted {deleted_count} products",
            extra={
                "product_ids_count": len(product_ids) if product_ids else 0,
                "source": source.value if source else None,
            },
        )

        return int(deleted_count)

    async def get_supplier_products_with_unprocessed_logs(
        self, source_value: SourcesProductEnum
    ) -> list[SupplierProduct]:
        """
        Возвращает SupplierProduct по указанному source,
        у которых needs_review=True.
        Подгружает связанные Product и только те SupplierProductChangeLog,
        у которых is_processed=False.
        """
        query = (
            select(SupplierProduct)
            .outerjoin(
                SupplierProductChangeLog,
                and_(
                    SupplierProductChangeLog.supplier_product_id
                    == SupplierProduct.id,
                    SupplierProductChangeLog.is_processed.is_(False),
                ),
            )
            .where(SupplierProduct.source == source_value)
            .where(SupplierProduct.needs_review)
            .options(
                contains_eager(SupplierProduct.change_logs),
                selectinload(SupplierProduct.product),
            )
            .order_by(SupplierProduct.id)
            .distinct()
        )

        result = await self._execute_query(
            query,
            operation="get_supplier_products_with_unprocessed_logs",
            source_value=source_value.value,
        )

        products = result.unique().scalars().all()

        self.logger.info(
            "Fetched supplier products need review",
            extra={"source": str(source_value), "count": len(products)},
        )

        return products  # type: ignore[no-any-return]

    async def get_supplier_products_by_source(
        self, source_value: SourcesProductEnum
    ) -> list[SupplierProduct]:
        """
        Возвращает SupplierProduct по указанному source,
        у которых needs_review=True.
        Подгружает связанные Product и только те SupplierProductChangeLog,
        у которых is_processed=False.
        """
        query = (
            select(SupplierProduct)
            .where(SupplierProduct.source == source_value)
            .where(SupplierProduct.needs_review)
            .order_by(SupplierProduct.name)
        )

        result = await self._execute_query(
            query,
            operation="get_supplier_products_by_source_for_review",
            source_value=source_value.value,
        )

        products = result.scalars().all()

        self.logger.info(
            "Fetched supplier products need review",
            extra={"source": str(source_value), "count": len(products)},
        )

        return products  # type: ignore[no-any-return]

    async def get_category_mapping(
        self, source: SourcesProductEnum | None = None
    ) -> dict[tuple[str, str | None], int]:
        """
        Асинхронная версия получения словаря соответствия категорий.
        """
        # Строим запрос
        stmt = (
            select(
                SupplierProduct.supplier_category,
                SupplierProduct.supplier_subcategory,
                SupplierProduct.internal_section_id,
            )
            .where(
                and_(
                    SupplierProduct.supplier_category.is_not(None),
                    SupplierProduct.supplier_category != "",
                    SupplierProduct.internal_section_id.is_not(None),
                )
            )
            .distinct()
        )

        if source:
            stmt = stmt.where(SupplierProduct.source == source)

        result = await self._execute_query(
            stmt,
            operation="get_category_mapping",
            source=source.value if source else None,
        )
        rows = result.all()

        # Формируем словарь
        mapping: dict[tuple[str, str | None], int] = {}
        for category, subcategory, section_id in rows:
            # Обрабатываем подкатегорию
            if subcategory in (None, ""):
                subcategory = None
            mapping[(category, subcategory)] = section_id

        return mapping
