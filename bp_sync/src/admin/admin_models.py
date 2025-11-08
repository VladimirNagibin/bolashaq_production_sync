# from typing import Any

# from fastapi import HTTPException, status
from sqladmin import Admin

# from sqlalchemy import select
# from sqlalchemy.orm import selectinload

# from models.communications import CommunicationChannel
# from models.company_models import Company
# from models.deal_documents import Contract
# from models.user_models import Manager

# from .base_admin import BaseAdmin
# from .mixins import AdminListAndDetailMixin


"""
class CompanyAdmin(
    BaseAdmin, AdminListAndDetailMixin, model=Company
):  # type: ignore[call-arg]
    name = "Компания"
    name_plural = "Компании"
    category = "Сущности"
    icon = "fa-solid fa-building"

    async def get_object_for_details(self, pk: Any) -> Any:
        stmt = (
            select(Company)
            .options(
                selectinload(Company.communications).selectinload(
                    CommunicationChannel.channel_type
                ),
                # Добавляем загрузку контрактов с связанными объектами
                selectinload(Company.contracts).selectinload(
                    Contract.shipping_company
                ),
                selectinload(Company.default_manager).selectinload(
                    Manager.user
                ),
                # Добавляем загрузку других связанных объектов, которые могут
                # понадобиться
                selectinload(Company.assigned_user),
                selectinload(Company.created_user),
                selectinload(Company.modify_user),
                selectinload(Company.last_activity_user),
                selectinload(Company.company_type),
                selectinload(Company.industry),
                selectinload(Company.employees),
                selectinload(Company.source),
                selectinload(Company.currency),
                selectinload(Company.main_activity),
                selectinload(Company.shipping_company),
                selectinload(Company.contact),
                selectinload(Company.lead),
                selectinload(Company.deal_failure_reason),
                selectinload(Company.deal_type),
                selectinload(Company.parent_company),
            )
            .where(Company.id == pk)
        )
        async with self.session_maker(expire_on_commit=False) as session:
            result = await session.execute(stmt)
            obj = result.scalar_one_or_none()
            if obj is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
            return obj

    column_list = [  # Поля в списке
        "external_id",
        "title",
        "revenue",
        "date_last_shipment",
        "main_activity",
        "city",
        "is_deleted_in_bitrix",
    ]

    @staticmethod
    def _format_revenue(model: Company, attribute: str) -> str:
        "Форматирование суммы"
        return AdminListAndDetailMixin.format_currency(model, attribute, "₽")

    # Форматирование значений
    column_formatters: dict[str, Any] = {
        "title": AdminListAndDetailMixin.format_title,
        "revenue": _format_revenue,
        "date_last_shipment": AdminListAndDetailMixin.format_date,
    }

    # Форматтеры для детальной страницы
    column_formatters_detail: dict[str, Any] = {
        "title": AdminListAndDetailMixin.format_title,
        "revenue": _format_revenue,
        "date_last_shipment": AdminListAndDetailMixin.format_date,
    }

    column_labels = {  # Надписи полей в списке
        "assigned_user": "Ответственный",
        "created_user": "Создатель",
        "modify_user": "Изменил",
        "last_activity_user": "Последняя активность",
        "date_create": "Дата создания",
        "date_modify": "Дата изменения",
        "last_activity_time": "Дата последней активности",
        "last_communication_time": "Дата последней коммуникации",
        "phones": "Телефоны",
        "emails": "Email",
        "webs": "Сайты",
        "ims": "IM",
        "links": "Ссылки",
        "address": "Адрес",
        "comments": "Комментарии",
        "opened": "Доступна всем",
        "external_id": "Внешний код",
        "title": "Название компании",
        "is_my_company": "Моя компания",
        "revenue": "Годовой оборот",
        "industry": "Сфера деятельности",
        "employees": "Численность сотрудников",
        "source": "Источник",
        "currency": "Валюта",
        "company_type": "Тип компании",
        "contact": "Контакт",
        "lead": "Лид",
        "main_activity": "Основная деятельность",
        "deal_failure_reason": "Причина провала",
        "deal_type": "Тип сделки",
        "shipping_company": "Фирма отгрузки",
        "shipping_company_id": "ID фирмы отгрузки",
        "banking_details": "Банковские реквизиты",
        "address_legal": "Юридический адрес",
        "address_company": "Адрес компании",
        "province_company": "Область/Край",
        "is_shipment_approved": "Разрешение на отгрузку",
        "date_last_shipment": "Дата последней отгрузки",
        "origin_version": "Версия данных",
        "parent_company": "Головная компания",
        "related_companies": "Дочерние компании",
        "deals": "Сделки",
        "leads": "Лиды",
        "contacts": "Контакты",
        "contracts": "Договоры",
        "invoices": "Счета",
        "delivery_notes": "Накладные",
        "position_head": "Должность руководителя",
        "basis_operates": "Основание деятельности",
        "position_head_genitive": "Должность руков. (род. падеж)",
        "basis_operates_genitive": "Основание деятельности (род. падеж)",
        "payment_delay_genitive": "Отсрочка (род. падеж)",
        "full_name_genitive": "ФИО (род. падеж)",
        "current_contract": "Текущий договор",
        "current_number_contract": "Номер договора",
        "city": "Город",
        "is_deleted_in_bitrix": "Удален в Битрикс",
        "default_manager": "Менеджер по умолчанию",
    }

    column_sortable_list = [
        "external_id",
        "title",
        "revenue",
        "date_last_shipment",
        "main_activity",
        "city",
        "is_deleted_in_bitrix",
    ]

    column_searchable_list = [
        "external_id",
        "title",
        "address_legal",
        "address_company",
        "city",
    ]

    form_columns = [  # Поля на форме редактирования
        "external_id",
        "title",
        "is_deleted_in_bitrix",
    ]

    column_details_list = [  # Поля на форме просмотра
        "external_id",
        "title",
        "revenue",
        "currency",
        "banking_details",
        "comments",  # from BusinessEntityCore
        # addsess
        "city",  # from BusinessEntityCore
        "address",  # from AddressMixin
        "address_legal",
        "address_company",
        "province_company",
        # Группа пользователей
        "assigned_user",  # from UserRelationsMixin
        "created_user",  # from UserRelationsMixin
        "modify_user",  # from UserRelationsMixin
        "last_activity_user",
        # Временные метки
        "date_last_shipment",
        "date_create",  # TimestampsMixin
        "date_modify",  # TimestampsMixin
        "last_activity_time",  # TimestampsMixin
        "last_communication_time",  # TimestampsMixin
        # Коммуникации
        "phones",  # CommunicationMixin
        "emails",  # CommunicationMixin
        "webs",  # CommunicationMixin
        "ims",  # CommunicationMixin
        "links",  # CommunicationMixin
        # Договора
        "contracts",
        "shipping_company",
        "shipping_company_id",
        "position_head",
        "position_head_genitive",
        "basis_operates",
        "basis_operates_genitive",
        "payment_delay_genitive",
        "full_name_genitive",
        "current_contract",
        "current_number_contract",
        # Типы и справочники
        "company_type",
        "industry",
        "employees",
        "source",
        "main_activity",
        "deal_type",
        "default_manager",
        "origin_version",
        # Статусы и флаги
        "is_shipment_approved",
        "is_my_company",
        "opened",  # from BusinessEntityCore
        # Связи
        "deals",
        "lead",
        "leads",
        "invoices",
        "delivery_notes",
        "contact",
        "contacts",
    ]
"""

"""
    # Настройки AJAX для связанных полей
    form_ajax_refs = {
        "currency": {
            "fields": ("name", "symbol"),
            "order_by": "name",
        },
        "company_type": {
            "fields": ("name",),
            "order_by": "name",
        },
        "industry": {
            "fields": ("name",),
            "order_by": "name",
        },
        "employees": {
            "fields": ("name",),
            "order_by": "name",
        },
        "source": {
            "fields": ("name",),
            "order_by": "name",
        },
        "main_activity": {
            "fields": ("name",),
            "order_by": "name",
        },
        "shipping_company": {
            "fields": ("name",),
            "order_by": "name",
        },
        "parent_company": {
            "fields": ("title",),
            "order_by": "title",
        },
        "contact": {
            "fields": ["name", "last_name"]
        },
    }
"""
# "currency": {
#    "fields": ["name", "external_id"],
#    "page_size": 10,
#    "placeholder": "Search currency...",
#    "minimum_input_length": 2
# },

"""
    async def scaffold_form(
        self, rules: list[str] | None = None
    ) -> type[Form]:
        form_class = await super().scaffold_form(rules)
        default_render_kw = {
            "class": "form-control",  # Основной класс стилей
            "autocomplete": "off",  # Стандартный атрибут в SQLAdmin
            "spellcheck": "false",  # Отключение проверки орфографии
        }
        form_class.code_mark = StringField(
            "QR криптохвост",
            validators=[Optional()],
            render_kw=default_render_kw,
        )
        form_class.code_mark_mid = StringField(
            "QR сред", validators=[Optional()], render_kw=default_render_kw
        )
        form_class.doc_out = StringField(
            "Исходящий документ",
            validators=[Optional()],
            render_kw=default_render_kw,
        )
        return form_class  # type: ignore
"""


# Регистрация всех моделей
def register_models(admin: Admin) -> None:
    ...
    # admin.add_view(CompanyAdmin)
