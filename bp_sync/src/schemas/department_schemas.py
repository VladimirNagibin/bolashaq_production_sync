from typing import Any

from pydantic import ConfigDict, Field, field_validator

from .base_schemas import CommonFieldMixin


class Department(CommonFieldMixin):
    """
    Общие поля создания и обновления с алиасами для соответствия
    SQLAlchemy модели
    """

    name: str = Field(alias="NAME")
    parent_id: int | None = Field(None, alias="PARENT")

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        extra="ignore",
    )

    def model_dump_db(self, exclude_unset: bool = False) -> dict[str, Any]:
        return self.model_dump(  # type: ignore[no-any-return]
            exclude_unset=exclude_unset
        )

    @field_validator("external_id", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_str_to_int(cls, value: str | int) -> int:
        """Автоматическое преобразование строк в числа для ID"""
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return value  # type: ignore[return-value]
