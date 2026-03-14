from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from schemas.enums import SourcesProductEnum


class ChangeLogBase(BaseModel):  # type: ignore[misc]
    """Базовая схема для лога изменений"""

    supplier_product_id: UUID | None = Field(
        None, description="ID товара поставщика"
    )
    source: SourcesProductEnum = Field(..., description="Источник данных")
    config_name: str | None = Field(
        None, description="Источник импорта (название файла или конфига)"
    )
    field_name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Название измененного поля",
    )
    old_value: str | None = Field(None, description="Значение ДО изменения")
    new_value: str | None = Field(None, description="Значение ПОСЛЕ изменения")
    value_type: str | None = Field(
        None, description="Тип значения (int, float, str, bool)"
    )


class ChangeLogCreate(ChangeLogBase):
    """Схема для создания записи в логе"""

    pass


class ChangeLogUpdate(BaseModel):  # type: ignore[misc]
    """Схема для обновления (ручная обработка)"""

    is_processed: bool = Field(False, description="Проверено вручную?")
    processed_at: datetime | None = Field(None, description="Когда проверили")
    processed_by_user_id: int | None = Field(
        None, description="ID пользователя, который проверил"
    )
    comment: str | None = Field(
        None, max_length=1000, description="Комментарий менеджера при проверке"
    )


class ChangeLogInDB(ChangeLogBase):
    """Схема для записи из БД"""

    id: UUID = Field(..., description="ID записи в логе")
    is_processed: bool = Field(..., description="Проверено вручную?")
    processed_at: datetime | None = Field(None, description="Когда проверили")
    processed_by_user_id: int | None = Field(
        None, description="ID пользователя, который проверил"
    )
    comment: str | None = Field(
        None, description="Комментарий менеджера при проверке"
    )

    model_config = ConfigDict(from_attributes=True)
