from typing import Any

from core.settings import settings
from models.user_models import User as UserDB

from ..base_services.base_service import BaseEntityClient
from .user_bitrix_services import UserBitrixClient
from .user_repository import UserRepository


class UserClient(
    BaseEntityClient[
        UserDB, UserRepository, UserBitrixClient  # type: ignore[type-var]
    ]
):
    def __init__(
        self,
        user_bitrix_client: UserBitrixClient,
        user_repo: UserRepository,
    ):
        super().__init__()
        self._bitrix_client = user_bitrix_client
        self._repo = user_repo

    @property
    def entity_name(self) -> str:
        return "user"

    @property
    def bitrix_client(self) -> UserBitrixClient:
        return self._bitrix_client

    @property
    def repo(self) -> UserRepository:
        return self._repo

    @property
    def webhook_config(self) -> dict[str, Any]:
        return settings.web_hook_config_user  # type: ignore[no-any-return]
