from typing import Any

from schemas.base_schemas import ListResponseSchema
from schemas.timeline_comment_schemas import (
    TimelineCommentCreate,
    TimelineCommentUpdate,
)

from ..bitrix_services.base_bitrix_services import BaseBitrixEntityClient


class TimeLineCommentBitrixClient(
    BaseBitrixEntityClient[TimelineCommentCreate, TimelineCommentUpdate]
):
    entity_name = "timeline.comment"
    create_schema = TimelineCommentCreate
    update_schema = TimelineCommentUpdate

    async def get_comments_by_entity(
        self, entity_type: str, entity_id: int
    ) -> ListResponseSchema[TimelineCommentUpdate]:
        filter_entity: dict[str, Any] = {
            "ENTITY_TYPE": entity_type,
            "ENTITY_ID": entity_id,
        }
        select = [
            "ID",
            "COMMENT",
            "CREATED",
            "AUTHOR_ID",
            "ENTITY_TYPE",
            "ENTITY_ID",
        ]
        start = 0
        return await self.list(
            select=select, filter_entity=filter_entity, start=start
        )
