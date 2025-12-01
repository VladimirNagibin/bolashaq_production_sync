from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.logger import logger
from models.product_models import Product as ProductDB
from models.product_models import ProductProperty, ProductSimpleProperty
from models.user_models import User as UserDB
from schemas.enums import EntityType
from schemas.fields import FIELDS_PRODUCT_ALT
from schemas.product_schemas import ProductCreate, ProductUpdate

from ..base_repositories.base_repository import (
    BaseRepository,
)
from ..exceptions import CyclicCallException

if TYPE_CHECKING:
    from ..users.user_services import UserClient


class ProductRepository(
    BaseRepository[ProductDB, ProductCreate, ProductUpdate, int]
):
    """Contact repository with lazy UserClient loading"""

    model = ProductDB
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
