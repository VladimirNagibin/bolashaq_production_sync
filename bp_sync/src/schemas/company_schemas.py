from datetime import datetime
from typing import Any

from pydantic import Field, field_validator

from .base_schemas import (
    AddressMixin,
    BaseCreateSchema,
    BaseUpdateSchema,
    CommunicationChannel,
    HasCommunicationCreateMixin,
    HasCommunicationUpdateMixin,
)
from .enums import SYSTEM_USER_ID


class BaseCompany:
    """Base schema of Contact"""

    # Финансы
    banking_details: str | None = Field(None, alias="BANKING_DETAILS")

    # География и источники
    origin_version: str | None = Field(None, alias="ORIGIN_VERSION")
    employees: str | None = Field(None, alias="EMPLOYEES")

    # Адреса
    address_legal: str | None = Field(None, alias="ADDRESS_LEGAL")

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


class CompanyCreate(
    BaseCreateSchema, BaseCompany, AddressMixin, HasCommunicationCreateMixin
):
    """Contact create schema"""

    # Идентификаторы и основные данные
    title: str = Field(..., alias="TITLE")

    # Финансы
    revenue: float = Field(default=0.0, alias="REVENUE")

    # Статусы и флаги
    is_my_company: bool = Field(default=False, alias="IS_MY_COMPANY")

    @classmethod
    def get_default_entity(cls, external_id: int) -> "CompanyCreate":
        now = datetime.now()
        company_data: dict[str, Any] = {
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
            # Обязательные поля из CompanyCreate
            "title": f"Deleted Company {external_id}",
            # Задаем external_id и флаг удаления
            "external_id": external_id,  # Внешний ID
            "is_deleted_in_bitrix": True,
            # created_at=now,
            # updated_at=now,
        }
        return CompanyCreate(**company_data)


class CompanyUpdate(
    BaseUpdateSchema, BaseCompany, AddressMixin, HasCommunicationUpdateMixin
):
    """Contact create schema"""

    # Идентификаторы и основные данные
    title: str | None = Field(default=None, alias="TITLE")

    # Финансы
    revenue: float | None = Field(default=None, alias="REVENUE")

    # Статусы и флаги
    is_my_company: bool | None = Field(default=None, alias="IS_MY_COMPANY")
