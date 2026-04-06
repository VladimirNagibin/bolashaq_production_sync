from typing import Any

from api.v1.schemas.site_request import SiteRequestPayload

from ..companies.company_bitrix_services import CompanyBitrixClient
from ..contacts.contact_bitrix_services import ContactBitrixClient
from ..deals.deal_bitrix_services import DealBitrixClient
from ..products.product_bitrix_services import ProductBitrixClient

# from ..suppliers.repositories.supplier_product_repo import (
#     SupplierProductRepository
# )
from ..users.user_bitrix_services import UserBitrixClient
from .entities_services import EntityClient
from .site_request_handler import SiteRequestHandler


class EntitiesBitrixClient:
    def __init__(
        self,
        contact_bitrix_client: ContactBitrixClient,
        company_bitrix_client: CompanyBitrixClient,
        deal_bitrix_client: DealBitrixClient,
        user_bitrix_client: UserBitrixClient,
        product_bitrix_client: ProductBitrixClient,
        # supplier_repo: SupplierProductRepository,
    ) -> None:
        self.contact_bitrix_client = contact_bitrix_client
        self.deal_bitrix_client = deal_bitrix_client
        self.company_bitrix_client = company_bitrix_client
        self.user_bitrix_client = user_bitrix_client
        self.product_bitrix_client = product_bitrix_client
        # self.supplier_repo = supplier_repo
        self._site_request_handler: SiteRequestHandler | None = None

    @property
    def site_request_handler(self) -> SiteRequestHandler:
        if not self._site_request_handler:
            self._site_request_handler = SiteRequestHandler(self)
        return self._site_request_handler

    async def handle_request_price(
        self, payload: SiteRequestPayload, entity_client: EntityClient
    ) -> dict[str, Any]:
        return await self.site_request_handler.handle_request_price(
            payload, entity_client
        )
