from __future__ import annotations

import base64
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.postgres import Base
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
    content: Mapped["ProductImageContent | None"] = relationship(
        "ProductImageContent",
        foreign_keys="ProductImageContent.product_image_id",
        back_populates="product_image",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="selectin",
    )

    @property
    def image_base64(self) -> str:
        """Возвращает base64 строку изображения"""
        if self.content:
            return self.content.to_base64()  # type: ignore[no-any-return]
        return ""

    @property
    def image_data_url(self) -> str:
        """Возвращает data URL изображения"""
        if self.content:
            return (  # type: ignore[no-any-return]
                self.content.to_base64_with_prefix()
            )
        return ""

    @property
    def has_content(self) -> bool:
        """Проверяет наличие содержимого"""
        return self.content is not None


class ProductImageContent(Base):  # type: ignore[misc]
    """
    Содержание картинок товаров
    """

    __tablename__ = "product_images_content"

    product_image_id: Mapped[UUID] = mapped_column(
        ForeignKey("product_images.id", ondelete="CASCADE"),
        unique=True,
        comment="Картинка товара",
    )
    product_image: Mapped["ProductImage"] = relationship(
        "ProductImage",
        foreign_keys=[product_image_id],
        back_populates="content",
        uselist=False,
    )
    image_data: Mapped[bytes] = mapped_column(
        LargeBinary, nullable=False, comment="Бинарные данные изображения"
    )
    mime_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="MIME тип изображения (image/jpeg, image/png и т.д.)",
    )
    file_size: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Размер файла в байтах"
    )
    file_hash: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="SHA256 хеш для дедупликации"
    )

    def __str__(self) -> str:
        return f"{self.product_image_id}: {str(self.image_data)[:10]}"

    def to_base64(self) -> str:
        """Преобразует бинарные данные в base64 строку"""
        if self.image_data:
            return base64.b64encode(self.image_data).decode("utf-8")
        return ""

    def to_base64_with_prefix(self) -> str:
        """Возвращает base64 с префиксом для data URL"""
        if self.image_data and self.mime_type:
            base64_str = base64.b64encode(self.image_data).decode("utf-8")
            return f"data:{self.mime_type};base64,{base64_str}"
        return ""
