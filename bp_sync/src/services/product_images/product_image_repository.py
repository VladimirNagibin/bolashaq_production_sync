import hashlib
from uuid import UUID

import httpx
from sqlalchemy import and_, select
from sqlalchemy.exc import SQLAlchemyError

from core.logger import logger
from models.product_images_models import ProductImage as ProductImageDB
from models.product_images_models import ProductImageContent
from schemas.enums import EntityType, SourcesProductEnum
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
                and_(
                    ProductImageDB.product_id == product_id,
                    ProductImageDB.is_deleted_in_bitrix.is_(False),
                )
            )

            result = await self.session.execute(stmt)
            return result.scalars().all()  # type: ignore[no-any-return]
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при получении сделок: {e}")
            return []

    async def set_delete_in_bitrix_by_product_id(
        self, product_id: int
    ) -> None:
        """
        Получает картинки товара по его ID и помечает удалёнными в Битрикс.
        """
        try:
            pictures = await self.get_pictures_by_product_id(product_id)
            for picture in pictures:
                await self.set_deleted_in_bitrix(picture.external_id)
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при пометке сделок удалёнными: {e}")
            return None

    async def get_detail_picture_by_product_id(
        self, product_id: int
    ) -> ProductImageDB | None:
        """Получает картинки товара по его ID."""
        try:
            stmt = select(ProductImageDB).where(
                and_(
                    ProductImageDB.product_id == product_id,
                    ProductImageDB.image_type == "DETAIL_PICTURE",
                    ProductImageDB.is_deleted_in_bitrix.is_(False),
                )
            )

            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при получении сделок: {e}")
            return None

    async def add_image_content_from_url(
        self, product_image_id: UUID, image_url: str
    ) -> ProductImageContent:
        """
        Скачивает картинку по URL, сохраняет её в БД как бинарные данные
        и привязывает к product_image_id.
        """
        try:
            # 1. Скачиваем картинку (используем httpx для асинхронности)
            # Устанавливаем таймаут, чтобы не зависнуть,
            # если сервер не отвечает
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(image_url)
                response.raise_for_status()

                image_bytes = response.content

                # 2. Подготавливаем метаданные
                mime_type = response.headers.get("content-type")
                file_size = len(image_bytes)
                file_hash = hashlib.sha256(image_bytes).hexdigest()

                # 3. Создаем объект модели
                db_content = ProductImageContent(
                    product_image_id=product_image_id,
                    image_data=image_bytes,
                    mime_type=mime_type,
                    file_size=file_size,
                    file_hash=file_hash,
                )

                # 4. Сохраняем в базу
                self.session.add(db_content)
                await self.session.commit()
                await self.session.refresh(db_content)

                return db_content

        except httpx.HTTPStatusError as e:
            logger.error(
                "Ошибка при скачивании картинки "
                f"{image_url}: {e.response.status_code}"
            )
            raise
        except httpx.RequestError as e:
            logger.error(f"Ошибка сети при запросе {image_url}: {e}")
            raise
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Ошибка при сохранении контента картинки в БД: {e}")
            raise

    async def get_pictures(
        self,
        not_deleted_in_bitrix: bool = True,
        image_type: str | None = None,
        source: SourcesProductEnum | None = None,
    ) -> list[ProductImageDB]:
        """Получает картинки товара по его ID."""
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

            result = await self.session.execute(stmt)
            return result.scalars().all()  # type: ignore[no-any-return]
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при получении сделок: {e}")
            return []
