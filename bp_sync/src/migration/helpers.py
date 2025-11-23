from typing import Any


def get_query_for_bulk_insert(
    table_name: str, columns: list[str], data: list[tuple[Any, ...]]
) -> str:
    """
    Универсальная функция для вставки данных
    :param table_name: Имя таблицы
    :param columns: Список колонок
    :param data: Итерируемый объект с кортежами данных
    """
    rows: list[str] = []
    for row in data:
        formatted_values: list[str] = []
        for value in row:
            if value is None:
                formatted_values.append("NULL")
            elif isinstance(value, (int, float)):
                formatted_values.append(str(value))
            else:
                # Экранирование одинарных кавычек и оборачивание строк
                escaped = str(value).replace("'", "''")
                formatted_values.append(f"'{escaped}'")
        rows.append(f"({', '.join(formatted_values)})")

    values_str = ", ".join(rows)
    columns_str = ", ".join([f'"{col}"' for col in columns])
    return f"INSERT INTO {table_name} ({columns_str}) VALUES {values_str}"
