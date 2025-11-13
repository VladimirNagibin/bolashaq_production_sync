import re
from typing import Any

from core.logger import logger
from schemas.email_schemas import ParsedRequest, TypeEvent


class RequestParserService:
    """Сервис для парсинга запросов с сайта"""

    def __init__(self) -> None:
        # Паттерны для извлечения данных
        self.patterns = {
            "product": re.compile(r"Товар:\s*(.+?)(?:\s*\(|$)", re.IGNORECASE),
            "product_id": re.compile(r"ID:\s*(\d+)", re.IGNORECASE),
            "name": re.compile(r"Имя:\s*([^\r\n]*)(?:\r\n|$)", re.IGNORECASE),
            "phone": re.compile(
                r"Телефон:\s*([\d\s\+\(\)\-]+)(?:\r\n|$)", re.IGNORECASE
            ),
            "comment": re.compile(
                r"Комментарий:\s*([^\r\n]*)(?:\r\n|$)", re.IGNORECASE
            ),
        }

        # Паттерн для комплексного парсинга
        self.comprehensive_pattern = re.compile(
            r"Товар:\s*(.+?)\s*\(ID:\s*(\d+)\s*\)\s*\r?\n"
            r"Имя:\s*([^\r\n]*)\s*\r?\n"
            r"Телефон:\s*([\d\s\+\(\)\-]+)\s*\r?\n"
            r"Комментарий:\s*([^\r\n]*)",
            re.IGNORECASE | re.DOTALL,
        )

    def parse_request(
        self, text: str, type_event: TypeEvent | None
    ) -> ParsedRequest | None:
        """
        Парсит строку запроса и возвращает структурированные данные

        Args:
            text: Строка для парсинга

        Returns:
            ParsedRequest: Объект с распарсенными данными
        """
        if not text:
            logger.warning("Пустой текст или неверный формат для парсинга")
            return None

        # Сохраняем исходный текст
        parse_data: dict[str, Any] = {"raw_text": text.strip()}

        try:
            # Пытаемся использовать комплексный паттерн для точного извлечения
            comprehensive_match = self.comprehensive_pattern.search(text)
            if comprehensive_match:
                parse_data["product"] = comprehensive_match.group(1).strip()
                parse_data["product_id"] = int(
                    comprehensive_match.group(2).strip()
                )
                parse_data["name"] = comprehensive_match.group(3).strip()
                parse_data["phone"] = comprehensive_match.group(4).strip()
                parse_data["comment"] = comprehensive_match.group(5).strip()
                logger.debug("Успешный парсинг комплексным паттерном")
                return ParsedRequest(**parse_data)

            # Если комплексный паттерн не сработал, парсим по отдельным полям
            return self._parse_individual_fields(text)

        except Exception as e:
            logger.error(f"Ошибка при парсинге текста: {e}")
            return None

    def _parse_individual_fields(self, text: str) -> ParsedRequest | None:
        """Парсинг отдельных полей"""
        try:
            parse_data: dict[str, Any] = {"raw_text": text.strip()}

            # Парсим товар
            product_match = self.patterns["product"].search(text)
            if product_match:
                parse_data["product"] = product_match.group(1).strip()

            # Парсим ID товара
            product_id_match = self.patterns["product_id"].search(text)
            if product_id_match:
                parse_data["product_id"] = int(
                    product_id_match.group(1).strip()
                )

            # Парсим имя
            name_match = self.patterns["name"].search(text)
            if name_match:
                name_value = name_match.group(1).strip()
                # Проверяем, что это действительно имя, а не следующее поле
                if name_value and not name_value.startswith("Телефон:"):
                    parse_data["name"] = name_value

            # Парсим телефон
            phone_match = self.patterns["phone"].search(text)
            if phone_match:
                phone_value = phone_match.group(1).strip()
                # Проверяем, что это действительно телефон
                if phone_value and not phone_value.startswith("Комментарий:"):
                    parse_data["phone"] = self._clean_phone(phone_value)

            # Парсим комментарий
            comment_match = self.patterns["comment"].search(text)
            if comment_match:
                parse_data["comment"] = comment_match.group(1).strip()

            return ParsedRequest(**parse_data)
        except Exception:
            return None

    def _fallback_parsing(self, text: str, result: ParsedRequest) -> None:
        """Резервный метод парсинга при ошибках"""
        try:
            lines = text.split("\r\n")
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Пытаемся определить тип строки по содержимому
                if "Товар:" in line:
                    parts = line.split("Товар:", 1)
                    if len(parts) > 1:
                        product_text = parts[1].strip()
                        # Извлекаем ID из скобок
                        id_match = self.patterns["product_id"].search(
                            product_text
                        )
                        if id_match:
                            result.product_id = int(id_match.group(1))
                            result.product = (
                                self.patterns["product_id"]
                                .sub("", product_text)
                                .strip(" ()")
                            )
                        else:
                            result.product = product_text

                elif "Имя:" in line:
                    parts = line.split("Имя:", 1)
                    if len(parts) > 1:
                        result.name = parts[1].strip()

                elif "Телефон:" in line:
                    parts = line.split("Телефон:", 1)
                    if len(parts) > 1:
                        result.phone = self._clean_phone(parts[1].strip())

                elif "Комментарий:" in line:
                    parts = line.split("Комментарий:", 1)
                    if len(parts) > 1:
                        result.comment = parts[1].strip()

        except Exception as e:
            logger.error(f"Ошибка в резервном парсинге: {e}")

    def _clean_phone(self, phone: str) -> str:
        """Очищает и форматирует номер телефона"""
        if not phone:
            return phone

        # Удаляем все нецифровые символы, кроме +
        cleaned = re.sub(r"[^\d+]", "", phone)

        # Если номер начинается с 7 или 8, оставляем 7
        if cleaned.startswith("8"):
            cleaned = "7" + cleaned[1:]
        elif cleaned.startswith("+7"):
            cleaned = "7" + cleaned[2:]

        return cleaned

    def validate_parsed_data(self, data: ParsedRequest) -> dict[str, bool]:
        """
        Валидирует распарсенные данные

        Returns:
            Dict с результатами валидации для каждого поля
        """
        validation = {
            "product": bool(data.product and data.product.strip()),
            "product_id": bool(data.product_id),
            "name": bool(data.name and data.name.strip()),
            "phone": bool(data.phone and len(data.phone) >= 10),
            "comment": bool(data.comment and data.comment.strip()),
        }

        return validation


# Фабрика для создания сервиса
def get_request_parser() -> RequestParserService:
    """Создает и возвращает экземпляр сервиса парсинга"""
    return RequestParserService()
