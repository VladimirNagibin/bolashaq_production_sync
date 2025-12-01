from datetime import datetime
from typing import Any, Type
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from schemas.enums import EntityType, EntityTypeAbbr

# from schemas.fields import FIELDS_PRODUCT_ALT
from schemas.product_schemas import (
    FieldText,
    FieldValue,
    ProductCreate,
    ProductEntityCreate,
)

from .bases import IntIdEntity
from .user_models import User


class Product(IntIdEntity):
    """
    Товары/Продукты
    """

    __tablename__ = "products"
    _schema_class = ProductCreate

    @property
    def entity_type(self) -> EntityType:
        return EntityType.PRODUCT

    @property
    def tablename(self) -> str:
        return self.__tablename__

    def __str__(self) -> str:
        return str(self.name)

    # Основные данные товара
    name: Mapped[str] = mapped_column(
        comment="Название товара"
    )  # NAME : Название товара

    code: Mapped[str | None] = mapped_column(
        comment="Символьный код"
    )  # CODE : Символьный код

    active: Mapped[bool | None] = mapped_column(
        comment="Активен"
    )  # ACTIVE : Активен (Y/N)

    sort: Mapped[int | None] = mapped_column(
        comment="Сортировка"
    )  # SORT : Сортировка

    xml_id: Mapped[str | None] = mapped_column(
        comment="Внешний код"
    )  # XML_ID : Внешний код

    # Временные метки
    date_create: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Дата создания"
    )  # DATE_CREATE : Дата создания

    date_modify: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Дата изменения"
    )  # TIMESTAMP_X : Дата изменения

    modified_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.external_id"), comment="Кем изменён"
    )  # MODIFIED_BY : Кем изменён
    modified_user: Mapped["User"] = relationship(
        "User", foreign_keys=[modified_by], back_populates="modified_products"
    )

    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.external_id"), comment="Кем создан"
    )  # CREATED_BY : Кем создан
    created_user: Mapped["User"] = relationship(
        "User", foreign_keys=[created_by], back_populates="created_products"
    )

    # Каталог и раздел
    catalog_id: Mapped[int | None] = mapped_column(
        comment="Каталог"
    )  # CATALOG_ID : Каталог

    section_id: Mapped[int | None] = mapped_column(
        comment="Раздел"
    )  # SECTION_ID : Раздел

    # Цены и валюта
    price: Mapped[float | None] = mapped_column(comment="Цена")  # PRICE : Цена

    currency_id: Mapped[str | None] = mapped_column(
        comment="Валюта"
    )  # CURRENCY_ID : Валюта

    # НДС
    vat_id: Mapped[int | None] = mapped_column(
        comment="Ставка НДС"
    )  # VAT_ID : Ставка НДС

    vat_included: Mapped[bool | None] = mapped_column(
        comment="НДС включён в цену"
    )  # VAT_INCLUDED : НДС включён в цену (Y/N)

    # Единица измерения
    measure: Mapped[int | None] = mapped_column(
        comment="Единица измерения"
    )  # MEASURE : Единица измерения

    # Описание
    description: Mapped[str | None] = mapped_column(
        comment="Описание"
    )  # DESCRIPTION : Описание

    description_type: Mapped[str | None] = mapped_column(
        comment="Тип описания"
    )  # DESCRIPTION_TYPE : Тип описания

    properties: Mapped[list["ProductProperty"]] = relationship(
        "ProductProperty",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    simple_properties: Mapped[list["ProductSimpleProperty"]] = relationship(
        "ProductSimpleProperty",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    # Свойства товара (PROPERTY_*)
    # Ссылка
    # link: Mapped[str | None] = mapped_column(
    #     comment="Ссылка"
    # )  # PROPERTY_111 : Ссылка

    # # Доп описание
    # additional_description: Mapped[str | None] = mapped_column(
    #     comment="Доп описание"
    # )  # PROPERTY_113 : Доп описание

    # # Оригинальное название
    # original_name: Mapped[str | None] = mapped_column(
    #     comment="Оригинальное название"
    # )  # PROPERTY_115 : Оригинальное название

    # # Стандарты
    # standards: Mapped[str | None] = mapped_column(
    #     comment="Стандарты"
    # )  # PROPERTY_117 : Стандарты

    # # Артикул
    # article: Mapped[str | None] = mapped_column(
    #     comment="Артикул"
    # )  # PROPERTY_119 : Артикул

    # # Технические характеристики
    # characteristics: Mapped[str | None] = mapped_column(
    #     comment="Технические характеристики"
    # )  # PROPERTY_121 : Технические характеристики

    # # Тех характеристики для печати
    # characteristics_for_print: Mapped[str | None] = mapped_column(
    #     comment="Тех характеристики для печати"
    # )  # PROPERTY_123 : Тех характеристики для печати

    # # Комплект поставки для печати
    # complect_for_print: Mapped[str | None] = mapped_column(
    #     comment="Комплект поставки для печати"
    # )  # PROPERTY_125 : Комплект поставки для печати

    # # Комплект поставки
    # complect: Mapped[str | None] = mapped_column(
    #     comment="Комплект поставки"
    # )  # PROPERTY_127 : Комплект поставки

    # # Описание для документов
    # description_for_print: Mapped[str | None] = mapped_column(
    #     comment="Описание для документов"
    # )  # PROPERTY_129 : Описание для документов

    # # Стандарты для печати
    # standards_for_print: Mapped[str | None] = mapped_column(
    #     comment="Стандарты для печати"
    # )  # PROPERTY_131 : Стандарты для печати

    # Связь с товарами в сущностях
    product_entities: Mapped[list["ProductEntity"]] = relationship(
        "ProductEntity",
        back_populates="product",
        lazy="selectin",
    )

    async def to_pydantic(
        self,
        schema_class: Type[ProductCreate] | None = None,
        exclude_relationships: bool = True,
    ) -> ProductCreate:
        """
        Преобразует объект SQLAlchemy в Pydantic схему

        Args:
            schema_class: Класс Pydantic схемы
            exclude_relationships: Исключать ли связи из преобразования

        Returns:
            Экземпляр Pydantic схемы
        """
        schema_class = schema_class or self._get_schema_class()
        if schema_class is None:
            raise ValueError(
                "Cannot automatically determine schema class for "
                f"{self.__class__.__name__}. Please provide schema_class "
                "parameter or set _schema_class."
            )
        data: dict[str, Any] = {}
        # Получаем все поля схемы
        for field_name in schema_class.model_fields:
            # Пропускаем поля, которые являются связями и должны быть исключены
            if exclude_relationships and self._is_relationship_field(
                field_name
            ):
                continue

            if hasattr(self, field_name):
                value = getattr(self, field_name)
                data.update(self._transform_field_value(field_name, value))
        if hasattr(self, "id"):
            data["internal_id"] = self.id
        # for property in self.simple_properties:
        #     data[property.property_code] = property.to_pydantic_()
        # for property in self.properties:
        #     data[property.property_code] = property.to_pydantic_()
        return schema_class(**data)


class ProductSimpleProperty(IntIdEntity):
    """
    SQLAlchemy модель для хранения простых пользовательских свойств товара.
    """

    __tablename__ = "product_simple_properties"
    # _schema_class = FieldValue

    # Внешний ключ к товару
    product_id: Mapped[UUID] = mapped_column(
        ForeignKey("products.id"), index=True, comment="Внешний ключ к товару"
    )

    # Код свойства из Bitrix (например, 'link', 'original_name')
    property_code: Mapped[str] = mapped_column(
        index=True, comment="Наименование свойства"
    )

    value: Mapped[str | None] = mapped_column(
        comment="Значение свойства"
    )  # value : Значение свойства

    # Обратная связь для удобства доступа к товару из свойства
    product: Mapped["Product"] = relationship(
        "Product", back_populates="simple_properties"
    )

    def __repr__(self) -> str:
        return (
            "<ProductSimpleProperty"
            f"({self.property_code}, product_id={self.product_id}"
        )

    def to_pydantic_(self) -> FieldValue:
        data: dict[str, Any] = {
            "value_id": self.external_id,
            "value": self.value,
        }
        return FieldValue(**data)


class ProductProperty(IntIdEntity):
    """
    SQLAlchemy модель для хранения простых пользовательских свойств товара.
    """

    __tablename__ = "product_properties"
    # _schema_class = FieldValue

    # Внешний ключ к товару
    product_id: Mapped[UUID] = mapped_column(
        ForeignKey("products.id"), index=True, comment="Внешний ключ к товару"
    )

    # Код свойства из Bitrix (например, 'link', 'original_name')
    property_code: Mapped[str] = mapped_column(
        index=True, comment="Наименование свойства"
    )

    text_field: Mapped[str | None] = mapped_column(
        nullable=True, comment="Значение свойства"
    )
    type_field: Mapped[str | None] = mapped_column(
        nullable=True, comment="Значение свойства"
    )
    product: Mapped["Product"] = relationship(
        "Product", back_populates="properties"
    )

    def __repr__(self) -> str:
        return (
            f"<ProductProperty(id={self.id}, product_id={self.product_id}, "
            f"code='{self.property_code}')>"
        )

    def to_pydantic_(self) -> FieldValue:
        value = FieldText(
            text_field=self.text_field, type_field=self.type_field
        )
        data: dict[str, Any] = {"value_id": self.external_id, "value": value}
        return FieldValue(**data)


class ProductEntity(IntIdEntity):
    """
    Товары в сущностях (сделках, лидах и т.д.)
    """

    __tablename__ = "product_entities"
    _schema_class = ProductEntityCreate

    @property
    def entity_type(self) -> EntityType:
        return EntityType.PRODUCT

    @property
    def tablename(self) -> str:
        return self.__tablename__

    def __str__(self) -> str:
        return f"ProductEntity {self.external_id}: {self.product_name}"

    # Идентификаторы и основные данные
    product_name: Mapped[str | None] = mapped_column(
        comment="Название товара"
    )  # productName : Название товара

    price: Mapped[float | None] = mapped_column(comment="Цена")  # price : Цена

    price_exclusive: Mapped[float | None] = mapped_column(
        comment="Цена без налога со скидкой"
    )  # priceExclusive : Цена без налога со скидкой

    price_netto: Mapped[float | None] = mapped_column(
        comment="PRICE_NETTO"
    )  # priceNetto : PRICE_NETTO

    price_brutto: Mapped[float | None] = mapped_column(
        comment="PRICE_BRUTTO"
    )  # priceBrutto : PRICE_BRUTTO

    quantity: Mapped[float | None] = mapped_column(
        comment="Количество"
    )  # quantity : Количество

    discount_type_id: Mapped[int | None] = mapped_column(
        comment="Тип скидки"
    )  # discountTypeId : Тип скидки

    discount_rate: Mapped[float | None] = mapped_column(
        comment="Величина скидки"
    )  # discountRate : Величина скидки

    discount_sum: Mapped[float | None] = mapped_column(
        comment="Сумма скидки"
    )  # discountSum : Сумма скидки

    tax_rate: Mapped[float | None] = mapped_column(
        comment="Налог"
    )  # taxRate : Налог

    tax_included: Mapped[bool | None] = mapped_column(
        comment="Налог включен в цену"
    )  # taxIncluded : Налог включен в цену Y/N

    customized: Mapped[bool | None] = mapped_column(
        comment="Изменен"
    )  # customized : Изменен

    measure_code: Mapped[int | None] = mapped_column(
        comment="Код единицы измерения"
    )  # measureCode : Код единицы измерения

    measure_name: Mapped[str | None] = mapped_column(
        comment="Единица измерения"
    )  # measureName : Единица измерения

    sort: Mapped[int | None] = mapped_column(
        comment="Сортировка"
    )  # sort : Сортировка

    type: Mapped[int | None] = mapped_column(comment="TYPE")  # type : TYPE

    store_id: Mapped[int | None] = mapped_column(
        comment="STORE_ID"
    )  # storeId : STORE_ID

    # Связи с владельцем
    owner_id: Mapped[int] = mapped_column(
        comment="ID владельца"
    )  # ownerId : ID владельца

    owner_type: Mapped[EntityTypeAbbr] = mapped_column(
        comment="Тип владельца"
    )  # ownerType : Тип владельца

    # Связь с товаром
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.external_id"), comment="Товар"
    )  # productId : Товар
    product: Mapped["Product"] = relationship(
        "Product", back_populates="product_entities"
    )
