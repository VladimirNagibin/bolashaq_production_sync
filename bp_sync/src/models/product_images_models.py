from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from schemas.enums import EntityType, SourcesProductEnum

# from schemas.fields import FIELDS_PRODUCT_ALT
from schemas.product_image_schemas import ProductImageCreate

from .bases import IntIdEntity

if TYPE_CHECKING:
    from .product_models import Product


class ProductImage(IntIdEntity):
    """
    Картинки товаров
    """

    __tablename__ = "product_images"
    _schema_class = ProductImageCreate

    @property
    def entity_type(self) -> EntityType:
        return EntityType.PRODUCT_IMAGE

    @property
    def tablename(self) -> str:
        return self.__tablename__

    def __str__(self) -> str:
        return f"{self.image_type}: {self.name}"

    # Основные данные товара
    name: Mapped[str] = mapped_column(
        comment="Наименование файла"
    )  # name : Наименование файла

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.external_id"), comment="Товар"
    )  # productId : Ид товара
    product: Mapped["Product"] = relationship(
        "Product", foreign_keys=[product_id], back_populates="images"
    )

    detail_url: Mapped[str] = mapped_column(
        comment="Ссылка на картинку"
    )  # detailUrl : Ссылка на картинку

    image_type: Mapped[str] = mapped_column(
        comment="Тип картинки"
    )  # type : Тип картинки DETAIL_PICTURE, PREVIEW_PICTURE, MORE_PHOTO

    source: Mapped[SourcesProductEnum | None] = mapped_column(
        String(20), comment="Источник данных"
    )
    supplier_image_url: Mapped[str | None] = mapped_column(
        comment="Ссылка поставщика на картинку"
    )
