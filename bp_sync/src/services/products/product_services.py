from typing import Any

from core.settings import settings
from models.product_models import Product as ProductDB
from services.users.user_services import UserClient

from ..base_services.base_service import BaseEntityClient
from .product_bitrix_services import (
    ProductBitrixClient,
)
from .product_repository import ProductRepository


class ProductClient(
    BaseEntityClient[
        ProductDB,
        ProductRepository,
        ProductBitrixClient,
    ]
):
    def __init__(
        self,
        product_bitrix_client: ProductBitrixClient,
        product_repo: ProductRepository,
        user_client: UserClient | None = None,
    ):
        super().__init__()
        self._bitrix_client = product_bitrix_client
        self._repo = product_repo

        if user_client is not None:
            self._repo.set_user_client(user_client)

    @property
    def entity_name(self) -> str:
        return "product"

    @property
    def bitrix_client(self) -> ProductBitrixClient:
        return self._bitrix_client

    @property
    def repo(self) -> ProductRepository:
        return self._repo

    @property
    def webhook_config(self) -> dict[str, Any]:
        return settings.web_hook_config_product  # type: ignore
