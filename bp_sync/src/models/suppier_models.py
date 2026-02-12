from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    false,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.postgres import Base
from schemas.enums import EntityType, SourcesProductEnum

from .bases import IntIdEntity

if TYPE_CHECKING:
    from .product_models import Product as ProductDB


class SupplierProduct(IntIdEntity):
    """
    Товары/продукты поставщиков.
    Хранит сырые данные, полученные от поставщиков до валидации и маппинга.
    """

    __tablename__ = "supplier_products"
    # TODO: _schema_class = SupplierProductCreate

    __table_args__ = (
        Index("ix_supplier_products_source", "source"),
        Index("ix_supplier_products_code", "code"),
        Index("ix_supplier_products_product_id", "product_id"),
        CheckConstraint(
            "price >= 0", name="ck_supplier_products_price_positive"
        ),
        CheckConstraint(
            "quantity >= 0", name="ck_supplier_products_quantity_positive"
        ),
        UniqueConstraint("source", "code", name="uq_supplier_source_code"),
    )

    @property
    def entity_type(self) -> EntityType:
        return EntityType.SUPPLIER_PRODUCT

    @property
    def tablename(self) -> str:
        return self.__tablename__

    def __str__(self) -> str:
        return str(self.name)

    # Основные данные товара
    name: Mapped[str] = mapped_column(
        String(500),
        comment="Название товара",
    )
    code: Mapped[str | None] = mapped_column(
        String(100),
        index=True,
        comment="Символьный код",
    )
    active: Mapped[bool | None] = mapped_column(
        Boolean,
        comment="Активен",
    )
    sort: Mapped[int | None] = mapped_column(Integer, comment="Сортировка")
    xml_id: Mapped[str | None] = mapped_column(
        String(100),
        comment="Внешний код",
    )

    # Цены и валюта
    price: Mapped[float | None] = mapped_column(Numeric(12, 2), comment="Цена")
    currency_id: Mapped[str | None] = mapped_column(
        String(10),
        comment="Валюта",
    )

    # Описание
    description: Mapped[str | None] = mapped_column(Text, comment="Описание")
    description_type: Mapped[str | None] = mapped_column(
        String(10), comment="Тип описания"
    )

    # Поля из свойств товаров
    link: Mapped[str | None] = mapped_column(
        String(500),
        comment="Ссылка",
    )
    original_name: Mapped[str | None] = mapped_column(
        String(500),
        comment="Оригинальное название",
    )
    standards: Mapped[str | None] = mapped_column(
        String(500), comment="Стандарты"
    )
    article: Mapped[str | None] = mapped_column(String(255), comment="Артикул")

    # Дополнительные поля из источников
    supplier_category: Mapped[str | None] = mapped_column(
        String(150), index=True, comment="Категория в системе поставщика"
    )
    supplier_subcategory: Mapped[str | None] = mapped_column(
        String(150), index=True, comment="Подкатегория в системе поставщика"
    )

    # Медиа
    detail_picture: Mapped[str | None] = mapped_column(
        String(500), comment="Детальная картинка (путь)"
    )
    detail_picture_description: Mapped[str | None] = mapped_column(
        String(255), comment="Описание для детальной картинки"
    )
    preview_picture: Mapped[str | None] = mapped_column(
        String(500), comment="Картинка для анонса (путь)"
    )
    preview_picture_description: Mapped[str | None] = mapped_column(
        String(255), comment="Описание для картинки анонса"
    )
    preview_text: Mapped[str | None] = mapped_column(
        Text, comment="Описание для анонса"
    )
    preview_text_type: Mapped[str | None] = mapped_column(
        String(10), comment="Тип описания для анонса"
    )

    # Статус и наличие
    availability_status: Mapped[str | None] = mapped_column(
        String(50), comment="Статус наличия"
    )
    quantity: Mapped[float | None] = mapped_column(
        Numeric(10, 2), comment="Остаток"
    )

    # Метаданные источника
    source: Mapped[SourcesProductEnum] = mapped_column(
        String(20), comment="Источник данных"
    )
    is_validated: Mapped[bool] = mapped_column(
        Boolean,
        server_default=false(),
        default=False,
        comment="Флаг обработки позиции",
    )
    should_export_to_crm: Mapped[bool] = mapped_column(
        Boolean,
        server_default=false(),
        default=False,
        comment="Выгружать в CRM",
    )
    internal_section_id: Mapped[int | None] = mapped_column(
        Integer, comment="Раздел в CRM"
    )

    # Связь с главной таблицей продуктов (Номенклатурой)
    product_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("products.id"),
        ondelete="SET NULL",
        nullable=True,
        index=True,
        comment="Идентификатор связанного товара в системе",
    )
    product: Mapped["ProductDB" | None] = relationship(
        "ProductDB",
        foreign_keys=[product_id],
        back_populates="supplier_product",
    )

    # Данные для предложений (Offers)
    preview_for_offer: Mapped[str | None] = mapped_column(
        Text, comment="Анонс для предложенияя"
    )
    description_for_offer: Mapped[str | None] = mapped_column(
        Text, comment="Описание для предложения"
    )

    # Связь с характеристиками
    characteristics: Mapped[list["SupplierCharacteristic"]] = relationship(
        "SupplierCharacteristic",
        back_populates="supplier_product",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="name",
    )

    # Связь с комплектующими (complects)
    complects: Mapped[list["SupplierComplect"]] = relationship(
        "SupplierComplect",
        back_populates="supplier_product",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class SourceImportConfig(Base):  # type: ignore[misc]
    """
    Основные настройки импорта для поставщиков
    """

    __tablename__ = "source_import_config"
    # TODO: _schema_class = SourceImportConfigCreate

    __table_args__ = (
        UniqueConstraint(
            "source", "config_name", name="uq_import_config_source_name"
        ),
    )

    def __str__(self) -> str:
        return f"{self.source}: {self.config_name if self.config_name else ''}"

    # Основные данные
    source: Mapped[SourcesProductEnum] = mapped_column(
        String(20), nullable=False, comment="Источник данных"
    )
    config_name: Mapped[str | None] = mapped_column(
        String(255), comment="Название конфигурации"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=true(),
        comment="Активность конфигурации",
    )

    # Настройки формата файла
    file_format: Mapped[str | None] = mapped_column(
        String(10),
        default="XLSX",
        comment="Формат файла: CSV, XLSX, XML и т.д.",
    )
    encoding: Mapped[str | None] = mapped_column(
        String(20),
        default="UTF-8",
        comment="Кодировка файла, например UTF-8",
    )
    delimiter: Mapped[str | None] = mapped_column(
        String(5),
        # default=";",
        comment="Разделитель для CSV.",
    )

    # Настройки структуры файла (Строки)
    header_row_index: Mapped[int | None] = mapped_column(
        Integer, comment="Номер строки с заголовками"
    )
    data_start_row: Mapped[int | None] = mapped_column(
        Integer, comment="Номер начала данных"
    )
    column_mappings: Mapped[list["SourceColumnMapping"]] = relationship(
        "SourceColumnMapping",
        back_populates="config",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="SourceColumnMapping.display_order",
    )


class SourceColumnMapping(Base):  # type: ignore[misc]
    """
    Маппинг колонок источника на поля целевой таблицы.
    Определяет соответствие между колонками в импортируемом файле и полями БД.
    """

    __tablename__ = "source_column_mapping"
    # TODO: _schema_class = SourceColumnMappingCreate

    __table_args__ = (
        UniqueConstraint(
            "config_id",
            "source_column_index",
            name="uq_column_mapping_config_index",
        ),
        UniqueConstraint(
            "config_id", "target_field", name="uq_column_mapping_config_target"
        ),
        Index("ix_column_mappings_config_id", "config_id"),
        Index("ix_column_mappings_target_field", "target_field"),
    )

    def __str__(self) -> str:
        return f"{self.source_column_name} -> {self.target_field}"

    config_id: Mapped[UUID] = mapped_column(
        ForeignKey("source_import_config.id", ondelete="CASCADE"),
        nullable=False,
        comment="Конфигурация источника данных",
    )
    config: Mapped["SourceImportConfig"] = relationship(
        "SourceImportConfig",
        back_populates="column_mappings",
        foreign_keys=[config_id],
    )

    # Что в нашей системе
    target_field: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Имя поля в базе данных"
    )

    # Что у поставщика
    source_column_name: Mapped[str] = mapped_column(
        String(255), comment="Имя столбца в загружаемом файле"
    )
    source_column_index: Mapped[int] = mapped_column(
        Integer, comment="Номер столбца в загружаемом файле"
    )

    # Настройки обработки
    force_import: Mapped[bool] = mapped_column(
        Boolean,
        server_default=false(),
        default=False,
        comment="Перегружать в CRM без проверки",
    )
    data_type: Mapped[str | None] = mapped_column(
        String(20), comment="Тип данных: string, integer, decimal, date и т.д."
    )
    transformation_rule: Mapped[str | None] = mapped_column(
        String(50), comment="Правило трансформации (regexp, формула)"
    )

    # Порядок и статус
    display_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Для UI и порядка обработки",
    )


class SupplierCharacteristic(Base):  # type: ignore[misc]
    """
    Дополнительные характеристики товара (свойства).
    """

    __tablename__ = "supplier_characteristics"
    # TODO: _schema_class = SupplierCharacteristicCreate

    def __str__(self) -> str:
        return str(self.name)

    name: Mapped[str] = mapped_column(
        String(500),
        comment="Название характеристики",
    )
    value: Mapped[str | None] = mapped_column(
        String(255),
        comment="Значение характеристики",
    )
    unit: Mapped[str | None] = mapped_column(
        String(255),
        comment="Единица измерения",
    )
    supplier_product_id: Mapped[UUID] = mapped_column(
        ForeignKey("supplier_products.id", ondelete="CASCADE"),
        nullable=False,
        comment="Ссылка на товар поставщика",
    )
    supplier_product: Mapped["SupplierProduct"] = relationship(
        "SupplierProduct",
        forien_keys=[supplier_product_id],
        back_populates="characteristics",
    )


class SupplierComplect(Base):  # type: ignore[misc]
    """
    Комплектующие товары (Аксессуары).
    """

    __tablename__ = "supplier_complects"
    # TODO: _schema_class = SupplierComplectCreate

    def __str__(self) -> str:
        return str(self.name)

    name: Mapped[str] = mapped_column(
        String(500),
        comment="Название комплектующего",
    )
    code: Mapped[str | None] = mapped_column(
        String(100),
        index=True,
        comment="Символьный код",
    )
    description: Mapped[str | None] = mapped_column(Text, comment="Описание")
    specifications: Mapped[str | None] = mapped_column(
        Text, comment="Спецификации"
    )

    supplier_product_id: Mapped[UUID] = mapped_column(
        ForeignKey("supplier_products.id", ondelete="CASCADE"),
        nullable=False,
        comment="Ссылка на товар поставщика",
    )
    supplier_product: Mapped["SupplierProduct"] = relationship(
        "SupplierProduct",
        forien_keys=[supplier_product_id],
        back_populates="complects",
    )
