import asyncio
import hashlib
import json
from typing import Any

from openai import APIConnectionError, APIError, OpenAI, RateLimitError
from redis.asyncio import Redis

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
# Кэшируем на 14 дней (604800 секунд) по умолчанию
DEFAULT_CACHE_TTL = 60 * 60 * 24 * 14


class OpenAIService:
    """
    Сервис для взаимодействия с OpenAI-совместимыми API (например, DeepSeek).
    Предназначен для парсинга и структурирования описаний товаров.
    """

    def __init__(
        self,
        redis_client: Redis,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = MAX_TOKENS,
        cache_ttl: int = DEFAULT_CACHE_TTL,
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
        self.redis_client = redis_client
        self.api_key = api_key or settings.OPEN_AI_API_KEY
        self.base_url = base_url or settings.OPEN_AI_BASE_URL
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.cache_ttl = cache_ttl

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

    def _generate_cache_key(
        self,
        product_name: str,
        description_text: str,
        article: str | None = None,
        brand: str | None = None,
    ) -> str:
        """
        Генерирует уникальный ключ кэша на основе хеша входных данных.
        """
        # Собираем все данные, влияющие на результат, в одну строку
        # Используем разделители, чтобы избежать коллизий
        # (например, "prod1desc" != "prod1desc")
        payload = (
            f"{product_name}|{article or ''}|{brand or ''}|"
            f"{description_text}"
        )

        # Создаем хеш SHA256
        return (
            "openai:parse:"
            f"{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"
        )

    async def parse_product_description(
        self,
        description_text: str,
        product_name: str,
        article: str | None = None,
        brand: str | None = None,
    ) -> ProductSection:
        """
        Парсит описание товара с помощью AI API.
        Использует кэш, если результат уже был вычислен.

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
        cache_key = self._generate_cache_key(
            product_name, description_text, article, brand
        )

        # 1. Пытаемся получить данные из кэша
        try:
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                logger.info(
                    "Cache hit for product parsing",
                    extra={
                        "product_name": product_name,
                        "key": cache_key[:16],
                    },
                )
                # Десериализуем JSON обратно в Pydantic модель
                return ProductSection.model_validate_json(cached_data)
        except Exception as e:
            logger.warning(
                (
                    f"Failed to retrieve from cache: {e}. "
                    "Proceeding with API call."
                ),
                exc_info=True,
            )

        # 2. Если кэш не сработал , вызываем API
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            self._call_openai_api,
            description_text,
            product_name,
            article,
            brand,
        )

        # 3. Сохраняем результат в кэш
        if result:
            try:
                # Сериализуем Pydantic модель в JSON
                json_data = result.model_dump_json()
                await self.redis_client.setex(
                    cache_key, self.cache_ttl, json_data
                )
                logger.debug(
                    "Saved to cache",
                    extra={
                        "product_name": product_name,
                        "ttl": self.cache_ttl,
                    },
                )
            except Exception as e:
                logger.warning(f"Failed to save to cache: {e}", exc_info=True)

        return result

    def _call_openai_api(
        self,
        description_text: str,
        product_name: str,
        article: str | None,
        brand: str | None,
    ) -> ProductSection:
        """
        Внутренний метод, содержащий логику вызова API.
        """
        # Mock режим (если нужно)
        if settings.OPEN_AI_MOCK_MODE:
            return ProductSection(
                announcement="announcement",
                description="description",
                characteristics=[
                    ProductCharacteristic(
                        name="name", value="value", unit="unit"
                    )
                ],
                kit=[
                    KitItem(
                        code="code",
                        name="name",
                        description="description",
                        specifications={"key": "value", "key_": "value_"},
                    )
                ],
            )

        # Валидация
        if not description_text or not description_text.strip():
            raise ValueError("Description text cannot be empty")
        if not product_name or not product_name.strip():
            raise ValueError("Product name cannot be empty")

        logger.info(
            "Starting OpenAI API call...",
            extra={
                "product_name": product_name,
                "article": article,
                "brand": brand,
                "description_length": len(description_text),
            },
        )

        try:
            user_prompt = self._build_user_prompt(
                description_text, product_name, article, brand
            )

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

            # Парсинг
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

        except (APIConnectionError, RateLimitError, APIError) as e:
            logger.error(f"OpenAI API error: {e}", exc_info=True)
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}", exc_info=True)
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
