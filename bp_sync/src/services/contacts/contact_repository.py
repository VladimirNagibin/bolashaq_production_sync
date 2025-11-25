from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Coroutine, Type

from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import logger
from db.postgres import Base
from models.bases import EntityType
from models.company_models import Company as CompanyDB
from models.contact_models import Contact as ContactDB
from models.lead_models import Lead as LeadDB
from models.references import (
    ContactType,
    DealFailureReason,
    DealType,
    MainActivity,
    Source,
)
from models.user_models import User as UserDB
from schemas.contact_schemas import ContactCreate, ContactUpdate

from ..base_repositories.base_communication_repo import (
    EntityWithCommunicationsRepository,
)
from ..exceptions import CyclicCallException
from ..users.user_services import UserClient

if TYPE_CHECKING:
    from ..companies.company_services import CompanyClient
    from ..entities.source_services import SourceClient
    from ..leads.lead_services import LeadClient


class ContactRepository(
    EntityWithCommunicationsRepository[
        ContactDB, ContactCreate, ContactUpdate, int
    ]
):

    model = ContactDB
    entity_type = EntityType.CONTACT

    def __init__(
        self,
        session: AsyncSession,
        get_company_client: Callable[[], Coroutine[Any, Any, CompanyClient]],
        get_lead_client: Callable[[], Coroutine[Any, Any, LeadClient]],
        get_user_client: Callable[[], Coroutine[Any, Any, UserClient]],
        get_source_client: Callable[[], Coroutine[Any, Any, SourceClient]],
    ):
        super().__init__(session)
        self.get_company_client = get_company_client
        self.get_lead_client = get_lead_client
        self.get_user_client = get_user_client
        self.get_source_client = get_source_client

    async def create_entity(self, data: ContactCreate) -> ContactDB:
        """Создает новый контакт с проверкой связанных объектов"""
        await self._check_related_objects(data)
        try:
            await self._create_or_update_related(data)
        except CyclicCallException:
            if not data.external_id:
                logger.error("Update failed: Missing ID")
                raise ValueError("ID is required for update")
            external_id = data.external_id
            data = ContactCreate.get_default_entity(int(external_id))
        return await self.create(data=data)

    async def update_entity(
        self, data: ContactCreate | ContactUpdate
    ) -> ContactDB:
        """Обновляет существующий контакт"""
        await self._check_related_objects(data)
        await self._create_or_update_related(data)
        return await self.update(data=data)

    async def _get_related_checks(self) -> list[tuple[str, Type[Base], str]]:
        """Возвращает специфичные для Deal проверки"""
        return [
            # (атрибут схемы, модель БД, поле в модели)
            ("type_id", ContactType, "external_id"),
            ("main_activity_id", MainActivity, "ext_alt2_id"),
            ("deal_failure_reason_id", DealFailureReason, "ext_alt2_id"),
            ("deal_type_id", DealType, "external_id"),
        ]

    async def _get_related_create(self) -> dict[str, tuple[Any, Any, bool]]:
        """Возвращает кастомные проверки для дочерних классов"""
        company_client = await self.get_company_client()
        lead_client = await self.get_lead_client()
        user_client = await self.get_user_client()
        source_client = await self.get_source_client()
        return {
            "lead_id": (lead_client, LeadDB, False),
            "company_id": (company_client, CompanyDB, False),
            "assigned_by_id": (user_client, UserDB, True),
            "created_by_id": (user_client, UserDB, True),
            "modify_by_id": (user_client, UserDB, False),
            "last_activity_by": (user_client, UserDB, False),
            "source_id": (source_client, Source, False),
        }
