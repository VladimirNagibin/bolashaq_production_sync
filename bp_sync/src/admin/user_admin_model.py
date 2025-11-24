from models.user_models import Manager, User

from .base_admin import BaseAdmin


class ManagerAdmin(BaseAdmin, model=Manager):  # type: ignore[call-arg]

    name = "Менеджер"
    name_plural = "Менеджеры"
    category = "Сотрудники"
    icon = "fa-solid fa-id-card"

    column_list = [  # Поля в списке
        "user_id",
        "user",
        "is_active",
        "disk_id",
        "chat_id",
    ]
    column_labels = {  # Надписи полей в списке
        "user_id": "Код пользователя",
        "user": "Пользователь",
        "is_active": "Менеджер активный",
        "disk_id": "Код диска",
        "chat_id": "ИД служебного чата",
    }
    column_default_sort = [("user_id", True)]  # Сортировка по умолчанию
    column_sortable_list = [  # Список полей по которым возможна сортировка
        "user_id",
        "is_active",
    ]
    column_searchable_list = [  # Список полей по которым возможен поиск
        "user_id",
        "is_active",
    ]
    form_columns = [
        "user_id",
        "is_active",
        "disk_id",
        "chat_id",
    ]

    column_details_list = [
        "user",
        "is_active",
        "disk_id",
        "chat_id",
        "created_at",
        "updated_at",
        "is_deleted_in_bitrix",
    ]


class UserAdmin(BaseAdmin, model=User):  # type: ignore[call-arg]
    name = "Пользователь"
    name_plural = "Пользователи"
    category = "Сотрудники"
    column_list = [  # Поля в списке
        "external_id",
        "full_name",
        "active",
        "department",
    ]
    column_labels = {  # Надписи полей в списке
        "external_id": "Код пользователя",
        "full_name": "Имя",
        "active": "Активный",
        "department": "Отдел",
    }
    column_default_sort = [("external_id", True)]  # Сортировка по умолчанию
    column_sortable_list = [  # Список полей по которым возможна сортировка
        "external_id",
        "full_name",
    ]
    column_searchable_list = [  # Список полей по которым возможен поиск
        "name",
        "full_name",
    ]
    form_columns = [
        "external_id",
        "active",
    ]
    column_details_list = [
        "external_id",
        "full_name",
        "department",
        "active",
    ]
    icon = "fa-solid fa-user"
