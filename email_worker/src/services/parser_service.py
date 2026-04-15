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
            "bin_company": re.compile(
                r"БИН/компания:\s*([^\r\n]*)(?:\r\n|$)", re.IGNORECASE
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
            r"БИН/компания:\s*([^\r\n]*)\s*\r?\n"
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
            type_event: Тип события

        Returns:
            ParsedRequest: Объект с распарсенными данными
        """
        if not text:
            logger.warning("Пустой текст или неверный формат для парсинга")
            return None

        # Сохраняем исходный текст
        parse_data: dict[str, Any] = {"raw_text": text.strip()}

        try:
            if type_event == TypeEvent.REQUEST_PRICE:
                # Пытаемся использовать комплексный паттерн для точного
                # извлечения
                comprehensive_match = self.comprehensive_pattern.search(text)
                if comprehensive_match:
                    parse_data["product"] = comprehensive_match.group(
                        1
                    ).strip()
                    parse_data["product_id"] = int(
                        comprehensive_match.group(2).strip()
                    )
                    parse_data["name"] = comprehensive_match.group(3).strip()
                    parse_data["phone"] = comprehensive_match.group(4).strip()
                    bin_val = comprehensive_match.group(5).strip()
                    parse_data["bin_company"] = bin_val if bin_val else None
                    parse_data["comment"] = comprehensive_match.group(
                        6
                    ).strip()
                    logger.debug("Успешный парсинг комплексным паттерном")
                    return ParsedRequest(**parse_data)

                # Если комплексный паттерн не сработал, парсим по отдельным
                # полям
                return self._parse_individual_fields(text)
            elif type_event == TypeEvent.ORDER:
                parse_data = self.parse_order_content(text)
                logger.debug("Успешный парсинг")
                return ParsedRequest(**parse_data)
            elif type_event == TypeEvent.REQUEST_PRICE_LABSET:
                parse_data = self._parse_request_price_labset(text)
                logger.debug("Успешный парсинг")
                return ParsedRequest(**parse_data)
            else:
                logger.warning(
                    f"Не найдена обработка типа события: {type_event}"
                )
                return None
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
                if phone_value and not phone_value.startswith("БИН/компания:"):
                    parse_data["phone"] = self._clean_phone(phone_value)

            # Парсим БИН/компанию (Новое поле)
            bin_match = self.patterns["bin_company"].search(text)
            if bin_match:
                bin_value = bin_match.group(1).strip()
                # Проверяем, что это действительно БИН
                if bin_value and not bin_value.startswith("Комментарий:"):
                    # Очистка от лишних пробелов
                    parse_data["bin_company"] = " ".join(bin_value.split())

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

                elif "БИН/компания:" in line:
                    parts = line.split("БИН/компания:", 1)
                    if len(parts) > 1:
                        result.bin_company = parts[1].strip()

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
            "bin_company": bool(data.bin_company),
            "comment": bool(data.comment and data.comment.strip()),
        }

        return validation

    def parse_order_content(self, text: str) -> dict[str, Any]:
        """
        Парсит строку с запросом КП и извлекает данные клиента и товары.
        """

        result: dict[str, Any] = {
            "raw_text": text.strip(),
            "name": "",
            "phone": "",
            "email": "",
            "bin_company": "",
            "products": [],
        }

        # Нормализуем переносы строк
        text = text.replace("\r\n", "\n")

        # === Парсинг контактных данных ===

        # Имя
        name_match = re.search(r"Имя:\s*([^\n]+)", text)
        if name_match:
            result["name"] = name_match.group(1).strip()

        # Телефон
        phone_match = re.search(r"Телефон:\s*([^\n]+)", text)
        if phone_match:
            result["phone"] = phone_match.group(1).strip()

        # Email (может заканчиваться пробелами или переносом)
        email_match = re.search(r"Email:\s*([^\s\n]+)", text)
        if email_match:
            result["email"] = email_match.group(1).strip()

        # БИН / Компания (может быть "—" или пусто)
        bin_match = re.search(r"БИН / Компания:\s*\n\s*([^\n]*)", text)
        if bin_match:
            value = bin_match.group(1).strip()
            # Отсекаем заголовок следующего раздела, если он "прилип"
            # к значению
            if "Товары в запросе" in value:
                value = value.split("Товары в запросе")[0].strip()
            # Если осталось только "—", считаем поле пустым
            if value == "—":
                value = ""
            result["bin_company"] = value

        # === Парсинг товаров ===
        # Паттерн ищет блок: URL -> Артикул -> Название (ID) -> Цена
        product_pattern = re.compile(
            r"https://matest\.kz/catalog/[^\n]+\n\s*"  # URL товара
            r"Артикул:\s*(\S+)\s*\n?\s*"  # Артикул: XXX
            r"(.+?)\s*\(ID:(\d+)\)\s*\n?\s*"  # Название (ID:XXX)
            r"((?:[\d\s\xa0]+тенге|Цена по запросу))",  # Цена или "по запросу"
            re.IGNORECASE | re.DOTALL,
        )

        for match in product_pattern.finditer(text):
            article = match.group(1).strip()
            name = match.group(2).strip()
            product_id = int(match.group(3))
            price_str = match.group(4).strip()

            # Парсинг цены
            if "Цена по запросу" in price_str:
                price = 0
            else:
                # Удаляем всё, кроме цифр (пробелы, \xa0, "тенге")
                price_clean = re.sub(r"[^\d]", "", price_str)
                price = int(price_clean) if price_clean else 0

            result["products"].append(
                {
                    "product": name,
                    "article": article,
                    "product_id": product_id,
                    "price": price,
                }
            )

        return result

    def _parse_request_price_labset(self, text: str) -> dict[str, Any]:
        """
        Парсит строку запроса КПО и извлекает данные клиента и товары.
        """
        result: dict[str, Any] = {
            "raw_text": text.strip(),
            "name": "",
            "phone": "",
            "email": "",
            "bin_company": "",
            "products": [],
        }

        # === Парсинг контактных данных ===
        # Имя: всё от "Имя:" до следующего поля (Email или Телефон)
        name_match = re.search(
            r"Имя:\s*(.+?)(?=\s+(?:Email|Телефон):|$)", text
        )
        if name_match:
            result["name"] = name_match.group(1).strip()

        # Email
        email_match = re.search(r"Email:\s*([^\s]+)", text)
        if email_match:
            result["email"] = email_match.group(1).strip()

        # Телефон
        phone_match = re.search(r"Телефон:\s*(\d+)", text)
        if phone_match:
            result["phone"] = phone_match.group(1).strip()

        # === Парсинг товаров ===
        # Выделяем секцию товаров: от "следующие позиции:" до "Итого"
        products_section_match = re.search(
            r"В запросе КП указаны следующие позиции:\s*(.+?)\s*Итого",
            text,
            re.DOTALL | re.IGNORECASE,
        )

        if products_section_match:
            products_section = products_section_match.group(1)

            # 🔧 УДАЛЯЕМ заголовок таблицы, чтобы он не попал в первый товар
            products_section = re.sub(
                r"Продукты\s+Цена\s+Кол-во\.?\s*Промежуточный итог\s*",
                "",
                products_section,
                flags=re.IGNORECASE,
            )

            # 🔧 ПАТТЕРН ТОВАРА:
            # (.+?) — название (теперь может содержать скобки!)
            # \(ID:\s*(\d+)\s*\) — якорь ID, по которому отсекаем название
            product_pattern = re.compile(
                r"(.+?)\s*\(ID:\s*(\d+)\s*\)\s+"  # название и ID
                # цена + необязательная валюта
                r"(\d+(?:[\s\xa0]*[.,]?\d+)?)\s*[₸$€]?\s*"
                r"(\d+)\s+"  # количество
                # промежуточный итог + валюта
                r"(\d+(?:[\s\xa0]*[.,]?\d+)?)\s*[₸$€]?",
                re.IGNORECASE,
            )

            for match in product_pattern.finditer(products_section):
                name = match.group(1).strip()
                product_id = int(match.group(2))

                # Парсинг цены
                price_str = match.group(3).replace("\xa0", "").replace(" ", "")
                price_str = price_str.replace(",", ".")
                try:
                    price = float(price_str) if price_str else 0
                except ValueError:
                    price = 0

                # Количество
                try:
                    quantity = int(match.group(4))
                except ValueError:
                    quantity = 0

                result["products"].append(
                    {
                        "product": name,
                        "product_id": product_id,
                        "price": price,
                        "quantity": quantity,
                    }
                )
        return result


# Фабрика для создания сервиса
def get_request_parser() -> RequestParserService:
    """Создает и возвращает экземпляр сервиса парсинга"""
    return RequestParserService()
