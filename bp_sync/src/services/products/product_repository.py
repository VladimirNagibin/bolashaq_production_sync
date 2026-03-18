from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.logger import logger
from models.product_models import Product as ProductDB
from models.product_models import (
    ProductEntity,
    ProductProperty,
    ProductSimpleProperty,
)
from models.user_models import User as UserDB
from schemas.enums import EntityType, EntityTypeAbbr
from schemas.fields import FIELDS_PRODUCT_ALT
from schemas.product_schemas import (
    ListProductEntity,
    ProductCreate,
    ProductEntityCreate,
    ProductUpdate,
)

from ..base_repositories.base_repository import (
    BaseRepository,
)
from ..exceptions import CyclicCallException, DatabaseException

if TYPE_CHECKING:
    from ..users.user_services import UserClient


class ProductRepository(
    BaseRepository[ProductDB, ProductCreate, ProductUpdate, int]
):
    """Contact repository with lazy UserClient loading"""

    model = ProductDB
    schema_update_class = ProductUpdate

    entity_type = EntityType.PRODUCT

    def __init__(
        self,
        session: AsyncSession,
    ):
        super().__init__(session)
        self._user_client: Optional["UserClient"] = None
        self._user_client_initialized = False

    def set_user_client(self, user_client: "UserClient") -> None:
        """Устанавливает UserClient после создания репозитория"""
        self._user_client = user_client
        self._user_client_initialized = True
        logger.debug("UserClient set for ProductRepository")

    @property
    def user_client(self) -> Optional["UserClient"]:
        """Ленивое свойство для доступа к UserClient"""
        if not self._user_client_initialized and self._user_client is None:
            logger.warning(
                "UserClient not initialized in ProductRepository. "
                "Call set_user_client() first or use methods "
                "that don't require UserClient."
            )
        return self._user_client

    async def create_entity(self, data: ProductCreate) -> ProductDB:
        """Создает новый товар с проверкой связанных объектов"""
        await self._check_related_objects(data)
        try:
            await self._create_or_update_related(data)
        except CyclicCallException:
            if not data.external_id:
                logger.error("Update failed: Missing ID")
                raise ValueError("ID is required for update")
            external_id = data.external_id
            data = ProductCreate.get_default_entity(int(external_id))
        return await self.create(
            data=data, post_commit_hook=self._create_properties
        )

    async def _create_properties(
        self, product_db: ProductDB, data: ProductCreate | ProductUpdate
    ) -> None:
        """Создает свойства товара"""
        for field_name in FIELDS_PRODUCT_ALT.get("dict_none_str", []):
            field_value_obj = getattr(data, field_name)
            if field_value_obj and field_value_obj.value:
                prop = ProductSimpleProperty(
                    product_id=product_db.id,
                    property_code=field_name,
                    external_id=field_value_obj.value_id,
                    value=field_value_obj.value,
                )
                self.session.add(prop)

        for field_name in FIELDS_PRODUCT_ALT.get("dict_none_dict", []):
            field_value_obj = getattr(data, field_name)
            if field_value_obj and field_value_obj.value:
                prop = ProductProperty(
                    product_id=product_db.id,
                    property_code=field_name,
                    external_id=field_value_obj.value_id,
                    text_field=field_value_obj.value.text_field,
                    type_field=field_value_obj.value.type_field,
                )
                self.session.add(prop)

    async def update_entity(
        self, data: ProductCreate | ProductUpdate
    ) -> ProductDB:
        """Обновляет существующий контакт"""
        await self._check_related_objects(data)
        await self._create_or_update_related(data)
        return await self.update(
            data=data,
            post_commit_hook=self._update_properties,
        )

    async def _update_properties(
        self, product_db: ProductDB, data: ProductCreate
    ) -> None:
        """
        Полностью обновляет свойства товара: удаляет старые и создает новые.
        Это надежная стратегия, которая предотвращает рассинхронизацию.
        """
        logger.debug(f"Updating properties for product_id: {product_db.id}")

        # 1. Удаляем все существующие свойства для товара
        await self.session.execute(
            delete(ProductSimpleProperty).where(
                ProductSimpleProperty.product_id == product_db.id
            )
        )
        await self.session.execute(
            delete(ProductProperty).where(
                ProductProperty.product_id == product_db.id
            )
        )

        # 2. Создаем новые свойства на основе входящих данных
        await self._create_properties(product_db, data)

    async def _get_related_create(self) -> dict[str, tuple[Any, Any, bool]]:
        """Возвращает кастомные проверки для дочерних классов"""
        return {
            "modified_by": (self.user_client, UserDB, False),
            "created_by": (self.user_client, UserDB, False),
        }

    async def get_product_with_properties(
        self, product_id: UUID
    ) -> ProductDB | None:
        """Получает продукт со всеми свойствами"""
        stmt = (
            select(ProductDB)
            .options(
                selectinload(ProductDB.simple_properties),
                selectinload(ProductDB.properties),
            )
            .where(ProductDB.id == product_id)
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # async def get_product_as_pydantic(
    #     self, product_id: UUID
    # ) -> ProductCreate | None:
    #     """Получает продукт в виде Pydantic модели"""
    #     product = await self.get_product_with_properties(product_id)
    #     if product:
    #         return await product.to_pydantic(
    #             include_properties=True, session=self.session
    #         )
    #     return None

    # product_entity

    async def get_entity_products(
        self,
        owner_id: int,
        owner_type: EntityTypeAbbr,
    ) -> ListProductEntity:
        """Получает продукты в сущности"""
        stmt = select(ProductEntity).where(
            ProductEntity.owner_id == owner_id,
            ProductEntity.owner_type == owner_type,
        )

        result = await self.session.execute(stmt)
        products_entity = result.scalars().all()
        return ListProductEntity(
            result=[product.to_pydantic() for product in products_entity]
        )

    async def delete_product_from_entity(
        self,
        owner_id: int,
        owner_type: EntityTypeAbbr,
        product_id: int,
    ) -> None:
        """Удаляет продукт из сущности"""
        stmt = delete(ProductEntity).where(
            ProductEntity.owner_id == owner_id,
            ProductEntity.owner_type == owner_type,
            ProductEntity.product_id == product_id,
        )

        await self.session.execute(stmt)

    async def create_or_update_product_in_entity(
        self, product_entity: ProductEntityCreate
    ) -> ProductEntity | None:
        """Создает или обновляет продукт в сущности"""

        try:
            # Проверяем существование
            stmt = select(ProductEntity).where(
                ProductEntity.owner_id == product_entity.owner_id,
                ProductEntity.owner_type == product_entity.owner_type,
                ProductEntity.product_id == product_entity.product_id,
            )

            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                # Обновляем существующий
                for field, value in product_entity.model_dump(
                    exclude_unset=True
                ).items():
                    setattr(existing, field, value)

                self.session.add(existing)
                await self.session.flush()

                logger.info(
                    "Updated product in entity",
                    extra={
                        "owner_id": product_entity.owner_id,
                        "owner_type": product_entity.owner_type.value,
                        "product_id": product_entity.product_id,
                    },
                )

                return existing
            else:
                # Создаем новый
                new_entity = ProductEntity(**product_entity.model_dump())
                self.session.add(new_entity)
                await self.session.flush()

                logger.info(
                    "Created product in entity",
                    extra={
                        "owner_id": product_entity.owner_id,
                        "owner_type": product_entity.owner_type.value,
                        "product_id": product_entity.product_id,
                    },
                )

                return new_entity

        except Exception as exc:
            logger.error(f"Failed to create/update product in entity: {exc}")
            raise DatabaseException(
                error_code="failed_to_create_or_update_product_in_entity",
                operation="create_or_update_product_in_entity",
                details=product_entity.model_dump(),
            )
