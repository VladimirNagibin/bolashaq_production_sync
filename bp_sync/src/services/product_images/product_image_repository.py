from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from core.logger import logger
from models.product_images_models import ProductImage as ProductImageDB
from schemas.enums import EntityType
from schemas.product_image_schemas import (
    ProductImageCreate,
    ProductImageUpdate,
)

from ..base_repositories.base_repository import BaseRepository


class ProductImageRepository(
    BaseRepository[ProductImageDB, ProductImageCreate, ProductImageUpdate, int]
):

    model = ProductImageDB
    entity_type = EntityType.PRODUCT_IMAGE
    schema_update_class = ProductImageUpdate

    async def get_pictures_by_product_id(
        self, product_id: int
    ) -> list[ProductImageDB]:
        """Получает картинки товара по его ID."""
        try:
            stmt = select(ProductImageDB).where(
                ProductImageDB.product_id == product_id
            )

            result = await self.session.execute(stmt)
            return result.scalars().all()  # type: ignore[no-any-return]
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при получении сделок: {e}")
            return []

    async def set_delete_in_bitrix_by_product_id(
        self, product_id: int
    ) -> None:
        """Получает картинки товара по его ID."""
        try:
            pictures = await self.get_pictures_by_product_id(product_id)
            for picture in pictures:
                await self.set_deleted_in_bitrix(picture.external_id)
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при получении сделок: {e}")
            return None
