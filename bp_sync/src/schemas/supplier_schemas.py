from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from typing_extensions import Annotated

from schemas.enums import SourceKeyField, SourcesProductEnum


class BaseFields(BaseModel):  # type: ignore[misc]
    """Базовая схема товара поставщика."""

    id: UUID | None = Field(
        default=None,
        # exclude=False,
        # init_var=False,
        description="Внутренний UUID идентификатор",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )
    created_at: datetime | None = Field(
        default=None,
        description="Дата и время создания записи",
    )
    updated_at: datetime | None = Field(
        default=None,
        description="Дата и время последнего обновления",
    )
    is_deleted_in_bitrix: bool | None = Field(
        default=None,
        description="Флаг удаления в Битрикс",
    )

    model_config = ConfigDict(
        from_attributes=True,
        # use_enum_values=True,
        # populate_by_name=True,
        # arbitrary_types_allowed=True,
        # validate_assignment=True,
        # str_strip_whitespace=True,
        # extra="ignore",
        json_encoders={
            datetime: lambda v: v.isoformat(),
            UUID: str,
        },
    )


# ----------------------------------------------------------------------
# SupplierProduct Schemas
# ----------------------------------------------------------------------
class SupplierProductBase(BaseFields):
    """Базовая схема товара поставщика."""

    code: Annotated[str, StringConstraints(max_length=100)] | None = None
    active: bool | None = None
    sort: int | None = None
    xml_id: Annotated[str, StringConstraints(max_length=100)] | None = None

    # Цены и валюта
    price: float | None = None
    currency_id: Annotated[str, StringConstraints(max_length=10)] | None = None

    # Описание
    description: str | None = None
    description_type: (
        Annotated[str, StringConstraints(max_length=10)] | None
    ) = None

    # Поля из свойств
    link: Annotated[str, StringConstraints(max_length=500)] | None = None
    original_name: Annotated[str, StringConstraints(max_length=500)] | None = (
        None
    )
    standards: Annotated[str, StringConstraints(max_length=500)] | None = None
    article: Annotated[str, StringConstraints(max_length=255)] | None = None

    # Категории
    supplier_category: (
        Annotated[str, StringConstraints(max_length=150)] | None
    ) = None
    supplier_subcategory: (
        Annotated[str, StringConstraints(max_length=150)] | None
    ) = None

    # Медиа
    detail_picture: (
        Annotated[str, StringConstraints(max_length=500)] | None
    ) = None
    detail_picture_description: (
        Annotated[str, StringConstraints(max_length=255)] | None
    ) = None
    preview_picture: (
        Annotated[str, StringConstraints(max_length=500)] | None
    ) = None
    preview_picture_description: (
        Annotated[str, StringConstraints(max_length=255)] | None
    ) = None
    more_photo: str | None = None
    preview_text: str | None = None
    preview_text_type: (
        Annotated[str, StringConstraints(max_length=10)] | None
    ) = None

    # Наличие
    availability_status: (
        Annotated[str, StringConstraints(max_length=50)] | None
    ) = None
    quantity: float | None = None

    # Метаданные
    internal_section_id: int | None = None

    # Связи
    product_id: UUID | None = None

    # Для предложений
    preview_for_offer: str | None = None
    description_for_offer: str | None = None


class SupplierProductCreate(SupplierProductBase):
    """Создание товара поставщика."""

    external_id: int = Field(description="Внешний идентификатор")
    name: Annotated[str, StringConstraints(max_length=500)]
    source: SourcesProductEnum
    is_validated: bool = False
    should_export_to_crm: bool = False
    needs_review: bool = True


class SupplierProductUpdate(SupplierProductBase):
    """Обновление товара поставщика (все поля опциональны)."""

    external_id: int | None = None
    name: Annotated[str, StringConstraints(max_length=500)] | None = None
    source: SourcesProductEnum | None = None
    is_validated: bool | None = None
    should_export_to_crm: bool | None = None
    needs_review: bool | None = None


# ----------------------------------------------------------------------
# ImportConfig Schemas
# ----------------------------------------------------------------------
class ImportConfigBase(BaseFields):
    """Базовая схема конфигурации импорта."""

    config_name: Annotated[str, StringConstraints(max_length=255)] | None = (
        None
    )
    is_active: bool = True

    file_format: Annotated[str, StringConstraints(max_length=10)] | None = (
        None  # "XLSX"
    )
    encoding: Annotated[str, StringConstraints(max_length=20)] | None = (
        None  # "UTF-8"
    )
    delimiter: Annotated[str, StringConstraints(max_length=5)] | None = None

    header_row_index: int | None = None
    data_start_row: int | None = None


class ImportConfigCreate(ImportConfigBase):
    """Создание конфигурации импорта."""

    source: SourcesProductEnum
    source_key_field: SourceKeyField = SourceKeyField.EXTERNAL_ID


class ImportConfigUpdate(ImportConfigBase):
    """Обновление конфигурации импорта."""

    source: SourcesProductEnum | None = None
    source_key_field: SourceKeyField | None = None


# ----------------------------------------------------------------------
# ImportColumnMapping Schemas
# ----------------------------------------------------------------------
class ImportColumnMappingBase(BaseFields):
    """Базовая схема маппинга колонок."""

    data_type: Annotated[str, StringConstraints(max_length=20)] | None = None
    transformation_rule: (
        Annotated[str, StringConstraints(max_length=50)] | None
    ) = None


class ImportColumnMappingCreate(ImportColumnMappingBase):
    """Создание маппинга колонок."""

    config_id: UUID
    target_field: Annotated[str, StringConstraints(max_length=100)]
    source_column_name: Annotated[str, StringConstraints(max_length=255)]
    source_column_index: int
    force_import: bool = False
    sync_with_crm: bool = False
    display_order: int = 0


class ImportColumnMappingUpdate(ImportColumnMappingBase):
    """Обновление маппинга колонок."""

    config_id: UUID | None = None
    target_field: Annotated[str, StringConstraints(max_length=100)] | None = (
        None
    )
    source_column_name: (
        Annotated[str, StringConstraints(max_length=255)] | None
    ) = None
    source_column_index: int | None = None
    force_import: bool | None = None
    sync_with_crm: bool | None = None
    display_order: int | None = None


# ----------------------------------------------------------------------
# SupplierCharacteristic Schemas
# ----------------------------------------------------------------------
class SupplierCharacteristicBase(BaseFields):
    """Базовая схема характеристики товара."""

    value: Annotated[str, StringConstraints(max_length=255)] | None = None
    unit: Annotated[str, StringConstraints(max_length=255)] | None = None


class SupplierCharacteristicCreate(SupplierCharacteristicBase):
    """Создание характеристики."""

    name: Annotated[str, StringConstraints(max_length=500)]
    supplier_product_id: UUID


class SupplierCharacteristicUpdate(SupplierCharacteristicBase):
    """Обновление характеристики."""

    name: Annotated[str, StringConstraints(max_length=500)] | None = None
    supplier_product_id: UUID | None = None


# ----------------------------------------------------------------------
# SupplierComplect Schemas
# ----------------------------------------------------------------------
class SupplierComplectBase(BaseFields):
    """Базовая схема комплектующего."""

    code: Annotated[str, StringConstraints(max_length=100)] | None = None
    description: str | None = None
    specifications: str | None = None


class SupplierComplectCreate(SupplierComplectBase):
    """Создание комплектующего."""

    name: Annotated[str, StringConstraints(max_length=500)]
    supplier_product_id: UUID


class SupplierComplectUpdate(SupplierComplectBase):
    """Обновление комплектующего."""

    name: Annotated[str, StringConstraints(max_length=500)] | None = None
    supplier_product_id: UUID | None = None


# ----------------------------------------------------------------------
# Response Schemas with Relations
# ----------------------------------------------------------------------
class SupplierProductDetail(SupplierProductCreate):
    """Товар поставщика с характеристиками и комплектующими."""

    characteristics: list[SupplierCharacteristicCreate] = []
    complects: list[SupplierComplectCreate] = []


class ImportConfigDetail(ImportConfigCreate):
    """Конфигурация импорта с маппингами."""

    column_mappings: list[ImportColumnMappingCreate] = []


class ImportResult(BaseModel):  # type: ignore[misc]
    """Результат импорта."""

    added_count: int = 0
    updated_count: int = 0
    force_import_count: int = 0
    bitrix_update_count: int = 0
    errors: list[str] = []
    bitrix_updates: list[Any] = []

    @property
    def total_processed(self) -> int:
        return self.added_count + self.updated_count
