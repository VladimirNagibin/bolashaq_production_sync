from datetime import datetime
from enum import Enum
from typing import Any, Callable, Type, TypeVar, cast

EnumT = TypeVar("EnumT", bound=Enum)
T = TypeVar("T")
SYSTEM_USER_ID = 37


class BitrixValidators:
    """Класс с общими валидаторами для Bitrix схем"""

    # Специальные поля для пользовательских ID
    _USER_FIELDS = {
        "CREATED_BY_ID",
        "created_by_id",
        "MODIFY_BY_ID",
        "modify_by_id",
        "updatedBy",
    }

    @staticmethod
    def normalize_empty_values(data: Any, fields: dict[str, Any]) -> Any:
        """
        Преобразует пустые строки в None и нормализует типы данных.

        Args:
            data: Входные данные для нормализации
            fields: Словарь с настройками типов полей

        Returns:
            Нормализованные данные
        """
        if not isinstance(data, dict):
            return data

        processed_data: dict[str, Any] = cast(dict[str, Any], data)

        for field_name, value in list(processed_data.items()):
            # Применяем цепочку преобразований
            new_field_name, new_value = BitrixValidators._process_field(
                field_name, value, fields
            )
            # Обновляем данные, если поле не исключено
            if new_field_name not in BitrixValidators._get_excluded_fields():
                processed_data[new_field_name] = new_value
            elif new_field_name in processed_data:
                del processed_data[new_field_name]

        return processed_data

    @staticmethod
    def _process_field(
        field_name: str, value: Any, fields: dict[str, Any]
    ) -> tuple[str, Any]:
        """Обрабатывает одно поле через цепочку преобразований"""
        # 1. Переименование полей
        field_name = BitrixValidators._rename_field(field_name)

        # 2. Обработка пользовательских полей
        value = BitrixValidators._process_user_fields(field_name, value)

        # 3. Применение типизированных преобразований
        value = BitrixValidators._apply_type_transformations(
            field_name, value, fields
        )

        return field_name, value

    @staticmethod
    def _rename_field(field_name: str) -> str:
        """Переименовывает специальные поля"""
        if field_name == "id":
            return "ID"
        return field_name

    @staticmethod
    def _process_user_fields(field_name: str, value: Any) -> Any:
        """Обрабатывает поля, связанные с пользователями"""
        if field_name in BitrixValidators._USER_FIELDS:
            try:
                return value if int(value) else SYSTEM_USER_ID
            except (ValueError, TypeError):
                return SYSTEM_USER_ID
        return value

    @staticmethod
    def _apply_type_transformations(
        field_name: str, value: Any, fields: dict[str, Any]
    ) -> Any:
        """Применяет преобразования в зависимости от типа поля"""
        field_types = BitrixValidators._get_field_types(field_name, fields)

        for field_type in field_types:
            transformer = BitrixValidators._TRANSFORMERS.get(field_type)
            if transformer:
                result = transformer(value)
                # if result is not None:
                return result
        return value

    @staticmethod
    def _get_field_types(field_name: str, fields: dict[str, Any]) -> list[str]:
        """Определяет типы поля на основе конфигурации"""
        field_types: list[str] = []

        for field_type, field_list in fields.items():
            if field_name in field_list:
                field_types.append(field_type)

        return field_types

    @staticmethod
    def _get_excluded_fields() -> set[str]:
        """Возвращает набор исключенных полей"""
        # Замените на реальные исключенные поля из вашего класса
        return set()

    # Словарь преобразователей для различных типов полей
    _TRANSFORMERS: dict[str, Callable[[Any], Any]] = {
        "str_none": lambda v: None if not v else v,
        "int_none": lambda v: None if not v or v == "0" else v,
        "bool": lambda v: bool(v in ("Y", "1", 1, True)),
        "bool_none": lambda v: bool(v in ("Y", "1", 1, True)),
        "datetime": lambda v: BitrixValidators.parse_datetime(v),
        "datetime_none": lambda v: BitrixValidators.parse_datetime(v),
        "float": lambda v: BitrixValidators.normalize_float(v),
        "list": lambda v: BitrixValidators.normalize_list(v),
        "list_in_int": lambda v: BitrixValidators.list_in_int(v),
        # "dict_none": (
        #    lambda v: v.get("value") if v and isinstance(v, dict) else None
        # ),
        "money": lambda v: BitrixValidators.normalize_money(v),
    }

    @staticmethod
    def normalize_float(v: Any) -> float:
        """
        Нормализует числовые поля.

        Args:
            v: Любое значение для преобразования в float

        Returns:
            float: Нормализованное число (0 в случае ошибки)
        """
        if v in (None, ""):
            return 0.0
        try:
            return float(str(v).replace(" ", ""))
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def parse_datetime(v: Any) -> datetime | None:
        """
        Парсит строковые даты в объекты datetime.

        Поддерживает форматы:
        - ISO формат: '2023-12-31T23:59:59'
        - Bitrix формат: '31.12.2023 23:59:59'

        Args:
            v: Значение для парсинга

        Returns:
            datetime | None: Объект datetime или None при ошибке
        """
        if not v:
            return None

        if isinstance(v, datetime):
            return v

        # Попытка парсинга ISO формата
        if isinstance(v, str) and ("T" in v or "-" in v):
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except ValueError:
                pass

        # Попытка парсинга Bitrix формата "dd.mm.YYYY HH:MM:SS"
        if isinstance(v, str):
            try:
                return datetime.strptime(v, "%d.%m.%Y %H:%M:%S")
            except ValueError:
                pass

        # Последняя попытка - стандартный парсер
        try:
            return datetime.fromisoformat(str(v))
        except (ValueError, TypeError):
            return None

    @staticmethod
    def convert_enum(v: Any, enum_type: Type[EnumT], default: EnumT) -> EnumT:
        """
        Преобразует значения в enum.

        Args:
            v: Значение для преобразования
            enum_type: Тип enum
            default: Значение по умолчанию

        Returns:
            EnumT: Значение enum
        """
        if v is None or v == "":
            return default

        try:
            if isinstance(v, str) and v.isdigit():
                v = int(v)
            return enum_type(v)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def normalize_list(v: Any) -> list[Any]:
        """
        Нормализует значение в список.

        Args:
            v: Значение для нормализации

        Returns:
            list: Нормализованный список (пустой список в случае ошибки)
        """
        if v is None:
            return []
        return v if isinstance(v, list) else []

    @staticmethod
    def list_in_int(v: Any) -> int:
        """
        Извлекает первое значение из списка и преобразует в int.

        Args:
            v: Значение для обработки

        Returns:
            int: Первый элемент списка как int (0 в случае ошибки)
        """
        if not v:
            return 0

        if isinstance(v, list) and v:
            try:
                return int(v[0])
            except (ValueError, TypeError):
                return 0
        return 0

    @staticmethod
    def normalize_money(v: Any) -> float:
        """
        Преобразует денежные значения из формата Bitrix в float.

        Поддерживает форматы:
        - "1953500|KZT" → 1953500.0
        - Числовые значения
        - Строки с числами

        Args:
            v: Значение для преобразования

        Returns:
            float: Числовое значение (0.0 в случае ошибки)
        """
        if v is None:
            return 0.0

        try:
            if isinstance(v, str):
                # Обработка формата "1953500|KZT"
                if "|" in v:
                    number_part = v.split("|")[0].strip()
                    return float(number_part)
                else:
                    return float(v)
            else:
                return float(v)
        except (ValueError, TypeError, IndexError):
            return 0.0
