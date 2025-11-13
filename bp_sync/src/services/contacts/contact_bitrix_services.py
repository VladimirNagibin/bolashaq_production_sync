from schemas.contact_schemas import ContactCreate, ContactUpdate

from ..bitrix_services.base_bitrix_services import BaseBitrixEntityClient


class ContactBitrixClient(
    BaseBitrixEntityClient[ContactCreate, ContactUpdate]
):
    entity_name = "contact"
    create_schema = ContactCreate
    update_schema = ContactUpdate
