import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, TypeAdapter

from schemas.open_ai_schemas import KitItem, ProductCharacteristic
from schemas.supplier_schemas import (
    SupplierCharacteristicUpdate,
    SupplierComplectUpdate,
)

# Создаем TypeAdapter для списка ProductCharacteristic
product_characteristic_list_adapter = TypeAdapter(list[ProductCharacteristic])
# Создаем TypeAdapter для списка KitItem
kit_item_list_adapter = TypeAdapter(list[KitItem])

supp_product_charact_list_adapter = TypeAdapter(
    list[SupplierCharacteristicUpdate]
)
supp_complect_item_list_adapter = TypeAdapter(list[SupplierComplectUpdate])


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, Decimal):
            return float(obj)
        # Добавьте другие типы по необходимости
        return super().default(obj)


class PreprocessedDataSerializer:

    @staticmethod
    def serialize_for_cache(data: dict[str, Any]) -> str:
        """
        Сериализует словарь с Pydantic моделями в JSON строку для кэширования
        """

        def encoder(obj: Any) -> Any:
            # Для Pydantic моделей используем model_dump() (Pydantic v2)
            if isinstance(obj, BaseModel):
                return obj.model_dump()

            # Для datetime объектов
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()

            # Для UUID
            if isinstance(obj, UUID):
                return str(obj)

            # Для Decimal
            if isinstance(obj, Decimal):
                return float(obj)

            # Для множеств
            if isinstance(obj, set):
                return list(obj)

            # Если ничего не подошло, пробуем стандартный механизм
            try:
                json.dumps(obj)
                return obj
            except TypeError:
                return str(obj)

        return json.dumps(data, default=encoder, ensure_ascii=False, indent=2)

    @staticmethod
    def deserialize_from_cache(cache_data: str) -> dict[str, Any]:
        """
        Десериализует JSON строку из кэша обратно в словарь с Pydantic моделями
        """
        # Сначала парсим JSON в обычный словарь
        raw_dict = json.loads(cache_data)

        # Преобразуем специфические поля обратно в Pydantic модели
        result = {}

        for key, value in raw_dict.items():
            if key == "characteristics" and "new_value" in value:
                # Преобразуем список характеристик
                if value["new_value"]:
                    v = product_characteristic_list_adapter.validate_python(
                        value["new_value"]
                    )
                    value["new_value"] = v
            if key == "characteristics" and "old_value" in value:
                # Преобразуем список характеристик
                if value["old_value"]:
                    v = supp_product_charact_list_adapter.validate_python(
                        value["old_value"]
                    )
                    value["old_value"] = v
            if key == "complects" and "new_value" in value:
                # Преобразуем список комплектации
                if value["new_value"]:
                    value["new_value"] = kit_item_list_adapter.validate_python(
                        value["new_value"]
                    )
            if key == "complects" and "old_value" in value:
                # Преобразуем список комплектации
                if value["old_value"]:
                    v = supp_complect_item_list_adapter.validate_python(
                        value["old_value"]
                    )
                    value["old_value"] = v

            result[key] = value

        return result
