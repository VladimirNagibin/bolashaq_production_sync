from typing import Any

from core.settings import settings
from models.company_models import Company as CompanyDB
from services.users.user_services import UserClient

from ..base_services.base_service import BaseEntityClient
from .company_bitrix_services import (
    CompanyBitrixClient,
)
from .company_repository import CompanyRepository


class CompanyClient(
    BaseEntityClient[
        CompanyDB,
        CompanyRepository,
        CompanyBitrixClient,
    ]
):
    def __init__(
        self,
        company_bitrix_client: CompanyBitrixClient,
        company_repo: CompanyRepository,
        user_client: UserClient | None = None,
    ):
        super().__init__()
        self._bitrix_client = company_bitrix_client
        self._repo = company_repo

        if user_client is not None:
            self._repo.set_user_client(user_client)

    @property
    def entity_name(self) -> str:
        return "company"

    @property
    def bitrix_client(self) -> CompanyBitrixClient:
        return self._bitrix_client

    @property
    def repo(self) -> CompanyRepository:
        return self._repo

    @property
    def webhook_config(self) -> dict[str, Any]:
        return settings.web_hook_config_company  # type: ignore
