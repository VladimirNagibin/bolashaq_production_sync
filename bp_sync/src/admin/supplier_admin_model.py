from models.supplier_models import (  # SupplierProduct,
    SourceColumnMapping,
    SourceImportConfig,
)

from .base_admin import BaseAdmin


class ImportConfigAdmin(
    BaseAdmin, model=SourceImportConfig
):  # type: ignore[call-arg]

    name = "Настройки импорта"
    name_plural = "Настройки импортов"
    category = "Поставщики"
    icon = "fa-solid fa-id-card"

    column_list = [  # Поля в списке
        "source",
        "config_name",
        "is_active",
        "file_format",
        "encoding",
        "delimiter",
        "header_row_index",
        "data_start_row",
        "source_key_field",
    ]
    column_labels = {  # Надписи полей в списке
        "source": "Источник",
        "config_name": "Имя настройки",
        "is_active": "Активна",
        "file_format": "Формат файла",
        "encoding": "Кодировка файла",
        "delimiter": "Разделитель для CSV",
        "header_row_index": "Номер строки с заголовками",
        "data_start_row": "Номер начала данных",
        "column_mappings": "Маппинг колонок",
        "source_key_field": (
            "Поле-идентификатор для сопоставления с источником"
        ),
    }
    column_default_sort = [("source", True)]  # Сортировка по умолчанию
    column_sortable_list = [  # Список полей по которым возможна сортировка
        "source",
        "is_active",
    ]
    column_searchable_list = [  # Список полей по которым возможен поиск
        "source",
        "is_active",
    ]
    form_columns = [
        "source",
        "config_name",
        "is_active",
        "file_format",
        "encoding",
        "delimiter",
        "header_row_index",
        "data_start_row",
        "column_mappings",
        "source_key_field",
    ]

    column_details_list = [
        "source",
        "config_name",
        "is_active",
        "file_format",
        "encoding",
        "delimiter",
        "header_row_index",
        "data_start_row",
        "column_mappings",
        "source_key_field",
    ]


class ColumnMappingAdmin(
    BaseAdmin, model=SourceColumnMapping
):  # type: ignore[call-arg]

    name = "Настройки колонок"
    name_plural = "Настройки колонок"
    category = "Поставщики"
    icon = "fa-solid fa-id-card"

    column_list = [  # Поля в списке
        "config",
        "target_field",
        "source_column_name",
        "source_column_index",
        "force_import",
        "data_type",
        "transformation_rule",
        "display_order",
    ]
    column_labels = {  # Надписи полей в списке
        "config_id": "ИД конфигурации",
        "config": "Конфигурация",
        "target_field": "Имя поля в базе данных",
        "source_column_name": "Имя столбца в загружаемом файле",
        "source_column_index": "Номер столбца в загружаемом файле",
        "force_import": "Перегружать в CRM без проверки",
        "data_type": "Тип данных",
        "transformation_rule": "Правило трансформации",
        "display_order": "Для UI и порядка обработки",
    }
    column_default_sort = [("config_id", True)]  # Сортировка по умолчанию
    column_sortable_list = [  # Список полей по которым возможна сортировка
        "config_id",
        "display_order",
        "source_column_index",
    ]
    column_searchable_list = [  # Список полей по которым возможен поиск
        "config_id",
        "force_import",
    ]
    form_columns = [
        "config_id",
        "config",
        "target_field",
        "source_column_name",
        "source_column_index",
        "force_import",
        "data_type",
        "transformation_rule",
        "display_order",
    ]

    column_details_list = [
        "config_id",
        "config",
        "target_field",
        "source_column_name",
        "source_column_index",
        "force_import",
        "data_type",
        "transformation_rule",
        "display_order",
    ]
