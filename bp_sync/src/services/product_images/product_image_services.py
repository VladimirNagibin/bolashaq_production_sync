# from datetime import timedelta
# from typing import Any

# from core.logger import logger
# from core.settings import settings
# from models.product_images_models import ProductImage as ProductImageDB

# from ..base_services.base_service import BaseEntityClient
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
        return "lead"

    @property
    def bitrix_client(self) -> ProductImageService:
        return self._bitrix_client

    @property
    def repo(self) -> ProductImageRepository:
        return self._repo
