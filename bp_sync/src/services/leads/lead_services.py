from typing import Any

from core.settings import settings
from models.lead_models import Lead as LeadDB
from services.users.user_services import UserClient

from ..base_services.base_service import BaseEntityClient
from .lead_bitrix_services import LeadBitrixClient
from .lead_repository import LeadRepository


class LeadClient(BaseEntityClient[LeadDB, LeadRepository, LeadBitrixClient]):
    def __init__(
        self,
        lead_bitrix_client: LeadBitrixClient,
        lead_repo: LeadRepository,
        user_client: UserClient | None = None,
    ):
        super().__init__()
        self._bitrix_client = lead_bitrix_client
        self._repo = lead_repo

        if user_client is not None:
            self._repo.set_user_client(user_client)

    @property
    def entity_name(self) -> str:
        return "lead"

    @property
    def bitrix_client(self) -> LeadBitrixClient:
        return self._bitrix_client

    @property
    def repo(self) -> LeadRepository:
        return self._repo

    @property
    def webhook_config(self) -> dict[str, Any]:
        return settings.web_hook_config_lead  # type: ignore
