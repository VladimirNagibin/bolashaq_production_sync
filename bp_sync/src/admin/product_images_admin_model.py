from models.product_images_models import ProductImage, ProductImageContent

from .base_admin import BaseAdmin
from .mixins import COLUMN_LABELS


class ProductImageAdmin(
    BaseAdmin, model=ProductImage
):  # type: ignore[call-arg]
    name = "Изображение товара"
    name_plural = "Изображения товаров"
    category = "Товары"
    icon = "fa-solid fa-tags"

    column_list = [  # Поля в списке
        "name",
        "product",
        "external_id",
        "image_type",
        "is_deleted_in_bitrix",
        "source",
    ]
    column_labels_local = {  # Надписи полей в списке
        "name": "Наименование файла",
        "product_id": "ИД товара",
        "product": "Товар",
        "detail_url": "Ссылка на картинку",
        "image_type": "Тип картинки",
        "source": "Источник данных",
        "supplier_image_url": "Ссылка поставщика на картинку",
    }
    column_labels = COLUMN_LABELS | column_labels_local
    column_default_sort = [("product_id", True)]  # Сортировка по умолчанию
    column_sortable_list = [  # Список полей по которым возможна сортировка
        "product_id",
    ]
    column_searchable_list = [  # Список полей по которым возможен поиск
        "product_id",
    ]
    form_columns = [  # Поля на форме
        "external_id",
        "product_id",
        "name",
        "detail_url",
        "image_type",
        "source",
        "supplier_image_url",
        "is_deleted_in_bitrix",
    ]
    column_details_list = [
        "external_id",
        "product_id",
        "product",
        "name",
        "detail_url",
        "image_type",
        "source",
        "supplier_image_url",
        "is_deleted_in_bitrix",
        "content",
    ]  # Поля на форме просмотра


class ProductImageContentAdmin(
    BaseAdmin, model=ProductImageContent
):  # type: ignore[call-arg]
    name = "Содержание изображения товара"
    name_plural = "Содержания изображений товаров"
    category = "Товары"
    icon = "fa-solid fa-tags"

    column_list = [  # Поля в списке
        "product_image",
        "mime_type",
        "file_size",
        "file_hash",
    ]
    column_labels_local = {  # Надписи полей в списке
        "product_image": "Картинка товара",
        "product_image_id": "ИД картинки товара",
        "mime_type": "MIME тип изображения (image/jpeg, image/png и т.д.)",
        "image_data": "Бинарные данные изображения",
        "file_size": "Размер файла в байтах",
        "file_hash": "SHA256 хеш для дедупликации",
    }
    column_labels = COLUMN_LABELS | column_labels_local
    column_default_sort = [
        ("product_image_id", True)
    ]  # Сортировка по умолчанию
    column_sortable_list = [  # Список полей по которым возможна сортировка
        "mime_type",
    ]
    column_searchable_list = [  # Список полей по которым возможен поиск
        "mime_type",
    ]
    form_columns = [  # Поля на форме
        "product_image_id",
        "mime_type",
        "file_size",
        "file_hash",
        "image_data",
    ]
    column_details_list = [
        "product_image",
        "product_image_id",
        "mime_type",
        "file_size",
        "file_hash",
        "image_data",
    ]  # Поля на форме просмотра
