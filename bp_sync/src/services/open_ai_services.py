import json
from typing import Any

from openai import APIConnectionError, APIError, OpenAI, RateLimitError

from core.logger import logger
from core.settings import settings
from schemas.open_ai_schemas import (
    KitItem,
    ProductCharacteristic,
    ProductSection,
)

# Константы для настройки по умолчанию
DEFAULT_MODEL = "deepseek-chat"
DEFAULT_TEMPERATURE = 0.1
MAX_TOKENS = 2000


class OpenAIService:
    """
    Сервис для взаимодействия с OpenAI-совместимыми API (например, DeepSeek).
    Предназначен для парсинга и структурирования описаний товаров.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = MAX_TOKENS,
    ) -> None:
        """
        Инициализация сервиса OpenAI.

        Args:
            api_key: API ключ (если None, берется из настроек)
            base_url: Базовый URL API (если None, берется из настроек)
            model: Модель для использования
            temperature: Температура для генерации (0.0 - 1.0)
            max_tokens: Максимальное количество токенов в ответе
        """
        self.api_key = api_key or settings.OPEN_AI_API_KEY
        self.base_url = base_url or settings.OPEN_AI_BASE_URL
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        if not self.api_key:
            raise ValueError("API ключ не указан и не найден в настройках.")
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

        logger.info(
            "OpenAI service initialized",
            extra={
                "model": self.model,
                "base_url": self.base_url,
                "temperature": self.temperature,
            },
        )

    def parse_product_description(
        self,
        description_text: str,
        product_name: str,
        article: str | None = None,
        brand: str | None = None,
    ) -> ProductSection:
        """
        Парсит описание товара с помощью AI API.

        Args:
            description_text: Текст описания товара
            product_name: Наименование товара
            article: Артикул товара (опционально)
            brand: Производитель/бренд товара (опционально)

        Returns:
            ProductSection: Структурированная информация о товаре

        Raises:
            APIConnectionError: При проблемах с соединением
            RateLimitError: При превышении лимитов API
            APIError: При других ошибках API
            ValueError: При невалидных входных данных
        """
        if settings.OPEN_AI_MOCK_MODE:
            # Заглушка для данных
            return ProductSection(
                announcement="announcement",
                description="description",
                characteristics=[
                    ProductCharacteristic(
                        name="name", value="value", unit="unit"
                    ),
                    ProductCharacteristic(name="name_", value="value_"),
                ],
                kit=[
                    KitItem(
                        code="code",
                        name="name",
                        description="description",
                        specifications={"key": "value", "key_": "value_"},
                    ),
                    KitItem(
                        code="code_",
                        name="name_",
                        description="description_",
                        specifications={"key": "value", "key_": "value_"},
                    ),
                ],
            )
        # Валидация входных данных
        if not description_text or not description_text.strip():
            raise ValueError("Description text cannot be empty")
        if not product_name or not product_name.strip():
            raise ValueError("Product name cannot be empty")

        logger.info(
            "Starting product description parsing",
            extra={
                "product_name": product_name,
                "article": article,
                "brand": brand,
                "description_length": len(description_text),
            },
        )

        # Формируем промпт
        user_prompt = self._build_user_prompt(
            description_text=description_text,
            product_name=product_name,
            article=article,
            brand=brand,
        )

        try:
            # Вызов API
            logger.debug("Sending request to OpenAI API")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"},
            )

            # Получаем и парсим ответ
            response_content = response.choices[0].message.content

            if not response_content:
                raise ValueError("Empty response from API")

            logger.debug(
                "Received response from API",
                extra={
                    "response_length": len(response_content),
                    "finish_reason": response.choices[0].finish_reason,
                },
            )

            # Парсим ответ
            result = self._parse_api_response(response_content)

            logger.info(
                "Successfully parsed product description",
                extra={
                    "product_name": product_name,
                    "characteristics_count": len(result.characteristics),
                    "kit_items_count": len(result.kit),
                },
            )

            return result

        except APIConnectionError as e:
            logger.error(f"Connection error to OpenAI API: {e}", exc_info=True)
            raise

        except RateLimitError as e:
            logger.error(
                f"Rate limit exceeded for OpenAI API: {e}", exc_info=True
            )
            raise

        except APIError as e:
            logger.error(
                f"OpenAI API error: {e}",
                exc_info=True,
                extra={
                    "status_code": getattr(e, "status_code", None),
                    "response": getattr(e, "response", None),
                },
            )
            raise

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}", exc_info=True)
            raise

        except Exception as e:
            logger.error(
                f"Unexpected error during product parsing: {e}", exc_info=True
            )
            raise

    def _get_system_prompt(self) -> str:
        """Возвращает системный промпт с инструкциями для роли."""
        return (
            "Ты эксперт по парсингу технических описаний товаров. "
            "Твоя задача - разбить описание товара на структурированные "
            "части: "
            "1. Анонс/назначение "
            "(краткое описание для чего используется товар). "
            "2. Подробное описание (технические детали и особенности). "
            "3. Характеристики товара (технические параметры). "
            "4. Комплектация (что входит в набор, дополнительные элементы). "
            "Характеристики заполни отдельными строками. "
            # "Выдели числовые значения и единицы измерений. "
            # "Для комплектации извлеки артикулы (например S245-01)."
        )

    def _build_user_prompt(
        self,
        description_text: str,
        product_name: str,
        article: str | None,
        brand: str | None,
    ) -> str:
        """
        Формирует пользовательский промпт для API.

        Args:
            description_text: Текст описания товара
            product_name: Наименование товара
            article: Артикул товара
            brand: Производитель/бренд товара

        Returns:
            Сформированный промпт
        """

        # Формируем строку контекста
        context_parts = [f"наименованию: {product_name}"]
        if brand:
            context_parts.append(f"производителю: {brand}")
        if article:
            context_parts.append(f"артикулу: {article}")

        context_str = ", ".join(context_parts)

        return f"""
        Разбери следующее описание товара на структурированные части:

        {description_text}

        Верни ответ строго в формате JSON со следующей структурой:
        {{
            "announcement": "краткое назначение товара",
            "description": "подробное описание",
            "characteristics": [
                {{
                    "name": "Название характеристики",
                    "value": "значение",
                    "unit": "единица измерения при наличии иначе null"
                }}
            ],
            "kit": [
                {{
                    "code": "артикул при наличии иначе null",
                    "name": "название",
                    "description": "описание при наличии иначе null",
                    "specifications": {{}}
                }}
            ]
        }}

        Проверь правильность заполнения по {context_str}.
        """

    def _parse_api_response(self, response_content: str) -> ProductSection:
        """
        Парсит и валидирует ответ от API.

        Args:
            response_content: Сырой ответ от API

        Returns:
            ProductSection: Структурированная информация о товаре

        Raises:
            json.JSONDecodeError: Если ответ не является валидным JSON
            ValueError: Если структура ответа невалидна
        """
        try:
            result_json = json.loads(response_content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse API response as JSON: {e}")
            logger.debug(f"Raw response: {response_content[:500]}")
            raise

        # Валидация структуры
        self._validate_response_data(result_json)

        # Парсинг характеристик
        characteristics_data = result_json.get("characteristics", [])
        characteristics = [
            ProductCharacteristic(**char) for char in characteristics_data
        ]

        # Парсинг комплектации
        kit_data = result_json.get("kit", [])
        kit_items = [KitItem(**item) for item in kit_data]

        logger.debug(
            "Parsed API response",
            extra={
                "characteristics_count": len(characteristics),
                "kit_items_count": len(kit_items),
            },
        )

        return ProductSection(
            announcement=result_json.get("announcement", ""),
            description=result_json.get("description", ""),
            characteristics=characteristics,
            kit=kit_items,
        )

    def _validate_response_data(self, data: dict[str, Any]) -> None:
        """
        Валидирует структуру ответа от API.

        Args:
            data: Распарсенный JSON ответ

        Raises:
            ValueError: Если структура ответа невалидна
        """
        required_fields = [
            "announcement",
            "description",
            "characteristics",
            "kit",
        ]

        for field in required_fields:
            if field not in data:
                raise ValueError(
                    f"Missing required field in response: {field}"
                )

        if not isinstance(data["characteristics"], list):
            raise ValueError("Field 'characteristics' must be a list")

        if not isinstance(data["kit"], list):
            raise ValueError("Field 'kit' must be a list")
