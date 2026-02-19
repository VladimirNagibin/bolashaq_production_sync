# from typing import Any

from pydantic import BaseModel


class ProductCharacteristic(BaseModel):  # type: ignore[misc]
    """Модель для характеристики товара"""

    name: str
    value: str
    unit: str | None = None


class KitItem(BaseModel):  # type: ignore[misc]
    """Модель для элемента комплектации"""

    code: str  # артикул, например "S245-01"
    name: str  # название
    description: str  # описание
    specifications: dict[str, str]  # технические характеристики


class ProductSection(BaseModel):  # type: ignore[misc]
    """Структура для частей описания товара"""

    announcement: str  # анонс/назначение
    description: str  # подробное описание
    characteristics: list[ProductCharacteristic]  # характеристики
    kit: list[KitItem]  # комплектация
