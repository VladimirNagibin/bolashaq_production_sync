from models.supplier_models import (
    SourceColumnMapping,
    SourceImportConfig,
    SupplierCharacteristic,
    SupplierComplect,
    SupplierProduct,
    SupplierProductChangeLog,
)

from .base_admin import BaseAdmin


class SupplierProductAdmin(
    BaseAdmin, model=SupplierProduct
):  # type: ignore[call-arg]

    name = "Товар поставщиков"
    name_plural = "Товары поставщиков"
    category = "Поставщики"
    icon = "fa-solid fa-id-card"

    column_list = [  # Поля в списке
        "external_id",
        "name",
        "source",
        "code",
        "active",
        "price",
        "original_name",
        "article",
        "supplier_category",
        "supplier_subcategory",
    ]
    column_labels = {  # Надписи полей в списке
        "external_id": "ID во внешней системе",
        "name": "Название товара",
        "code": "Символьный код",
        "active": "Активен",
        "sort": "Сортировка",
        "xml_id": "Внешний код",
        "price": "Цена",
        "currency_id": "Валюта",
        "description": "Описание",
        "description_type": "Тип описания",
        "link": "Ссылка",
        "original_name": "Оригинальное название",
        "standards": "Стандарты",
        "article": "Артикул",
        "supplier_category": "Категория в системе поставщика",
        "supplier_subcategory": "Подкатегория в системе поставщика",
        "detail_picture": "Детальная картинка (путь)",
        "detail_picture_description": "Описание для детальной картинки",
        "preview_picture": "Картинка для анонса (путь)",
        "preview_picture_description": "Описание для картинки анонса",
        "preview_text": "Описание для анонса",
        "preview_text_type": "Тип описания для анонса",
        "availability_status": "Статус наличия",
        "quantity": "Остаток",
        "source": "Источник данных",
        "is_validated": "Флаг обработки позиции",
        "should_export_to_crm": "Выгружать в CRM",
        "needs_review": "Требует ручной обработки",
        "internal_section_id": "Раздел в CRM",
        "product_id": "Идентификатор связанного товара в системе",
        "product": "Связь с основной номенклатурой",
        "preview_for_offer": "Анонс для предложенияя",
        "description_for_offer": "Описание для предложения",
        "characteristics": "Связь с характеристиками",
        "complects": "Связь с комплектующими",
        "more_photo": "Дополнительные картинки",
        "change_logs": "История изменений",
        "brend": "Бренд",
        "more_photo_process": "Обработанные доп картинки",
    }
    column_default_sort = [("source", True)]  # Сортировка по умолчанию
    column_sortable_list = [  # Список полей по которым возможна сортировка
        "external_id",
        "name",
    ]
    column_searchable_list = [  # Список полей по которым возможен поиск
        "external_id",
        "name",
    ]
    form_columns = [
        "external_id",
        "name",
        "code",
        "active",
        "sort",
        "xml_id",
        "price",
        "currency_id",
        "description",
        "description_type",
        "link",
        "original_name",
        "standards",
        "article",
        "supplier_category",
        "supplier_subcategory",
        "brend",
        "detail_picture",
        "detail_picture_description",
        "preview_picture",
        "preview_picture_description",
        "more_photo",
        "more_photo_process",
        "preview_text",
        "preview_text_type",
        "availability_status",
        "quantity",
        "source",
        "is_validated",
        "should_export_to_crm",
        "needs_review",
        "internal_section_id",
        "product_id",
        "product",
        "preview_for_offer",
        "description_for_offer",
        "characteristics",
        "complects",
    ]

    column_details_list = [
        "external_id",
        "name",
        "code",
        "active",
        "sort",
        "xml_id",
        "price",
        "currency_id",
        "description",
        "description_type",
        "link",
        "original_name",
        "standards",
        "article",
        "supplier_category",
        "supplier_subcategory",
        "brend",
        "detail_picture",
        "detail_picture_description",
        "preview_picture",
        "preview_picture_description",
        "more_photo",
        "more_photo_process",
        "preview_text",
        "preview_text_type",
        "availability_status",
        "quantity",
        "source",
        "is_validated",
        "should_export_to_crm",
        "needs_review",
        "internal_section_id",
        "product_id",
        "product",
        "preview_for_offer",
        "description_for_offer",
        "characteristics",
        "complects",
        "change_logs",
    ]


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
        "sync_with_crm",
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
        "sync_with_crm": "Синхронизировать с CRM",
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
        "sync_with_crm",
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
        "sync_with_crm",
        "data_type",
        "transformation_rule",
        "display_order",
    ]


class SupplierCharacteristicAdmin(
    BaseAdmin, model=SupplierCharacteristic
):  # type: ignore[call-arg]

    name = "Характеристики товара"
    name_plural = "Характеристики товаров"
    category = "Поставщики"
    icon = "fa-solid fa-id-card"

    column_list = [  # Поля в списке
        "name",
        "value",
        "unit",
        "supplier_product_id",
        "supplier_product",
    ]
    column_labels = {  # Надписи полей в списке
        "name": "Название характеристики",
        "value": "Значение характеристики",
        "unit": "Единица измерения",
        "supplier_product_id": "Ссылка на товар поставщика",
        "supplier_product": "Связь с товаром поставщика",
    }
    column_default_sort = [("name", True)]  # Сортировка по умолчанию
    column_sortable_list = [  # Список полей по которым возможна сортировка
        "name",
        "value",
        "supplier_product_id",
    ]
    column_searchable_list = [  # Список полей по которым возможен поиск
        "name",
        "value",
        "supplier_product_id",
    ]
    form_columns = [
        "name",
        "value",
        "unit",
        "supplier_product_id",
        "supplier_product",
    ]

    column_details_list = [
        "name",
        "value",
        "unit",
        "supplier_product_id",
        "supplier_product",
    ]


class SupplierProductChangeLogAdmin(
    BaseAdmin, model=SupplierProductChangeLog
):  # type: ignore[call-arg]

    name = "Лог изменения поля товара"
    name_plural = "Логи изменений полей товаров"
    category = "Поставщики"
    icon = "fa-solid fa-id-card"

    column_list = [  # Поля в списке
        "field_name",
        "is_processed",
        "source",
        "value_type",
        "created_at",
        "supplier_product_id",
        "supp_product",
    ]
    column_labels = {  # Надписи полей в списке
        "field_name": "Название измененного поля",
        "source": "Источник данных",
        "value_type": "Тип значения",
        "config_name": "Название конфигурации",
        "supplier_product_id": "Ссылка на товар поставщика",
        "supp_product": "Связь с товаром поставщика",
        "old_value": "Значение ДО изменения",
        "new_value": "Значение ПОСЛЕ изменения",
        "is_processed": "Обработано",
        "processed_at": "Дата обработки",
        "processed_by_user_id": "Обработано пользователем",
        "comment": "Комментарий",
        "loaded_value": "Загруженное значение",
        "crm_value_previous": "Предыдущее значение в CRM",
    }
    column_default_sort = [
        ("supplier_product_id", True)
    ]  # Сортировка по умолчанию
    column_sortable_list = [  # Список полей по которым возможна сортировка
        "supplier_product_id",
        "field_name",
        "source",
    ]
    column_searchable_list = [  # Список полей по которым возможен поиск
        "old_value",
        "new_value",
        "supplier_product_id",
    ]
    # form_columns = [
    #     "name",
    #     "code",
    #     "description",
    #     "specifications",
    #     "supplier_product_id",
    #     "supplier_product",
    # ]

    # column_details_list = [
    #     "name",
    #     "code",
    #     "description",
    #     "specifications",
    #     "supplier_product_id",
    #     "supplier_product",
    # ]


class SupplierComplectAdmin(
    BaseAdmin, model=SupplierComplect
):  # type: ignore[call-arg]

    name = "Комплектация товара"
    name_plural = "Комплектация товаров"
    category = "Поставщики"
    icon = "fa-solid fa-id-card"

    column_list = [  # Поля в списке
        "name",
        "code",
        "description",
        "specifications",
        "supplier_product_id",
        "supplier_product",
    ]
    column_labels = {  # Надписи полей в списке
        "name": "Название комплектующего",
        "code": "Символьный код",
        "description": "Описание",
        "specifications": "Спецификации",
        "supplier_product_id": "Ссылка на товар поставщика",
        "supplier_product": "Связь с товаром поставщика",
    }
    column_default_sort = [("name", True)]  # Сортировка по умолчанию
    column_sortable_list = [  # Список полей по которым возможна сортировка
        "name",
        "code",
        "supplier_product_id",
    ]
    column_searchable_list = [  # Список полей по которым возможен поиск
        "name",
        "code",
        "supplier_product_id",
    ]
    form_columns = [
        "name",
        "code",
        "description",
        "specifications",
        "supplier_product_id",
        "supplier_product",
    ]

    column_details_list = [
        "name",
        "code",
        "description",
        "specifications",
        "supplier_product_id",
        "supplier_product",
    ]
