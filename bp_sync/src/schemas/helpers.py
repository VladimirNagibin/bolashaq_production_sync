# import re
from typing import Any


def parse_numeric_string(value: Any) -> float | None:
    """
    Универсальная функция для парсинга числовых строк с разными форматами
    """
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        # Нормализуем пробелы и нестандартные символы
        normalized = value.strip()

        # Заменяем неразрывные пробелы и другие специальные пробелы
        normalized = normalized.replace("\xa0", " ")  # неразрывный пробел
        normalized = normalized.replace("\u2009", " ")  # тонкий пробел
        normalized = normalized.replace("\u202f", " ")  # узкий неразрывный

        # Паттерны для разных форматов чисел
        # patterns = [
        # Формат с пробелами как разделителями тысяч: "27 300" -> 27300
        #    r"^(\d+)[\s]+(\d+)$",
        # Формат с пробелами и десятичной частью: "27 300,50" -> 27300.50
        #    r"^(\d+)[\s]+(\d+)[,.](\d+)$",
        # Просто число с запятой как десятичным разделителем
        #    r"^(\d+),(\d+)$",
        # Число с точкой как десятичным разделителем
        #    r"^(\d+)\.(\d+)$",
        # ]

        """
        # Пробуем разные паттерны
        for pattern in patterns:
            match = re.match(pattern, normalized)
            if match:
                groups = match.groups()
                if len(groups) == 2 and pattern == patterns[0]:
                    # "27 300" -> 27300
                    return float(groups[0] + groups[1])
                elif len(groups) == 3 and pattern == patterns[1]:
                    # "27 300,50" -> 27300.50
                    return float(groups[0] + groups[1] + '.' + groups[2])
                elif (
                    len(groups) == 2 and pattern in (patterns[2], patterns[3])
                ):
                    # "27,50" -> 27.50 или "27.50" -> 27.50
                    return float(groups[0] + '.' + groups[1])
        """
        # Если паттерны не сработали, просто очищаем от всех нецифровых
        # символов кроме . и -
        # cleaned = re.sub(r'[^\d\.\-]', '', normalized)

        cleaned = normalized
        if cleaned:
            try:
                return float(cleaned)
            except (ValueError, TypeError):
                pass

    return None
