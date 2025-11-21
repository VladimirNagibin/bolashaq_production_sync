from datetime import datetime
from typing import Any

from pydantic import Field, field_validator

from schemas.enums import StageSemanticEnum

from .base_schemas import (
    AddressMixin,
    BaseCreateSchema,
    BaseUpdateSchema,
    CommunicationChannel,
    HasCommunicationCreateMixin,
    HasCommunicationUpdateMixin,
)
from .bitrix_validators import BitrixValidators
from .enums import SYSTEM_USER_ID


class BaseLead:
    """Base schema of Lead"""

    # Идентификаторы и основные данные
    name: str | None = Field(None, alias="NAME")
    second_name: str | None = Field(None, alias="SECOND_NAME")
    last_name: str | None = Field(None, alias="LAST_NAME")
    post: str | None = Field(None, alias="POST")
    company_title: str | None = Field(None, alias="COMPANY_TITLE")

    # Временные метки
    birthdate: datetime | None = Field(None, alias="BIRTHDATE")
    date_closed: datetime | None = Field(None, alias="DATE_CLOSED")
    moved_time: datetime | None = Field(None, alias="MOVED_TIME")

    # Связи с другими сущностями
    currency_id: str | None = Field(None, alias="CURRENCY_ID")
    company_id: int | None = Field(None, alias="COMPANY_ID")
    contact_id: int | None = Field(None, alias="CONTACT_ID")
    source_id: str | None = Field(None, alias="SOURCE_ID")

    # Связи по пользователю
    moved_by_id: int | None = Field(None, alias="MOVED_BY_ID")

    # Коммуникации
    phone: list[CommunicationChannel] | None = Field(None, alias="PHONE")
    email: list[CommunicationChannel] | None = Field(None, alias="EMAIL")
    web: list[CommunicationChannel] | None = Field(None, alias="WEB")
    im: list[CommunicationChannel] | None = Field(None, alias="IM")
    link: list[CommunicationChannel] | None = Field(None, alias="LINK")

    @field_validator("external_id", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_str_to_int(cls, value: str | int) -> int:
        """Автоматическое преобразование строк в числа для ID"""
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return value  # type: ignore[return-value]


class LeadCreate(
    BaseCreateSchema, BaseLead, AddressMixin, HasCommunicationCreateMixin
):
    """Contact create schema"""

    # Идентификаторы и основные данные
    title: str = Field(..., alias="TITLE")

    # Статусы и флаги
    is_manual_opportunity: bool = Field(
        default=False, alias="IS_MANUAL_OPPORTUNITY"
    )
    is_return_customer: bool = Field(default=False, alias="IS_RETURN_CUSTOMER")

    # Финансовые данные
    opportunity: float = Field(default=0.0, alias="OPPORTUNITY")

    # Перечисляемые типы
    status_semantic_id: StageSemanticEnum = Field(
        default=StageSemanticEnum.PROSPECTIVE, alias="STATUS_SEMANTIC_ID"
    )

    # Связи с другими сущностями
    status_id: str = Field(..., alias="STATUS_ID")

    @field_validator("status_semantic_id", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_status_semantic_id(cls, v: Any) -> StageSemanticEnum:
        return BitrixValidators.convert_enum(
            v, StageSemanticEnum, StageSemanticEnum.PROSPECTIVE
        )

    @classmethod
    def get_default_entity(cls, external_id: int) -> "LeadCreate":
        now = datetime.now()
        lead_data: dict[str, Any] = {
            # Обязательные поля из TimestampsCreateMixin
            "date_create": now,
            "date_modify": now,
            # Обязательные поля из UserRelationsCreateMixin
            "assigned_by_id": SYSTEM_USER_ID,
            "created_by_id": SYSTEM_USER_ID,
            "modify_by_id": SYSTEM_USER_ID,
            # Обязательные поля из HasCommunicationCreateMixin
            "has_phone": False,
            "has_email": False,
            "has_imol": False,
            # Обязательные поля из LeadCreate
            "status_id": "NEW",
            "title": f"Deleted Lead {external_id}",
            # Задаем external_id и флаг удаления
            "external_id": external_id,  # Внешний ID
            "is_deleted_in_bitrix": True,
            # created_at=now,
            # updated_at=now,
        }
        return LeadCreate(**lead_data)


class LeadUpdate(
    BaseUpdateSchema, BaseLead, AddressMixin, HasCommunicationUpdateMixin
):
    """Contact create schema"""

    # Основные поля с алиасами (все необязательные)
    title: str | None = Field(None, alias="TITLE")

    # Статусы и флаги
    is_manual_opportunity: bool | None = Field(
        None, alias="IS_MANUAL_OPPORTUNITY"
    )
    is_return_customer: bool | None = Field(None, alias="IS_RETURN_CUSTOMER")

    # Финансовые данные
    opportunity: float | None = Field(None, alias="OPPORTUNITY")

    # Перечисляемые типы
    status_semantic_id: StageSemanticEnum | None = Field(
        None, alias="STATUS_SEMANTIC_ID"
    )

    # Связи с другими сущностями
    status_id: str | None = Field(None, alias="STATUS_ID")

    @field_validator("status_semantic_id", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_status_semantic_id(cls, v: Any) -> StageSemanticEnum:
        return BitrixValidators.convert_enum(
            v, StageSemanticEnum, StageSemanticEnum.PROSPECTIVE
        )
