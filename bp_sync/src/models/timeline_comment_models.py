from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from schemas.enums import EntityType

from .bases import IntIdEntity
from .user_models import User

if TYPE_CHECKING:
    from .deal_models import Deal


class TimelineComment(IntIdEntity):
    """
    Комментарии из ленты сущности
    """

    __tablename__ = "timeline_comments"

    def __str__(self) -> str:
        return str(
            self.comment_entity[:30]
            if self.comment_entity
            else self.deal.title
        )

    # Идентификаторы и основные данные
    created: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Дата добавления"
    )  # CREATED
    entity_id: Mapped[int] = mapped_column(
        comment="ID элемента, к которому привязан комментарий"
    )  # ENTITY_ID
    entity_type: Mapped[EntityType] = mapped_column(
        String(20), comment="Тип элемента, к которому привязан комментарий"
    )  # ENTITY_TYPE
    author_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.external_id"),
        comment="Автор",
    )  # AUTHOR_ID
    author: Mapped["User"] = relationship(
        "User", foreign_keys=[author_id], back_populates="timeline_comments"
    )
    comment_entity: Mapped[str | None] = mapped_column(
        comment="Текст комментария"
    )  # COMMENT

    deal: Mapped["Deal"] = relationship(
        "Deal",
        back_populates="timeline_comments",
        foreign_keys="[TimelineComment.entity_id]",
        primaryjoin=(
            "and_(Deal.external_id == TimelineComment.entity_id, "
            "TimelineComment.entity_type == 'Deal')"
        ),
        viewonly=True,
    )
