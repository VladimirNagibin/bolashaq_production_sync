from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import logger
from models.timeline_comment_models import TimelineComment as TimelineCommDB
from models.user_models import User as UserDB
from schemas.enums import EntityType
from schemas.timeline_comment_schemas import (
    TimelineCommentCreate,
    TimelineCommentUpdate,
)

from ..base_repositories.base_repository import BaseRepository

if TYPE_CHECKING:
    from ..users.user_services import UserClient


class TimelineCommentRepository(
    BaseRepository[
        TimelineCommDB, TimelineCommentCreate, TimelineCommentUpdate, int
    ]
):

    model = TimelineCommDB
    entity_type = EntityType.TIMELINE_COMMENT

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
        logger.debug("UserClient set for TimelineCommentRepository")

    @property
    def user_client(self) -> Optional["UserClient"]:
        """Ленивое свойство для доступа к UserClient"""
        if not self._user_client_initialized and self._user_client is None:
            logger.warning(
                "UserClient not initialized in TimelineCommentRepository. "
                "Call set_user_client() first or use methods "
                "that don't require UserClient."
            )
        return self._user_client

    async def create_entity(
        self, data: TimelineCommentCreate
    ) -> TimelineCommDB:
        """Создает новый комментарий с проверкой связанных объектов"""
        await self._create_or_update_related(data)
        return await self.create(data=data)

    async def update_entity(
        self, data: TimelineCommentUpdate | TimelineCommentCreate
    ) -> TimelineCommDB:
        """Обновляет существующий лид"""
        await self._create_or_update_related(data)
        return await self.update(data=data)

    async def _get_related_create(self) -> dict[str, tuple[Any, Any, bool]]:
        """Возвращает кастомные проверки для дочерних классов"""
        return {
            "author_id": (self.user_client, UserDB, True),
        }

    async def get_existing_comments_entity(
        self, entity_type: EntityType, entity_id: int
    ) -> list[TimelineCommDB]:
        """Получает существующие комментарии для сделки"""
        stmt = select(TimelineCommDB).where(
            TimelineCommDB.entity_type == entity_type,
            TimelineCommDB.entity_id == entity_id,
            TimelineCommDB.is_deleted_in_bitrix.is_(False),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
