from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from models.communications import CommunicationChannel
from models.company_models import Company
from schemas.enums import CURRENCY

from .base_admin import BaseAdmin
from .mixins import AdminListAndDetailMixin


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
                # Добавляем загрузку других связанных объектов, которые могут
                # понадобиться
                selectinload(Company.assigned_user),
                selectinload(Company.created_user),
                selectinload(Company.modify_user),
                selectinload(Company.last_activity_user),
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
        "is_deleted_in_bitrix",
    ]

    @staticmethod
    def _format_revenue(model: Company, attribute: str) -> str:
        """Форматирование суммы"""
        return AdminListAndDetailMixin.format_currency(
            model, attribute, CURRENCY
        )

    # Форматирование значений
    column_formatters: dict[str, Any] = {
        # "title": AdminListAndDetailMixin.format_title,
        "revenue": _format_revenue,
        # "date_last_shipment": AdminListAndDetailMixin.format_date,
    }

    # Форматтеры для детальной страницы
    column_formatters_detail: dict[str, Any] = {
        "title": AdminListAndDetailMixin.format_title,
        "revenue": _format_revenue,
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
        "deal_type": "Тип сделки",
        "banking_details": "Банковские реквизиты",
        "address_legal": "Юридический адрес",
        "address_company": "Адрес компании",
        "province_company": "Область/Край",
        "origin_version": "Версия данных",
        "deals": "Сделки",
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
        "is_deleted_in_bitrix",
    ]

    column_searchable_list = [
        "external_id",
        "title",
        "address_legal",
        "address_company",
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
        # Типы и справочники
        "company_type",
        "industry",
        "employees",
        "source",
        "deal_type",
        "origin_version",
        # Статусы и флаги
        "is_my_company",
        "opened",  # from BusinessEntityCore
        # Связи
        "deals",
    ]
