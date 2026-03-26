from typing import Any
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.exc import SQLAlchemyError

from core.exceptions.repo_exceptions import DatabaseOperationError
from core.logger import logger
from models.product_images_models import ProductImage as ProductImageDB
from models.product_images_models import ProductImageContent
from schemas.enums import EntityType, ImageType, SourcesProductEnum
from schemas.product_image_schemas import (
    ProductImageCreate,
    ProductImageUpdate,
)

from ..base_repositories.base_repository import BaseRepository


class ProductImageRepository(
    BaseRepository[ProductImageDB, ProductImageCreate, ProductImageUpdate, int]
):
    """
    Репозиторий для управления изображениями товаров в локальной базе данных.
    """

    model = ProductImageDB
    entity_type = EntityType.PRODUCT_IMAGE
    schema_update_class = ProductImageUpdate

    async def get_active_by_product_id(
        self, product_id: int
    ) -> list[ProductImageDB]:
        """
        Получает список неудаленных изображений для конкретного товара.

        Args:
            product_id: ID товара.

        Returns:
            Список изображений (ProductImageDB).
        """
        try:
            stmt = select(ProductImageDB).where(
                and_(
                    ProductImageDB.product_id == product_id,
                    ProductImageDB.is_deleted_in_bitrix.is_(False),
                )
            )

            result = await self.session.execute(stmt)
            return result.scalars().all()  # type: ignore[no-any-return]
        except Exception as e:
            logger.error(
                f"Error fetching images for product {product_id}: {e}",
                exc_info=True,
            )
            raise DatabaseOperationError(
                operation=f"fetching images for product {product_id}",
                entity_name="ProductImage",
                detail=f"Ошибка запроса к БД: {e}",
                original_error=e,
            )

    async def get_detail_by_product_id(
        self, product_id: int
    ) -> ProductImageDB | None:
        """
        Получает детальную картинку товара.

        Args:
            product_id: ID товара.

        Returns:
            Объект детальной картинки или None.
        """
        try:
            stmt = select(ProductImageDB).where(
                and_(
                    ProductImageDB.product_id == product_id,
                    ProductImageDB.image_type == ImageType.DETAIL_PICTURE.name,
                    ProductImageDB.is_deleted_in_bitrix.is_(False),
                )
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"Error fetching detail image for product {product_id}: {e}",
                exc_info=True,
            )
            return None

    async def mark_all_deleted_by_product_id(self, product_id: int) -> None:
        """
        Получает картинки товара по его ID и помечает удалёнными в Битрикс.
        """
        try:
            pictures = await self.get_active_by_product_id(product_id)
            for picture in pictures:
                await self.set_deleted_in_bitrix(picture.external_id)
        except SQLAlchemyError as e:
            logger.error(
                (
                    "Error marking images as deleted for product "
                    f"{product_id}: {e}"
                ),
                exc_info=True,
            )
            raise DatabaseOperationError(
                operation=f"mark_all_deleted_by_product_id: {product_id}",
                entity_name="ProductImage",
                detail=f"Ошибка запроса к БД: {e}",
                original_error=e,
            )

    async def save_image_content(
        self, product_image_id: UUID, image_data: dict[str, Any]
    ) -> ProductImageContent:
        """
        Сохраняет бинарный контент изображения в базу данных.

        Args:
            product_image_id: ID записи изображения в локальной БД.
            image_data: Словарь с данными файла (raw_bytes, file_hash и т.д.).

        Returns:
            Созданный объект ProductImageContent.
        """
        try:
            image_bytes = image_data.get("raw_bytes")
            file_hash = image_data.get("file_hash")
            file_size = image_data.get("file_size")
            mime_type = image_data.get("content_type")

            if not image_bytes:
                raise ValueError(
                    "Отсутствуют 'raw_bytes' в данных изображения"
                )

            # Создаем объект модели
            db_content = ProductImageContent(
                product_image_id=product_image_id,
                image_data=image_bytes,
                mime_type=mime_type,
                file_size=file_size,
                file_hash=file_hash,
            )

            # Сохраняем в базу
            self.session.add(db_content)
            await self.session.commit()
            await self.session.refresh(db_content)

            return db_content
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to save image content: {e}", exc_info=True)
            raise DatabaseOperationError(
                operation=f"save_image_content: {product_image_id}",
                entity_name="ProductImageContent",
                detail=f"Ошибка запроса к БД: {e}",
                original_error=e,
            )

    async def get_images(
        self,
        not_deleted_in_bitrix: bool = True,
        image_type: str | None = None,
        source: SourcesProductEnum | None = None,
        product_id: int | None = None,
    ) -> list[ProductImageDB]:
        """Получает картинки по фильтрам."""
        try:
            stmt = select(ProductImageDB)
            if not_deleted_in_bitrix:
                stmt = stmt.where(
                    ProductImageDB.is_deleted_in_bitrix.is_(False)
                )
            if image_type:
                stmt = stmt.where(ProductImageDB.image_type == image_type)
            if source:
                stmt = stmt.where(ProductImageDB.source == source)
            if product_id:
                stmt = stmt.where(ProductImageDB.product_id == product_id)

            result = await self.session.execute(stmt)
            return result.scalars().all()  # type: ignore[no-any-return]
        except Exception as e:
            filters: list[str] = [
                f"not_deleted_in_bitrix: {not_deleted_in_bitrix}"
            ]
            if image_type:
                filters.append(f"type: {image_type}")
            if source:
                filters.append(f"source: {source}")
            if product_id:
                filters.append(f"product_id: {product_id}")

            logger.error(
                "Failed to get images by filters "
                f"{'; '.join(filters)}: {e}",
                exc_info=True,
            )
            raise DatabaseOperationError(
                operation=f"get_pictures_by_filters: {'; '.join(filters)}",
                entity_name="ProductImage",
                detail=f"Ошибка запроса к БД: {e}",
                original_error=e,
            )
