from sqladmin import ModelView

PAGE_SIZE = 50  # Количество записей на странице


# Базовые настройки модели
class BaseAdmin(ModelView):  # type: ignore[misc]
    page_size = PAGE_SIZE
    can_create = True
    can_edit = True
    can_delete = True
    can_export = True
    can_view_details = True
    icon = "fa-solid fa-table"
