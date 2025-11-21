from datetime import datetime
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .base_schemas import CommonFieldMixin, EntityAwareSchema
from .bitrix_validators import BitrixValidators
from .enums import EntityType
from .fields import FIELDS_TIMELINE_COMMENT


class BaseTimelineComment(CommonFieldMixin):
    """
    Общие поля создания и обновления с алиасами для соответствия
    SQLAlchemy модели
    """

    FIELDS_BY_TYPE: ClassVar[dict[str, str]] = FIELDS_TIMELINE_COMMENT

    created: datetime | None = Field(None, alias="CREATED")
    author_id: int | None = Field(None, alias="AUTHOR_ID")
    comment_entity: str | None = Field(None, alias="COMMENT")

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        extra="ignore",
    )


class TimelineCommentCreate(BaseTimelineComment, EntityAwareSchema):
    """Модель для создания пользователей"""

    entity_id: int = Field(..., alias="ENTITY_ID")
    entity_type: EntityType = Field(..., alias="ENTITY_TYPE")

    @field_validator("entity_type", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_entity_type(cls, v: Any) -> EntityType:
        if isinstance(v, str):
            v = v.capitalize()
        return BitrixValidators.convert_enum(v, EntityType, EntityType.DEAL)


class TimelineCommentUpdate(
    BaseTimelineComment, BaseModel  # type: ignore[misc]
):
    """Модель для частичного обновления пользователей"""

    entity_id: int | None = Field(None, alias="ENTITY_ID")
    entity_type: EntityType | None = Field(None, alias="ENTITY_TYPE")

    @field_validator("entity_type", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_entity_type(cls, v: Any) -> EntityType:
        if isinstance(v, str):
            v = v.capitalize()
        return BitrixValidators.convert_enum(v, EntityType, EntityType.DEAL)
