from models.deal_models import ProductAgreementSupervisor
from models.product_models import Product

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
