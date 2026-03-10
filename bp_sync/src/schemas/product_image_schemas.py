from typing import Any

from pydantic import Field

from schemas.enums import SourcesProductEnum

from .base_schemas import CommonFieldMixin


class BaseProductImage(CommonFieldMixin):
    """
    Общие поля создания и обновления с алиасами для соответствия
    SQLAlchemy модели
    """

    # FIELDS_BY_TYPE: ClassVar[dict[str, str]] = FIELDS_PRODUCT
    # FIELDS_BY_TYPE_ALT: ClassVar[dict[str, str]] = FIELDS_PRODUCT_ALT

    source: SourcesProductEnum | None = None
    supplier_image_url: str | None = None

    def model_dump_db(self, exclude_unset: bool = False) -> dict[str, Any]:
        return self.model_dump(  # type: ignore[no-any-return]
            exclude_unset=exclude_unset
        )


class ProductImageCreate(BaseProductImage):

    name: str = Field(alias="name")  # name : Наименование файла
    product_id: int = Field(alias="productId")  # productId : Ид товара
    detail_url: str = Field(
        alias="detailUrl"
    )  # detailUrl : Ссылка на картинку
    image_type: str = Field(
        alias="type",
    )  # type : Тип картинки DETAIL_PICTURE, PREVIEW_PICTURE, MORE_PHOTO


class ProductImageUpdate(BaseProductImage):

    name: str | None = Field(None, alias="name")  # name : Наименование файла
    product_id: int | None = Field(
        None,
        alias="productId",
    )  # productId : Ид товара
    detail_url: str | None = Field(
        None,
        alias="detailUrl",
    )  # detailUrl : Ссылка на картинку
    image_type: str | None = Field(
        None,
        alias="type",
    )  # type : Тип картинки DETAIL_PICTURE, PREVIEW_PICTURE, MORE_PHOTO
