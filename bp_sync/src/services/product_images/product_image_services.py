from typing import Any

from core.logger import logger
from models.product_images_models import ProductImage as ProductImageDB
from schemas.product_image_schemas import (
    ProductImageCreate,
    ProductImageUpdate,
)
from services.exceptions import BitrixApiError, DatabaseException

from .product_image_bitrix_service import ProductImageService
from .product_image_repository import ProductImageRepository


class ProductImageClient:
    """Клиент для управления картинками товаров."""

    def __init__(
        self,
        product_image_bitrix_client: ProductImageService,
        product_image_repo: ProductImageRepository,
    ) -> None:
        """
        Инициализирует клиент картинок товаров.

        Args:
            product_image_bitrix_client: Клиент Bitrix для работы с картинками
            product_image_repo: Репозиторий картинок товаров
        """
        super().__init__()
        self._bitrix_client = product_image_bitrix_client
        self._repo = product_image_repo

    @property
    def entity_name(self) -> str:
        return "product_image"

    @property
    def bitrix_client(self) -> ProductImageService:
        return self._bitrix_client

    @property
    def repo(self) -> ProductImageRepository:
        return self._repo

    async def import_from_bitrix(
        self, product_id: int
    ) -> list[ProductImageDB]:
        """
        Импортирует картинки товара из Bitrix в базу данных.

        Args:
            product_id: ID товара в Bitrix

        Returns:
            list[ProductImageDB]: Список синхронизированных изображений

        Raises:
            BitrixApiError: При ошибке получения данных из Bitrix
            DatabaseError: При ошибке работы с базой данных
        """
        logger.info(
            "Starting product images import from Bitrix",
            extra={"product_id": product_id},
        )
        try:
            # Получаем изображения из Bitrix
            bitrix_images = await self._fetch_bitrix_images(product_id)

            # Получаем существующие изображения из БД
            db_images = await self._fetch_db_images(product_id)

            # Синхронизируем изображения
            synchronized_images = await self._synchronize_images(
                source_images=bitrix_images,
                target_images=db_images,
                product_id=product_id,
            )

            logger.info(
                "Product images import completed successfully",
                extra={
                    "product_id": product_id,
                    "total_images": len(synchronized_images),
                },
            )

            return synchronized_images

        except BitrixApiError as e:
            logger.error(
                f"Failed to fetch images from Bitrix for product {product_id}",
                extra={"error": str(e), "product_id": product_id},
                exc_info=True,
            )
            raise

        except DatabaseException as e:
            logger.error(
                f"Database error during image sync for product {product_id}",
                extra={"error": str(e), "product_id": product_id},
                exc_info=True,
            )
            raise

        except Exception as e:
            logger.error(
                "Unexpected error during image import for product "
                f"{product_id}",
                extra={"error": str(e), "product_id": product_id},
                exc_info=True,
            )
            raise DatabaseException(f"Image import failed: {e}")

    async def _fetch_bitrix_images(
        self, product_id: int
    ) -> list[ProductImageCreate]:
        """
        Получает изображения товара из Bitrix.

        Args:
            product_id: ID товара

        Returns:
            list[ProductImageCreate]: Список изображений из Bitrix
        """
        try:
            images = await self.bitrix_client.get_pictures_by_product_id(
                product_id
            )
            logger.debug(
                "Retrieved {len(images)} images from Bitrix for product "
                f"{product_id}"
            )
            return images
        except BitrixApiError as e:
            logger.error(
                f"Bitrix API error for product {product_id}: {e}",
                exc_info=True,
            )
            raise

    async def _fetch_db_images(self, product_id: int) -> list[ProductImageDB]:
        """
        Получает существующие изображения товара из БД.

        Args:
            product_id: ID товара

        Returns:
            list[ProductImageDB]: Список изображений из БД
        """
        try:
            images = await self.repo.get_pictures_by_product_id(product_id)
            logger.debug(
                "Retrieved {len(images)} images from DB for product "
                f"{product_id}"
            )
            return images
        except Exception as e:
            logger.error(
                "Database error while fetching images for product "
                f"{product_id}: {e}",
                exc_info=True,
            )
            raise DatabaseException(f"Failed to fetch images from DB: {e}")

    async def _synchronize_images(
        self,
        source_images: list[ProductImageCreate],
        target_images: list[ProductImageDB],
        product_id: int,
    ) -> list[ProductImageDB]:
        """
        Синхронизация изображений товара между данными из внешнего источника
        и БД.

        Args:
            source_images: Изображения из источника (Bitrix)
            target_images: Существующие изображения в БД
            product_id: ID товара

        Returns:
            List[ProductImage]: Список актуальных изображений
        """

        # Создаем словари для быстрого поиска
        source_index: dict[int, ProductImageCreate] = {
            int(img.external_id): img
            for img in source_images
            if img.external_id
        }
        target_index = {img.external_id: img for img in target_images}

        # Счетчики операций
        stats: dict[str, int] = {"created": 0, "updated": 0, "deleted": 0}

        # Обрабатываем существующие изображения
        await self._process_existing_images(
            target_images=target_images,
            source_index=source_index,
            stats=stats,
        )

        # Создаем новые изображения
        created_images = await self._create_new_images(
            source_images=source_images,
            target_index=target_index,
            product_id=product_id,
            stats=stats,
        )

        # Логируем результаты
        self._log_sync_results(product_id, stats)

        # Возвращаем все актуальные (не удаленные) изображения
        return self._filter_active_images(target_images + created_images)

    async def _process_existing_images(
        self,
        target_images: list[ProductImageDB],
        source_index: dict[int, ProductImageCreate],
        stats: dict[str, int],
    ) -> list[ProductImageDB]:
        """
        Обрабатывает существующие изображения: обновляет или помечает как
        удаленные.

        Args:
            target_images: Список существующих изображений
            source_index: Индекс изображений из источника
            stats: Счетчик операций

        Returns:
            list[ProductImageDB]: Список обновленных изображений
        """
        updated_images: list[ProductImageDB] = []

        for existing_image in target_images:
            if existing_image.external_id not in source_index:
                # Изображение отсутствует в источнике - помечаем как удаленное
                if not existing_image.is_deleted_in_bitrix:
                    await self.repo.set_deleted_in_bitrix(
                        existing_image.external_id
                    )
                    stats["deleted"] += 1
                    logger.info(
                        f"Image {existing_image.external_id} "
                        f"({existing_image.name}) "
                        "marked as deleted for product "
                        f"{existing_image.product_id}"
                    )
            else:
                # Изображение присутствует в источнике -
                # обновляем при необходимости
                source_image = source_index[existing_image.external_id]
                updated = await self._update_if_changed(
                    existing_image, source_image
                )
                if updated:
                    updated_images.append(existing_image)
                    stats["updated"] += 1

        return updated_images

    async def _update_if_changed(
        self,
        existing: ProductImageDB,
        source: ProductImageCreate,
    ) -> bool:
        """
        Обновляет изображение, если поля изменились.

        Args:
            existing: Существующее изображение
            source: Изображение из источника

        Returns:
            bool: True если были изменения, иначе False
        """
        update_dict: dict[str, Any] = {
            "external_id": existing.external_id,
            "product_id": existing.product_id,
        }
        update_data = ProductImageUpdate(**update_dict)
        has_changes = False

        # Проверяем каждое поле
        field_changes: dict[str, tuple[Any, Any]] = {
            "name": (existing.name, source.name),
            "detail_url": (existing.detail_url, source.detail_url),
            "image_type": (existing.image_type, source.image_type),
        }

        for field_name, (old_value, new_value) in field_changes.items():
            if old_value != new_value:
                setattr(update_data, field_name, new_value)
                has_changes = True
                logger.debug(
                    f"Image {existing.external_id}: {field_name} changed "
                    f"'{old_value}' -> '{new_value}'"
                )

        # Обрабатываем флаг удаления
        if existing.is_deleted_in_bitrix:
            update_data.is_deleted_in_bitrix = False
            has_changes = True
            logger.debug(f"Image {existing.external_id}: removed deleted flag")

        # Сохраняем изменения
        if has_changes:
            await self.repo.update(update_data)

        return has_changes

    async def _create_new_images(
        self,
        source_images: list[ProductImageCreate],
        target_index: dict[int, ProductImageDB],
        product_id: int,
        stats: dict[str, int],
    ) -> list[ProductImageDB]:
        """
        Создает новые изображения, отсутствующие в БД.

        Args:
            source_images: Список изображений из источника
            target_index: Индекс существующих изображений
            product_id: ID товара
            stats: Счетчик операций

        Returns:
            list[ProductImageDB]: Список созданных изображений
        """
        created_images: list[ProductImageDB] = []

        for source_image in source_images:
            if source_image.external_id not in target_index:
                try:
                    new_image = await self.repo.create(source_image)
                    created_images.append(new_image)
                    stats["created"] += 1
                    logger.debug(
                        f"Created new image {source_image.external_id} "
                        f"({source_image.name}) for product {product_id}"
                    )
                except Exception as e:
                    logger.error(
                        (
                            "Failed to create image "
                            f"{source_image.external_id}: {e}"
                        ),
                        exc_info=True,
                    )
                    raise DatabaseException(f"Failed to create image: {e}")

        return created_images

    def _filter_active_images(
        self,
        images: list[ProductImageDB],
    ) -> list[ProductImageDB]:
        """
        Фильтрует активные (не удаленные) изображения.

        Args:
            images: Список изображений

        Returns:
            list[ProductImageDB]: Список активных изображений
        """
        return [img for img in images if not img.is_deleted_in_bitrix]

    def _log_sync_results(
        self,
        product_id: int,
        stats: dict[str, int],
    ) -> None:
        """
        Логирует результаты синхронизации.

        Args:
            product_id: ID товара
            stats: Статистика операций
        """
        logger.info(
            f"Product {product_id} images sync completed",
            extra={
                "product_id": product_id,
                "created_": stats["created"],
                "updated_": stats["updated"],
                "deleted_": stats["deleted"],
                "total_active": (
                    stats["created"] + (stats["updated"] - stats["deleted"])
                ),
            },
        )

    async def transform_product_picture_fields(self, product_id: int) -> bool:
        # await self.import_from_bitrix(product_id)

        pictures = await self.repo.get_pictures_by_product_id(product_id)
        logger.info(f"{pictures}--------------------------------------")
        detail_id = None
        detail_url = None
        for picture in pictures:
            if picture.image_type == "DETAIL_PICTURE":
                return True
            if (
                detail_id is None
                and picture.image_type == "MORE_PHOTO"
                and picture.source is None
            ):
                detail_id = picture.external_id
                detail_url = picture.detail_url
        if detail_id and detail_url:
            logger.info(
                f"{detail_id}---{detail_url}-------------------------------"
            )
            await self.bitrix_client.set_detail_picture(product_id, detail_url)
            await self.bitrix_client.delete_picture_by_id(
                product_id, detail_id
            )
            # await self.import_from_bitrix(product_id)
            return True
        return False
