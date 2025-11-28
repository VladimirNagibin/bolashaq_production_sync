from typing import Any

from models.deal_models import Deal
from schemas.enums import (
    DealStatusEnum,
    StageSemanticEnum,
)

from .base_admin import BaseAdmin
from .mixins import AdminListAndDetailMixin


class DealAdmin(
    BaseAdmin, AdminListAndDetailMixin, model=Deal
):  # type: ignore[call-arg]
    name = "Сделка"
    name_plural = "Сделки"
    category = "Сделки"
    icon = "fa-solid fa-handshake"

    column_list = [  # Поля в списке
        "external_id",
        "title",
        "opportunity",
        "company",
        "stage",
        "type",
        "source",
        "status_deal",
        "is_deleted_in_bitrix",
        "category",
        "stage_semantic_id",
        "moved_date",
    ]

    @staticmethod
    def _format_stage_semantic(model: Deal, attribute: str) -> str:
        """Форматирование семантики стадии"""
        return AdminListAndDetailMixin.format_enum_display(
            StageSemanticEnum, model, attribute
        )

    @staticmethod
    def _format_status(model: Deal, attribute: str) -> str:
        """Форматирование статуса сделки"""
        return AdminListAndDetailMixin.format_enum_display(
            DealStatusEnum, model, attribute
        )

    # Форматирование значений
    column_formatters: dict[str, Any] = {
        "title": AdminListAndDetailMixin.format_title,
        "opportunity": AdminListAndDetailMixin.format_currency,
        "stage_semantic_id": _format_stage_semantic,
    }

    # Форматтеры для детальной страницы (показываем display_name)
    column_formatters_detail: dict[str, Any] = {
        "stage_semantic_id": _format_stage_semantic,
        "status_deal": _format_status,
    }

    column_labels = {  # Надписи полей в списке # type: ignore
        "external_id": "Внешний код",
        "title": "Название",
        "opportunity": "Сумма",
        "category_id": "Воронка",
        "stage": "Стадия",
        "type_id": "Тип",
        "creation_source": "Источник сводно",
        "source_id": "Источник",
        "status_deal": "Статус сделки",
        "is_deleted_in_bitrix": "Удалён в Б24",
        "assigned_user": "Ответственный",
        "created_user": "Создатель",
        "modify_user": "Изменил",
        "last_activity_user": "Последняя активность",
        "date_create": "Дата создания",
        "date_modify": "Дата изменения",
        "last_activity_time": "Дата последней активности",
        "last_communication_time": "Дата последней коммуникации",
        "additional_info": "Дополнительная информация",
        "stage_semantic_id": "Семантика стадии",
        "begindate": "Дата начала сделки",
        "closedate": "Дата завершения сделки",
        "moved_time": "Время перемещения сделки",
        "timeline_comments": "Комментарии из ленты",
        "company": "Компания",
        "contact": "Контакт",
        "lead": "Лид",
        "add_info": "Дополнительная информация",
        "moved_date": "Дата перемещения сделки",
    }
    column_sortable_list = [  # Список полей по которым возможна сортировка
        "external_id",
        "title",
        "opportunity",
        "status_deal",
        "is_deleted_in_bitrix",
        "moved_date",
    ]
    column_searchable_list = [  # Список полей по которым возможен поиск
        "external_id",
        "title",
    ]
    form_columns = [  # Поля на форме редактирования
        "external_id",
        "title",
        "status_deal",
        "is_deleted_in_bitrix",
        "moved_date",
    ]
    column_details_list = [  # Поля на форме просмотра
        "external_id",
        "title",
        "opportunity",
        "category_id",
        "stage",
        "type_id",
        "source_id",
        "status_deal",
        "is_deleted_in_bitrix",
        "assigned_user",
        "created_user",
        "modify_user",
        "last_activity_user",
        "begindate",
        "closedate",
        "moved_date",
        "moved_time",
        "date_create",
        "date_modify",
        "last_activity_time",
        "last_communication_time",
        "additional_info",
        "stage_semantic_id",
        "timeline_comments",
        "company",
        "contact",
        "lead",
    ]

    form_args = {
        "stage_semantic_id": {
            "choices": [
                (member.value, member.get_display_name(member.value))
                for member in StageSemanticEnum
            ]
        }
    }
