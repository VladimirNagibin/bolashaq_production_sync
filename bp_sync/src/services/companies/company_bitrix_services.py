from schemas.company_schemas import CompanyCreate, CompanyUpdate

from ..bitrix_services.base_bitrix_services import BaseBitrixEntityClient


class CompanyBitrixClient(
    BaseBitrixEntityClient[CompanyCreate, CompanyUpdate]
):
    entity_name = "company"
    create_schema = CompanyCreate
    update_schema = CompanyUpdate
