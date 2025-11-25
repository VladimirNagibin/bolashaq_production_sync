from models.communications import (
    CommunicationChannel,
    CommunicationChannelType,
)

from .base_admin import BaseAdmin
from .mixins import COLUMN_LABELS


class CommunicationChannelTypeAdmin(
    BaseAdmin, model=CommunicationChannelType
):  # type: ignore[call-arg]
    name = "Тип коммуникаций"
    name_plural = "Типы коммуникаций"
    category = "Коммуникации"
    icon = "fa-solid fa-tags"

    column_list = [  # Поля в списке
        "type_id",
        "value_type",
    ]
    column_labels_local = {  # Надписи полей в списке
        "type_id": "Тип коммуникации",
        "value_type": "Вид коммуникации",
        "description": "Описание типа канала",
        "channels": "Каналы",
    }
    column_labels = COLUMN_LABELS | column_labels_local
    column_default_sort = [("type_id", True), ("value_type", True)]
    column_sortable_list = [  # Список полей по которым возможна сортировка
        "type_id",
        "value_type",
    ]
    column_searchable_list = [  # Список полей по которым возможен поиск
        "type_id",
        "value_type",
    ]
    form_columns = [  # Поля на форме редактирования
        "type_id",
        "value_type",
        "is_deleted_in_bitrix",
    ]
    column_details_list = [
        "type_id",
        "value_type",
        "channels",
        "created_at",
        "updated_at",
        "is_deleted_in_bitrix",
    ]  # Поля на форме просмотра


class CommunicationChannelAdmin(
    BaseAdmin, model=CommunicationChannel
):  # type: ignore[call-arg]
    name = "Коммуникация"
    name_plural = "Коммуникации"
    category = "Коммуникации"
    icon = "fa-solid fa-tags"

    column_list = [  # Поля в списке
        "external_id",
        "entity_type",
        "entity_id",
        "channel_type",
        "value",
    ]
    column_labels_local = {  # Надписи полей в списке
        "entity_type": "Тип сущности",
        "entity_id": "ID сущности",
        "channel_type": "Тип канала",
        "value": "Значение коннекта",
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
        "value",
    ]
    form_columns = [  # Поля на форме редактирования
        "entity_type",
        "entity_id",
        "value",
        "is_deleted_in_bitrix",
    ]
    column_details_list = [
        "entity_type",
        "entity_id",
        "channel_type",
        "value",
        "created_at",
        "updated_at",
        "is_deleted_in_bitrix",
    ]  # Поля на форме просмотра
