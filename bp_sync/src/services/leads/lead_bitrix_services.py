from schemas.lead_schemas import LeadCreate, LeadUpdate

from ..bitrix_services.base_bitrix_services import BaseBitrixEntityClient


class LeadBitrixClient(BaseBitrixEntityClient[LeadCreate, LeadUpdate]):
    entity_name = "lead"
    create_schema = LeadCreate
    update_schema = LeadUpdate
