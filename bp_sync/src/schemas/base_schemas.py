from datetime import datetime
from enum import Enum
from typing import Any, ClassVar
from uuid import UUID

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
)
from typing_extensions import Self


class CommonFieldMixin(BaseModel):  # type: ignore[misc]
    """
    Базовый миксин для всех моделей с общими полями.

    Предоставляет общие поля и методы для сравнения сущностей.
    """

    # Константы для исключаемых полей при сравнении
    EXCLUDED_FIELDS: ClassVar[set[str]] = {
        "internal_id",
        "created_at",
        "updated_at",
        "is_deleted_in_bitrix",
    }
    internal_id: UUID | None = Field(
        default=None,
        exclude=True,
        init_var=False,
        description="Внутренний UUID идентификатор",
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
    external_id: int | str | None = Field(
        default=None,
        validation_alias=AliasChoices("ID", "id"),
        description="Внешний идентификатор (ID из Битрикс)",
    )

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        validate_assignment=True,
        str_strip_whitespace=True,
        extra="ignore",
        json_encoders={
            datetime: lambda v: v.isoformat(),
            UUID: str,
        },
    )

    @property
    def id(self) -> UUID | None:
        """Алиас для internal_id."""
        return self.internal_id

    @id.setter
    def id(self, value: UUID) -> None:
        """Сеттер для internal_id."""
        self.internal_id = value

    def get_changes(
        self, entity: Self, exclude_fields: set[str] | None = None
    ) -> dict[str, dict[str, Any]]:
        """
        Сравнивает две сущности и возвращает различия.

        Args:
            entity: Сущность для сравнения
            exclude_fields: Поля для исключения из сравнения

        Returns:
            Словарь с различиями в формате
            {поле: {internal: значение, external: значение}}

        Example:
            >>> changes = old_entity.get_changes(new_entity)
            >>> print(changes)
            {'name': {'internal': 'Old', 'external': 'New'}}
        """
        if exclude_fields is None:
            exclude_fields = self.EXCLUDED_FIELDS

        differences: dict[str, dict[str, Any]] = {}

        model_class = self.__class__
        fields = model_class.model_fields

        for field_name in fields:
            if field_name in exclude_fields:
                continue

            old_value = getattr(self, field_name)
            new_value = getattr(entity, field_name)

            # Сравниваем значения
            if not self._are_values_equal(field_name, old_value, new_value):
                differences[field_name] = {
                    "internal": old_value,
                    "external": new_value,
                }

        return differences

    def _are_values_equal(
        self, field_name: str, value1: Any, value2: Any
    ) -> bool:
        """
        Сравнивает два значения с учетом специальных типов данных.

        Args:
            field_name: Имя поля для специальной обработки
            value1: Первое значение
            value2: Второе значение

        Returns:
            True если значения равны, иначе False
        """
        # Оба значения None
        if value1 is None and value2 is None:
            return True

        if self._handle_special_fields(field_name, value1, value2):
            return True

        # Одно из значений None
        if value1 is None or value2 is None:
            return False

        # Для Enum сравниваем значения
        if isinstance(value1, Enum) and isinstance(value2, Enum):
            return bool(value1.value == value2.value)

        # Для Pydantic моделей рекурсивно сравниваем все поля
        if isinstance(value1, BaseModel) and isinstance(value2, BaseModel):
            return bool(value1.model_dump() == value2.model_dump())

        # Для списков и словарей сравниваем содержимое
        if isinstance(value1, (list, dict)) and isinstance(
            value2, (list, dict)
        ):
            return bool(value1 == value2)

        # Стандартное сравнение
        return bool(value1 == value2)

    def _handle_special_fields(
        self, field_name: str, value1: Any, value2: Any
    ) -> bool:
        """
        Обрабатывает специальные случаи для определенных полей.

        Returns:
            True если значения считаются равными для специального поля
        """
        special_handlers = {
            "company_id": self._compare_company_id,
        }

        handler = special_handlers.get(field_name)
        return handler(value1, value2) if handler else False

    def _compare_company_id(self, value1: Any, value2: Any) -> bool:
        """Сравнивает значения company_id с учетом 0 и None."""
        return value1 in (0, None) and value2 in (0, None)


class ListResponseSchema(BaseModel):  # type: ignore[misc]
    """
    Схема для ответа со списком сущностей.

    Attributes:
        result: Список сущностей
        total: Общее количество сущностей
        next: Идентификатор для пагинации (следующая страница)
    """

    result: list[CommonFieldMixin] = Field(
        default_factory=list[CommonFieldMixin], description="Список сущностей"
    )
    total: int = Field(ge=0, description="Общее количество сущностей")
    next: int | None = Field(
        default=None,
        ge=0,
        description="Идентификатор для пагинации (следующая страница)",
    )

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        extra="ignore",
        json_encoders={
            datetime: lambda v: v.isoformat(),
            UUID: str,
        },
    )
