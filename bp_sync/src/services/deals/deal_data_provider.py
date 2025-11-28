from typing import TYPE_CHECKING

from schemas.company_schemas import CompanyCreate
from schemas.contact_schemas import ContactCreate
from schemas.deal_schemas import DealCreate
from schemas.product_schemas import ListProductEntity

if TYPE_CHECKING:
    from .deal_services import DealClient


class DealDataProvider:
    """Провайдер данных для работы со сделками"""

    def __init__(self, deal_client: "DealClient"):
        self.deal_client = deal_client
        self._cached_company: CompanyCreate | None = None
        self._cached_contact: ContactCreate | None = None
        self._cached_products: ListProductEntity | None = None

    async def get_company_data(
        self, deal_b24: DealCreate
    ) -> CompanyCreate | None:
        """Получает данные компании"""
        if self._cached_company:
            return self._cached_company

        if deal_b24.company_id:
            company = await self.deal_client.get_company(deal_b24.company_id)
            if company:
                self._cached_company = company
                return company

        return None

    async def get_contact_data(
        self, deal_b24: DealCreate
    ) -> ContactCreate | None:
        """Получает данные контакта"""
        if self._cached_contact:
            return self._cached_contact

        if deal_b24.contact_id:
            contact = await self.deal_client.get_contact(deal_b24.contact_id)
            if contact:
                self._cached_contact = contact
                return contact

        return None

    async def get_products_data(self) -> ListProductEntity | None:
        """Получает товары сделки"""
        return self._cached_products

    def set_cached_company(self, company: CompanyCreate) -> None:
        """Устанавливает кэшированную компанию"""
        self._cached_company = company

    def set_cached_contact(self, contact: ContactCreate) -> None:
        """Устанавливает кэшированный контакт"""
        self._cached_contact = contact

    def set_cached_products(self, products: ListProductEntity) -> None:
        """Устанавливает кэшированные продукты"""
        self._cached_products = products

    def clear_cache(self) -> None:
        """Очищает кэш"""
        self._cached_company = None
        self._cached_contact = None
        self._cached_products = None
