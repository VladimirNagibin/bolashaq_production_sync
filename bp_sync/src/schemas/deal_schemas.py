from datetime import datetime, timezone
from typing import Any

from pydantic import Field, field_validator

from .base_schemas import BaseCreateSchema, BaseUpdateSchema, CommonFieldMixin
from .bitrix_validators import BitrixValidators
from .enums import DealStatusEnum, StageSemanticEnum


class BaseDeal:
    """
    Общие поля создания и обновления с алиасами для соответствия
    SQLAlchemy модели
    """

    # Идентификаторы и основные данные
    additional_info: str | None = Field(None, alias="ADDITIONAL_INFO")

    # Статусы и флаги
    probability: int | None = Field(None, alias="PROBABILITY")
    repeat_sale_segment_id: str | None = Field(
        None, alias="REPEAT_SALE_SEGMENT_ID"
    )
    introduction_offer: str | None = Field(None, alias="UF_CRM_1759510370")

    # Условия сделки
    delivery_days: int | None = Field(None, alias="UF_CRM_1759510532")
    warranty_months: int | None = Field(None, alias="UF_CRM_1759510662")
    contract: str | None = Field(None, alias="UF_CRM_1760952984")

    # Финансовые данные
    tax_value: float | None = Field(None, alias="TAX_VALUE")
    half_amount: float | None = Field(None, alias="UF_CRM_1760872964")
    begining_condition_payment_percentage: int | None = Field(
        None, alias="UF_CRM_1759510807"
    )
    shipping_condition_payment_percentage: int | None = Field(
        None, alias="UF_CRM_1759510842"
    )

    # Временные метки
    moved_time: datetime | None = Field(None, alias="MOVED_TIME")

    # География и источники
    location_id: str | None = Field(None, alias="LOCATION_ID")

    # Связи с другими сущностями
    currency_id: str | None = Field(None, alias="CURRENCY_ID")
    type_id: str | None = Field(None, alias="TYPE_ID")
    lead_id: int | None = Field(None, alias="LEAD_ID")
    company_id: int | None = Field(None, alias="COMPANY_ID")
    contact_id: int | None = Field(None, alias="CONTACT_ID")
    source_id: str | None = Field(None, alias="SOURCE_ID")
    quote_id: int | None = Field(None, alias="QUOTE_ID")

    contact_ids: list[int] | None = Field(None, alias="CONTACT_IDS")

    # Связи по пользователю
    moved_by_id: int | None = Field(None, alias="MOVED_BY_ID")

    # Социальные профили
    wz_instagram: str | None = Field(None, alias="UF_CRM_6909F9E973085")
    wz_vc: str | None = Field(None, alias="UF_CRM_6909F9E984D21")
    wz_telegram_username: str | None = Field(
        None, alias="UF_CRM_6909F9E9A38DA"
    )
    wz_telegram_id: str | None = Field(None, alias="UF_CRM_6909F9E9ADB80")
    wz_avito: str | None = Field(None, alias="UF_CRM_6909F9E98F0B8")
    wz_maxid: str | None = Field(None, alias="UF_CRM_6909F9E9994A9")

    # Вспомогательные флаги
    without_offer: bool | None = Field(default=None, alias="UF_CRM_1763633586")
    without_contract: bool | None = Field(
        default=None, alias="UF_CRM_1763633629"
    )

    offer_link: str | None = Field(None, alias="UF_CRM_1763483026")
    date_answer_client: datetime | None = Field(
        default=None, alias="UF_CRM_1763626692"
    )
    moved_date: datetime | None = Field(default=None)

    @field_validator("external_id", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_str_to_int(cls, value: str | int) -> int:
        """Автоматическое преобразование строк в числа для ID"""
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return value  # type: ignore[return-value]


class DealCreate(BaseCreateSchema, BaseDeal):
    """Модель для создания сделок"""

    # Идентификаторы и основные данные
    title: str = Field(..., alias="TITLE")

    # Статусы и флаги
    is_manual_opportunity: bool = Field(False, alias="IS_MANUAL_OPPORTUNITY")
    closed: bool = Field(False, alias="CLOSED")
    is_new: bool = Field(False, alias="IS_NEW")
    is_recurring: bool = Field(False, alias="IS_RECURRING")
    is_return_customer: bool = Field(False, alias="IS_RETURN_CUSTOMER")
    is_repeated_approach: bool = Field(False, alias="IS_REPEATED_APPROACH")

    # Финансовые данные
    opportunity: float = Field(0.0, alias="OPPORTUNITY")

    # Временные метки
    begindate: datetime = Field(..., alias="BEGINDATE")
    closedate: datetime = Field(..., alias="CLOSEDATE")

    # Перечисляемые типы
    stage_semantic_id: StageSemanticEnum = Field(
        StageSemanticEnum.PROSPECTIVE, alias="STAGE_SEMANTIC_ID"
    )

    # Связи с другими сущностями
    stage_id: str = Field(..., alias="STAGE_ID")
    category_id: int = Field(..., alias="CATEGORY_ID")

    status_deal: DealStatusEnum = Field(
        DealStatusEnum.NOT_DEFINE, alias="UF_CRM_1763479557"
    )

    @field_validator("stage_semantic_id", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_stage_semantic_id(cls, v: Any) -> StageSemanticEnum:
        return BitrixValidators.convert_enum(
            v, StageSemanticEnum, StageSemanticEnum.PROSPECTIVE
        )

    @field_validator("closedate", mode="before")  # type: ignore[misc]
    @classmethod
    def set_closedate_default(cls, value: datetime | None) -> datetime:
        if value is None:
            return datetime.now(timezone.utc)
        return value

    @field_validator("status_deal", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_status_deal(cls, v: Any) -> DealStatusEnum:
        return BitrixValidators.convert_enum(
            v, DealStatusEnum, DealStatusEnum.NOT_DEFINE
        )


class DealUpdate(BaseUpdateSchema, BaseDeal):
    """Модель для частичного обновления сделок"""

    # Основные поля с алиасами (все необязательные)
    title: str | None = Field(default=None, alias="TITLE")

    # Статусы и флаги
    is_manual_opportunity: bool | None = Field(
        default=None, alias="IS_MANUAL_OPPORTUNITY"
    )
    closed: bool | None = Field(default=None, alias="CLOSED")
    is_new: bool | None = Field(default=None, alias="IS_NEW")
    is_recurring: bool | None = Field(default=None, alias="IS_RECURRING")
    is_return_customer: bool | None = Field(
        default=None, alias="IS_RETURN_CUSTOMER"
    )
    is_repeated_approach: bool | None = Field(
        default=None, alias="IS_REPEATED_APPROACH"
    )

    # Финансовые данные
    opportunity: float | None = Field(default=None, alias="OPPORTUNITY")

    # Временные метки
    begindate: datetime | None = Field(default=None, alias="BEGINDATE")
    closedate: datetime | None = Field(default=None, alias="CLOSEDATE")

    # Перечисляемые типы
    stage_semantic_id: StageSemanticEnum | None = Field(
        default=None, alias="STAGE_SEMANTIC_ID"
    )

    # Связи с другими сущностями
    stage_id: str | None = Field(default=None, alias="STAGE_ID")
    category_id: int | None = Field(default=None, alias="CATEGORY_ID")

    status_deal: DealStatusEnum | None = Field(
        default=None, alias="UF_CRM_1763479557"
    )

    @field_validator("stage_semantic_id", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_stage_semantic_id(cls, v: Any) -> StageSemanticEnum:
        return BitrixValidators.convert_enum(
            v, StageSemanticEnum, StageSemanticEnum.PROSPECTIVE
        )

    @field_validator("status_deal", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_status_deal(cls, v: Any) -> DealStatusEnum:
        return BitrixValidators.convert_enum(
            v, DealStatusEnum, DealStatusEnum.NOT_DEFINE
        )


class AddInfoCreate(CommonFieldMixin):
    """Модель для создания менеджеров"""

    deal_id: int
    comment: str


class AddInfoUpdate(CommonFieldMixin):
    """Модель для частичного обновления менеджеров"""

    deal_id: int | None = Field(default=None)
    comment: str | None = Field(default=None)
