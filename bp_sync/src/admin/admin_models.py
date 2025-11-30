from sqladmin import Admin

from models.deal_models import AdditionalInfo
from models.deal_stage_models import DealStage
from models.department_models import Department
from models.timeline_comment_models import TimelineComment

from .base_admin import BaseAdmin
from .communication_admin_model import (
    CommunicationChannelAdmin,
    CommunicationChannelTypeAdmin,
)
from .company_admin_model import CompanyAdmin
from .contact_admin_model import ContactAdmin
from .deal_admin_model import DealAdmin
from .lead_admin_model import LeadAdmin
from .mixins import COLUMN_LABELS
from .product_admin_model import ProductAdmin, ProductAgreementSupervisorAdmin
from .user_admin_model import ManagerAdmin, UserAdmin


class DepartmentAdmin(BaseAdmin, model=Department):  # type: ignore[call-arg]
    name = "Отдел"
    name_plural = "Отделы"
    category = "Справочники"
    icon = "fa-solid fa-tags"

    column_list = [  # Поля в списке
        "external_id",
        "name",
        "parent_department",
    ]
    column_labels_local = {  # Надписи полей в списке
        "parent_id": "Ид родителя",
        "child_departments": "Дочернии отделы",
        "parent_department": "Родительский отдел",
        "users": "Пользователи",
    }
    column_labels = COLUMN_LABELS | column_labels_local
    column_default_sort = [("external_id", True)]  # Сортировка по умолчанию
    column_sortable_list = [  # Список полей по которым возможна сортировка
        "external_id",
        "name",
    ]
    column_searchable_list = [  # Список полей по которым возможен поиск
        "name",
        "external_id",
    ]
    form_columns = [  # Поля на форме
        "external_id",
        "name",
        # "parent_id",
        "is_deleted_in_bitrix",
    ]
    column_details_list = [
        "external_id",
        "name",
        "parent_id",
        "created_at",
        "updated_at",
        "is_deleted_in_bitrix",
        "child_departments",
        "users",
        "parent_department",
    ]  # Поля на форме просмотра


class DealStageAdmin(BaseAdmin, model=DealStage):  # type: ignore[call-arg]
    name = "Этап"
    name_plural = "Этапы"
    category = "Сделки"
    icon = "fa-solid fa-tags"

    column_list = [  # Поля в списке
        "external_id",
        "name",
        "sort_order",
    ]
    column_labels_local = {  # Надписи полей в списке
        "sort_order": "Номер",
        "deals": "Сделки",
    }
    column_labels = COLUMN_LABELS | column_labels_local
    column_default_sort = [("sort_order", False)]  # Сортировка по умолчанию
    column_sortable_list = [  # Список полей по которым возможна сортировка
        "external_id",
        "name",
        "sort_order",
    ]
    column_searchable_list = [  # Список полей по которым возможен поиск
        "name",
        "external_id",
        "is_deleted_in_bitrix",
    ]
    form_columns = [  # Поля на форме
        "external_id",
        "name",
        "sort_order",
        "is_deleted_in_bitrix",
    ]
    column_details_list = [  # Поля на форме
        "external_id",
        "name",
        "sort_order",
        "created_at",
        "updated_at",
        "is_deleted_in_bitrix",
        "deals",
    ]


class TimelineCommentAdmin(
    BaseAdmin, model=TimelineComment
):  # type: ignore[call-arg]
    name = "Комментарий в ленте"
    name_plural = "Комментарии в ленте"
    category = "Сделки"
    column_list = [  # Поля в списке
        "external_id",
        "entity_id",
        "entity_type",
        "author",
    ]
    column_labels_local = {  # Надписи полей в списке
        "entity_type": "Тип сущности",
        "entity_id": "ID сущности",
        "author": "Автор",
        "created": "Дата добавления",
        "comment_entity": "Текст комментария",
        "deal": "Сделка",
    }
    column_labels = COLUMN_LABELS | column_labels_local
    column_default_sort = [("entity_type", True), ("entity_id", True)]
    column_sortable_list = [  # Список полей по которым возможна сортировка
        "entity_type",
        "entity_id",
    ]
    column_searchable_list = [  # Список полей по которым возможен поиск
        "entity_type",
        "entity_id",
    ]
    form_columns = [  # Поля на форме
        "created",
        "entity_id",
        "entity_type",
        "comment_entity",
    ]
    column_details_list = [
        "created",
        "entity_id",
        "entity_type",
        "author",
        "deal",
        "comment_entity",
        "created_at",
        "updated_at",
        "is_deleted_in_bitrix",
    ]
    icon = "fa-solid fa-comment"


class AddInfoAdmin(BaseAdmin, model=AdditionalInfo):  # type: ignore[call-arg]
    name = "Доп информация сделки"
    name_plural = "Доп информации сделок"
    category = "Сделки"
    column_list = [  # Поля в списке
        "deal",
        "comment",
    ]
    column_labels_local = {  # Надписи полей в списке
        "deal_id": "ID сделки",
        "deal": "Сделка",
        "comment": "Дополнительная информация",
    }
    column_labels = COLUMN_LABELS | column_labels_local
    column_default_sort = [("deal_id", True)]  # Сортировка по умолчанию
    column_sortable_list = [  # Список полей по которым возможна сортировка
        "deal_id",
        "comment",
    ]
    column_searchable_list = [  # Список полей по которым возможен поиск
        "deal_id",
        "comment",
    ]

    form_columns = [  # Поля на форме
        "comment",
        "is_deleted_in_bitrix",
    ]
    column_details_list = [
        "deal",
        "comment",
        "created_at",
        "updated_at",
        "is_deleted_in_bitrix",
    ]
    icon = "fa-solid fa-note-sticky"


# Регистрация всех моделей
def register_models(admin: Admin) -> None:
    admin.add_view(DealAdmin)
    admin.add_view(CompanyAdmin)
    admin.add_view(DepartmentAdmin)
    admin.add_view(DealStageAdmin)
    admin.add_view(CommunicationChannelTypeAdmin)
    admin.add_view(CommunicationChannelAdmin)
    admin.add_view(TimelineCommentAdmin)
    admin.add_view(AddInfoAdmin)
    admin.add_view(ManagerAdmin)
    admin.add_view(UserAdmin)
    admin.add_view(ProductAgreementSupervisorAdmin)
    admin.add_view(ContactAdmin)
    admin.add_view(LeadAdmin)
    admin.add_view(ProductAdmin)
