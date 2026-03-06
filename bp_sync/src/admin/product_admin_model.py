from models.deal_models import ProductAgreementSupervisor
from models.product_models import Product, ProductEntity
from models.productsection_models import Productsection

from .base_admin import BaseAdmin
from .mixins import COLUMN_LABELS


class ProductAgreementSupervisorAdmin(
    BaseAdmin, model=ProductAgreementSupervisor
):  # type: ignore[call-arg]
    name = "Товар из согласованного КП"
    name_plural = "Товары из согласованного КП"
    category = "Товары"
    icon = "fa-solid fa-tags"

    column_list = [  # Поля в списке
        "deal",
        "product_id",
        "status_deal",
    ]
    column_labels_local = {  # Надписи полей в списке
        "deal": "Сделка",
        "product_id": "ИД товара",
        "status_deal": "Статус сделки",
    }
    column_labels = COLUMN_LABELS | column_labels_local
    column_default_sort = [("deal_id", True)]  # Сортировка по умолчанию
    column_sortable_list = [  # Список полей по которым возможна сортировка
        "deal_id",
        "product_id",
    ]
    column_searchable_list = [  # Список полей по которым возможен поиск
        "product_id",
    ]
    form_columns = [  # Поля на форме
        "product_id",
        "status_deal",
        "is_deleted_in_bitrix",
    ]
    column_details_list = [
        "deal",
        "product_id",
        "status_deal",
        "created_at",
        "updated_at",
        "is_deleted_in_bitrix",
    ]  # Поля на форме просмотра


class ProductAdmin(BaseAdmin, model=Product):  # type: ignore[call-arg]
    name = "Товар"
    name_plural = "Товары"
    category = "Товары"
    icon = "fa-solid fa-tags"

    column_list = [  # Поля в списке
        "name",
        "code",
        "currency_id",
    ]
    column_labels_local = {  # Надписи полей в списке
        "code": "Код",
        "currency_id": "Валюта",
        "status_deal": "Статус сделки",
    }
    column_labels = COLUMN_LABELS | column_labels_local
    column_default_sort = [("name", True)]  # Сортировка по умолчанию
    column_sortable_list = [  # Список полей по которым возможна сортировка
        "name",
        "code",
    ]
    column_searchable_list = [  # Список полей по которым возможен поиск
        "name",
    ]
    form_columns = [  # Поля на форме
        "name",
        "code",
        "is_deleted_in_bitrix",
    ]

    # column_details_list = [
    #     "deal",
    #     "product_id",
    #     "status_deal",
    #     "created_at",
    #     "updated_at",
    #     "is_deleted_in_bitrix",
    # ]  # Поля на форме просмотра


class ProductEntityAdmin(
    BaseAdmin, model=ProductEntity
):  # type: ignore[call-arg]
    name = "Товар в сущности"
    name_plural = "Товары в сущности"
    category = "Товары"
    icon = "fa-solid fa-tags"

    column_list = [  # Поля в списке
        "product_name",
        "price",
        "quantity",
        "owner_id",
        "owner_type",
    ]
    column_labels_local = {  # Надписи полей в списке
        "product_name": "Наименование",
        "price": "Цена",
        "quantity": "Количество",
        "owner_id": "Ид доеумента",
        "owner_type": "Тип сущности",
    }
    column_labels = COLUMN_LABELS | column_labels_local
    column_default_sort = [
        ("owner_type", True),
        ("owner_id", True),
        ("product_id", True),
    ]  # Сортировка по умолчанию
    column_sortable_list = [  # Список полей по которым возможна сортировка
        "product_name",
        "owner_id",
        "owner_type",
    ]
    column_searchable_list = [  # Список полей по которым возможен поиск
        "product_name",
        "owner_id",
    ]
    form_columns = [  # Поля на форме
        "product_name",
        "price",
        "quantity",
        "owner_id",
        "owner_type",
        "is_deleted_in_bitrix",
    ]


class ProductsectionAdmin(
    BaseAdmin, model=Productsection
):  # type: ignore[call-arg]
    name = "Раздел"
    name_plural = "Разделы"
    category = "Товары"
    icon = "fa-solid fa-tags"

    column_list = [  # Поля в списке
        "name",
        "section_id",
        "catalog_id",
        "code",
        "xml_id",
        "is_deleted_in_bitrix",
    ]
    column_labels_local = {  # Надписи полей в списке
        "name": "Наименование",
        "section_id": "Родительский раздел",
        "catalog_id": "Каталог",
        "code": "Символьный код",
        "xml_id": "СВнешний код",
    }
    column_labels = COLUMN_LABELS | column_labels_local
    column_default_sort = [("section_id", True)]  # Сортировка по умолчанию
    column_sortable_list = [  # Список полей по которым возможна сортировка
        "name",
        "section_id",
        "catalog_id",
        "code",
        "xml_id",
    ]
    column_searchable_list = [  # Список полей по которым возможен поиск
        "name",
        "section_id",
        "catalog_id",
        "code",
        "xml_id",
    ]
    form_columns = [  # Поля на форме
        "name",
        "section_id",
        "catalog_id",
        "code",
        "xml_id",
        "is_deleted_in_bitrix",
    ]
    column_details_list = [
        "name",
        "section_id",
        "parent_productsection",
        "catalog_id",
        "code",
        "xml_id",
        "child_productsections",
        "is_deleted_in_bitrix",
    ]  # Поля на форме просмотра
