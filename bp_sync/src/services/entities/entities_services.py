from typing import Any

from api.v1.schemas.site_request import SiteRequestPayload

from ..suppliers.supplier_services import SupplierClient
from .entities_bitrix_services import EntitiesBitrixClient

# from core.settings import settings


class EntityClient:
    def __init__(
        self,
        bitrix_client: EntitiesBitrixClient,
        supplier_client: SupplierClient,
    ):
        super().__init__()
        self._bitrix_client = bitrix_client
        self._supplier_client = supplier_client

    @property
    def bitrix_client(self) -> EntitiesBitrixClient:
        return self._bitrix_client

    @property
    def supplier_client(self) -> SupplierClient:
        return self._supplier_client

    async def handle_request_price(
        self, payload: SiteRequestPayload
    ) -> dict[str, Any]:
        # TODO: move the product processing process to this level
        site_request_handler = self.bitrix_client.site_request_handler
        return await site_request_handler.handle_request_price(payload, self)
