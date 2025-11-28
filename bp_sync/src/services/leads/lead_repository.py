from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import logger
from models.lead_models import Lead as LeadDB
from models.user_models import User as UserDB
from schemas.enums import EntityType
from schemas.lead_schemas import LeadCreate, LeadUpdate

from ..base_repositories.base_communication_repo import (
    EntityWithCommunicationsRepository,
)
from ..exceptions import CyclicCallException

if TYPE_CHECKING:
    from ..users.user_services import UserClient


class LeadRepository(
    EntityWithCommunicationsRepository[LeadDB, LeadCreate, LeadUpdate, int]
):

    model = LeadDB
    entity_type = EntityType.LEAD

    def __init__(
        self,
        session: AsyncSession,
    ):
        super().__init__(session)
        self._user_client: Optional["UserClient"] = None
        self._user_client_initialized = False

    def set_user_client(self, user_client: "UserClient") -> None:
        """Устанавливает UserClient после создания репозитория"""
        self._user_client = user_client
        self._user_client_initialized = True
        logger.debug("UserClient set for LeadRepository")

    @property
    def user_client(self) -> Optional["UserClient"]:
        """Ленивое свойство для доступа к UserClient"""
        if not self._user_client_initialized and self._user_client is None:
            logger.warning(
                "UserClient not initialized in LeadRepository. "
                "Call set_user_client() first or use methods "
                "that don't require UserClient."
            )
        return self._user_client

    async def create_entity(self, data: LeadCreate) -> LeadDB:
        """Создает новый лид с проверкой связанных объектов"""
        await self._check_related_objects(data)
        try:
            await self._create_or_update_related(data)
        except CyclicCallException:
            if not data.external_id:
                logger.error("Update failed: Missing ID")
                raise ValueError("ID is required for update")
            external_id = data.external_id
            data = LeadCreate.get_default_entity(int(external_id))
        return await self.create(data=data)

    async def update_entity(self, data: LeadUpdate | LeadCreate) -> LeadDB:
        """Обновляет существующий лид"""
        await self._check_related_objects(data)
        await self._create_or_update_related(data)
        return await self.update(data=data)

    async def _get_related_create(self) -> dict[str, tuple[Any, Any, bool]]:
        """Возвращает кастомные проверки для дочерних классов"""
        return {
            "assigned_by_id": (self.user_client, UserDB, True),
            "created_by_id": (self.user_client, UserDB, True),
            "modify_by_id": (self.user_client, UserDB, False),
            "moved_by_id": (self.user_client, UserDB, False),
            "last_activity_by": (self.user_client, UserDB, False),
        }
