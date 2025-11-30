from datetime import datetime
from typing import Any, ClassVar

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)
from pydantic.fields import FieldInfo

from .base_schemas import CommonFieldMixin, EntityAwareSchema
from .enums import EntityTypeAbbr
from .fields import FIELDS_PRODUCT, FIELDS_PRODUCT_ALT
from .helpers import parse_numeric_string


class BaseProductEntity(CommonFieldMixin):
    """
    Общие поля создания и обновления с алиасами для соответствия
    SQLAlchemy модели
    """

    FIELDS_BY_TYPE: ClassVar[dict[str, str]] = FIELDS_PRODUCT
    FIELDS_BY_TYPE_ALT: ClassVar[dict[str, str]] = FIELDS_PRODUCT_ALT
    _EXCLUDED_FIELDS = FIELDS_PRODUCT_ALT["exclude_b24"]

    # Идентификаторы и основные данные
    product_name: str | None = Field(None, alias="productName")  # Название тов
    price: float | None = Field(None, alias="price")  # Цена
    price_exclusive: float | None = Field(
        None, alias="priceExclusive"
    )  # Цена без налога со скидкой
    price_netto: float | None = Field(None, alias="priceNetto")  # PRICE_NETTO
    price_brutto: float | None = Field(
        None, alias="priceBrutto"
    )  # PRICE_BRUTTO
    quantity: float | None = Field(None, alias="quantity")  # Количество
    discount_type_id: int | None = Field(
        None, alias="discountTypeId"
    )  # Тип скидки
    discount_rate: float | None = Field(
        None, alias="discountRate"
    )  # Величина скидки
    discount_sum: float | None = Field(
        None, alias="discountSum"
    )  # Сумма скидки
    tax_rate: float | None = Field(None, alias="taxRate")  # Налог
    tax_included: bool | None = Field(
        None, alias="taxIncluded"
    )  # Налог включен в цену Y/N
    customized: bool | None = Field(None, alias="customized")  # Изменен
    measure_code: int | None = Field(
        None, alias="measureCode"
    )  # Код единицы измерения
    measure_name: str | None = Field(
        None, alias="measureName"
    )  # Единица измерения
    sort: int | None = Field(None, alias="sort")  # Сортировка
    type: int | None = Field(None, alias="type")  # TYPE
    store_id: int | None = Field(None, alias="storeId")  # STORE_ID

    @field_validator("external_id", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_str_to_int(cls, value: str | int) -> int:
        """Автоматическое преобразование строк в числа для ID"""
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return value  # type: ignore[return-value]

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        extra="ignore",
    )

    def equals_ignore_owner(self, other: "BaseProductEntity") -> bool:
        """Сравнивает два объекта, игнорируя поля"""
        fields_meta = self.__class__.model_fields

        for field_name in fields_meta:
            if field_name in FIELDS_PRODUCT_ALT["exclude_b24"]:
                continue

            value1 = getattr(self, field_name)
            value2 = getattr(other, field_name)
            # Специальная обработка для float
            if isinstance(value1, float) and isinstance(value2, float):
                if abs(value1 - value2) > 1e-6:
                    return False
            elif value1 != value2:
                return False

        return True

    # def to_bitrix_dict(self) -> dict[str, Any]:
    #    """Преобразует модель в словарь для Bitrix API"""
    #    data = self.model_dump(
    #        by_alias=True,
    #        exclude_none=True,
    #        exclude_unset=True,  # опционально: исключить неустановленные поля
    #    )

    # Дополнительные преобразования
    #    result: dict[str, Any] = {}
    #    for alias, value in data.items():
    #        if alias in FIELDS_PRODUCT_ALT["exclude_b24"]:
    #            continue
    #        elif isinstance(value, bool):
    #            # Булёвы значения -> "Y"/"N"
    #            result[alias] = "Y" if value else "N"
    #        else:
    #            # Остальные значения без изменений (проверка ссылочных полей)
    #            result[alias] = value
    #    return result


class ProductEntityCreate(BaseProductEntity, EntityAwareSchema):
    """Модель для создания товаров в сущности"""

    owner_id: int = Field(..., alias="ownerId")  # ID владельца
    owner_type: EntityTypeAbbr = Field(..., alias="ownerType")  # Тип владельца
    product_id: int = Field(..., alias="productId")  # Товар


class ProductEntityUpdate(BaseProductEntity):
    """Модель для частичного обновления товаров в сущности"""

    owner_id: int | None = Field(None, alias="ownerId")  # ID владельца
    owner_type: EntityTypeAbbr | None = Field(
        None, alias="ownerType"
    )  # Тип владельца
    product_id: int | None = Field(None, alias="productId")  # Товар


class ListProductEntity(BaseModel):  # type: ignore[misc]
    """Схема для списка товаров сущности"""

    result: list[ProductEntityCreate]

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        extra="ignore",
    )

    def equals_ignore_owner(self, other: "ListProductEntity") -> bool:
        """Сравнивает два списка продуктов, игнорируя owner-поля"""
        if len(self.result) != len(other.result):
            return False

        return all(
            item1.equals_ignore_owner(item2)
            for item1, item2 in zip(self.result, other.result)
        )

    def to_bitrix_dict(self) -> list[dict[str, Any]]:
        return [
            product_entity.to_bitrix_dict() for product_entity in self.result
        ]

    @property
    def count_products(self) -> int:
        return len(self.result)


class FieldText(BaseModel):  # type: ignore[misc]
    text_field: str | None = Field(
        None, validation_alias=AliasChoices("TEXT", "text")
    )  # TEXT
    type_field: str | None = Field(
        "HTML", validation_alias=AliasChoices("TYPE", "type")
    )  # TYPE (HTML/TEXT)

    def to_bitrix_dict(self, alias_choice: int) -> dict[str, Any]:
        result: dict[str, Any] = {}

        for field_name, field_info in self.__class__.model_fields.items():
            value = getattr(self, field_name, None)
            if value is None:
                continue

            # Получаем финальный алиас для поля на основе alias_choice
            field_alias = self._get_field_alias(field_info, alias_choice)

            result[field_alias] = value

        return result

    def _get_field_alias(
        self, field_info: FieldInfo, alias_choice: int
    ) -> str:
        """
        Вспомогательный метод для получения алиаса поля из FieldInfo.
        """
        validation_alias = field_info.validation_alias
        if isinstance(validation_alias, AliasChoices):
            # Безопасный выбор алиаса с проверкой границ
            choice_index = max(
                0, min(alias_choice - 1, len(validation_alias.choices) - 1)
            )
            return validation_alias.choices[choice_index]  # type: ignore

        # Если AliasChoices не используется, пробуем получить обычный алиас
        return field_info.alias or field_info.name  # type: ignore


class FieldValue(BaseModel):  # type: ignore[misc]
    value_id: int = Field(..., alias="valueId")  # id value
    value: str | FieldText = Field(..., alias="value")  # value


class BaseProduct(CommonFieldMixin):
    """
    Общие поля создания и обновления с алиасами для соответствия
    SQLAlchemy модели
    """

    FIELDS_BY_TYPE: ClassVar[dict[str, str]] = FIELDS_PRODUCT
    FIELDS_BY_TYPE_ALT: ClassVar[dict[str, str]] = FIELDS_PRODUCT_ALT

    code: str | None = Field(
        None, validation_alias=AliasChoices("CODE", "code")
    )  # CODE
    active: bool | None = Field(
        None, validation_alias=AliasChoices("ACTIVE", "active")
    )  # Активен
    sort: int | None = Field(
        None,
        validation_alias=AliasChoices("SORT", "sort"),
    )  # Сортировка
    xml_id: str | None = Field(
        None, validation_alias=AliasChoices("XML_ID", "xmlId")
    )  # Внешний код
    date_create: datetime | None = Field(
        None,
        validation_alias=AliasChoices("DATE_CREATE", "dateCreate"),
    )  # Дата создания
    date_modify: datetime | None = Field(
        None,
        validation_alias=AliasChoices("TIMESTAMP_X", "timestampX"),
    )  # Дата изменения
    modified_by: int | None = Field(
        None,
        validation_alias=AliasChoices("MODIFIED_BY", "modifiedBy"),
    )  # Кем изменён
    created_by: int | None = Field(
        None,
        validation_alias=AliasChoices("CREATED_BY", "createdBy"),
    )  # Кем создан
    catalog_id: int | None = Field(
        None,
        validation_alias=AliasChoices("CATALOG_ID", "iblockId"),
    )  # Каталог
    section_id: int | None = Field(
        None,
        validation_alias=AliasChoices("SECTION_ID", "iblockSectionId"),
    )  # Раздел
    price: float | None = Field(
        None,
        validation_alias=AliasChoices("PRICE", "price"),
    )  # Цена (в каталоге отдельный справочник)
    currency_id: str | None = Field(
        None,
        validation_alias=AliasChoices("CURRENCY_ID", "currency_id"),
    )  # Валюта (в каталоге отдельный справочник)
    vat_id: int | None = Field(
        None,
        validation_alias=AliasChoices("VAT_ID", "vatId"),
    )  # Ставка НДС
    vat_included: bool | None = Field(
        None,
        validation_alias=AliasChoices("VAT_INCLUDED", "vatIncluded"),
    )  # НДС включён в цену Y/N
    measure: int | None = Field(
        None,
        validation_alias=AliasChoices("MEASURE", "measure"),
    )  # Единица измерения
    description: str | None = Field(
        None, validation_alias=AliasChoices("DESCRIPTION", "detailText")
    )  # DESCRIPTION
    description_type: str | None = Field(
        None,
        validation_alias=AliasChoices("DESCRIPTION_TYPE", "detailTextType"),
    )  # DESCRIPTION_TYPE
    link: FieldValue | None = Field(
        None,
        validation_alias=AliasChoices("PROPERTY_111", "property111"),
    )  # Ссылка
    additional_description: FieldValue | None = Field(
        None,
        validation_alias=AliasChoices("PROPERTY_113", "property113"),
    )  # Доп описание
    original_name: FieldValue | None = Field(
        None,
        validation_alias=AliasChoices("PROPERTY_115", "property115"),
    )  # Оригинальное название
    standards: FieldValue | None = Field(
        None,
        validation_alias=AliasChoices("PROPERTY_117", "property117"),
    )  # Стандарты
    article: FieldValue | None = Field(
        None,
        validation_alias=AliasChoices("PROPERTY_119", "property119"),
    )  # Артикул
    characteristics: FieldValue | None = Field(
        None,
        validation_alias=AliasChoices("PROPERTY_121", "property121"),
    )  # Технические характеристики
    characteristics_for_print: FieldValue | None = Field(
        None,
        validation_alias=AliasChoices("PROPERTY_123", "property123"),
    )  # Тех характеристики для печати
    complect_for_print: FieldValue | None = Field(
        None,
        validation_alias=AliasChoices("PROPERTY_125", "property125"),
    )  # Комплект поставки для печати
    complect: FieldValue | None = Field(
        None,
        validation_alias=AliasChoices("PROPERTY_127", "property127"),
    )  # Комплект поставки
    description_for_print: FieldValue | None = Field(
        None,
        validation_alias=AliasChoices("PROPERTY_129", "property129"),
    )  # Описание для документов
    standards_for_print: FieldValue | None = Field(
        None,
        validation_alias=AliasChoices("PROPERTY_131", "property131"),
    )  # Стандарты для печати

    @field_validator("price", mode="before")  # type: ignore[misc]
    @classmethod
    def clean_numeric_fields(cls, v: Any) -> float | None:
        return parse_numeric_string(v)


class ProductCreate(BaseProduct, EntityAwareSchema):
    """Модель для создания товаров"""

    name: str = Field(
        ..., validation_alias=AliasChoices("NAME", "name")
    )  # Название

    @classmethod
    def get_default_entity(cls, external_id: int) -> "ProductCreate":
        product_data: dict[str, Any] = {
            "name": f"Deleted Product {external_id}",
            "external_id": external_id,
            "is_deleted_in_bitrix": True,
        }
        return ProductCreate(**product_data)


class ProductUpdate(BaseProduct):
    """Модель для частичного обновления товаров"""

    name: str | None = Field(
        None, validation_alias=AliasChoices("NAME", "name")
    )  # Название


class ListProduct(BaseModel):  # type: ignore[misc]
    """Схема для списка товаров сущности"""

    result: list[ProductCreate]

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        extra="ignore",
    )
