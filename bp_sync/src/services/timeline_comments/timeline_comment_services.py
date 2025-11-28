from typing import Any

# from core.settings import settings
from models.timeline_comment_models import TimelineComment as TimelineCommentDB
from services.users.user_services import UserClient

from ..base_services.base_service import BaseEntityClient
from .timeline_comment_bitrix_services import (
    TimeLineCommentBitrixClient,
)
from .timeline_comment_repository import TimelineCommentRepository


class TimelineCommentClient(
    BaseEntityClient[
        TimelineCommentDB,
        TimelineCommentRepository,
        TimeLineCommentBitrixClient,
    ]
):
    def __init__(
        self,
        timeline_comment_bitrix_client: TimeLineCommentBitrixClient,
        timeline_comment_repo: TimelineCommentRepository,
        user_client: UserClient | None = None,
    ):
        super().__init__()
        self._bitrix_client = timeline_comment_bitrix_client
        self._repo = timeline_comment_repo

        if user_client is not None:
            self._repo.set_user_client(user_client)

    @property
    def entity_name(self) -> str:
        return "contact"

    @property
    def bitrix_client(self) -> TimeLineCommentBitrixClient:
        return self._bitrix_client

    @property
    def repo(self) -> TimelineCommentRepository:
        return self._repo

    @property
    def webhook_config(self) -> dict[str, Any]:
        return {}  # settings.web_hook_config_timeline_comment
