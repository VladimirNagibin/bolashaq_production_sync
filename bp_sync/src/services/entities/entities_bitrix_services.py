from typing import Any

from ..companies.company_bitrix_services import CompanyBitrixClient
from ..contacts.contact_bitrix_services import ContactBitrixClient
from ..deals.deal_bitrix_services import DealBitrixClient
from .site_request_handler import SiteRequestHandler


class EntitiesBitrixClient:
    def __init__(
        self,
        contact_bitrix_client: ContactBitrixClient,
        company_bitrix_client: CompanyBitrixClient,
        deal_bitrix_client: DealBitrixClient,
    ) -> None:
        self.contact_bitrix_client = contact_bitrix_client
        self.deal_bitrix_client = deal_bitrix_client
        self.company_bitrix_client = company_bitrix_client
        self._site_request_handler: SiteRequestHandler | None = None

    @property
    def site_request_handler(self) -> SiteRequestHandler:
        if not self._site_request_handler:
            self._site_request_handler = SiteRequestHandler(self)
        return self._site_request_handler

    async def handle_request_price(
        self,
        phone: str,
        product_id: int,
        product_name: str | None = None,
        name: str | None = None,
        comment: str | None = None,
        message_id: str | None = None,
    ) -> dict[str, Any]:
        return await self.site_request_handler.handle_request_price(
            phone, product_id, product_name, name, comment, message_id
        )
