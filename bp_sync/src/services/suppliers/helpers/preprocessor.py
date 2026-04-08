import hashlib
import json
from typing import Any

from redis.asyncio import Redis

from core.logger import logger
from schemas.enums import SourcesProductEnum
from schemas.open_ai_schemas import ProductSection
from schemas.supplier_schemas import SupplierProductDetail

from ...open_ai_services import OpenAIService
from ..json_encoder import CustomJSONEncoder, PreprocessedDataSerializer
from .category_cache import CategoryCacheService


class SupplierDataPreprocessor:
    """Сервис для предобработки данных (AI, категории, правила источников)."""

    # Константы для специальной обработки
    SOURCE_SPECIFIC_FIELDS = {
        SourcesProductEnum.LABSET: ["more_photo"],
    }

    # Маппинг полей AI на поля товара
    AI_FIELD_MAPPING = {
        "announcement": "preview_for_offer",
        "description": "description_for_offer",
        "characteristics": "characteristics",
        "kit": "complects",
    }

    # Время жизни кэша в секундах
    CACHE_TTL = 1800  # 30 минут

    def __init__(
        self,
        openai_service: OpenAIService,
        redis_client: Redis,
        category_cache: CategoryCacheService,
    ):
        self._openai_service = openai_service
        self._redis = redis_client
        self._category_cache = category_cache

    async def process(
        self,
        supplier_product: SupplierProductDetail,
        field_data: dict[str, dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        """
        Предобрабатывает данные товара: AI парсинг, определение категорий
        и т.д.

        Args:
            supplier_product: Товар поставщика
            field_data: Данные полей для обработки

        Returns:
            Dict[str, Dict[str, Any]]: Предобработанные данные
        """
        try:
            cached_result = await self._get_from_cache(
                supplier_product.id, field_data
            )
            if cached_result is not None:
                return cached_result

            # Выполняем обработку
            result = await self._run_processing_pipeline(
                supplier_product, field_data
            )

            # Сохраняем в кэш
            await self._save_to_cache(supplier_product.id, field_data, result)

            return result

        except Exception as e:
            logger.error(
                f"Preprocessing failed for product {supplier_product.id}: {e}",
                exc_info=True,
            )
            return {}

    async def _get_from_cache(
        self, product_id: Any, field_data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Получает предобработанные данные из кэша."""
        cache_key = self._generate_cache_key(product_id, field_data)

        try:
            cached = await self._redis.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for product {product_id}")
                return PreprocessedDataSerializer.deserialize_from_cache(
                    cached
                )
        except Exception as e:
            logger.warning(f"Failed to read from cache: {e}")

        return None

    async def _save_to_cache(
        self, product_id: Any, field_data: dict[str, Any], data: dict[str, Any]
    ) -> None:
        """Сохраняет предобработанные данные в кэш."""
        cache_key = self._generate_cache_key(product_id, field_data)

        try:
            serialized = PreprocessedDataSerializer.serialize_for_cache(data)
            await self._redis.set(cache_key, serialized, ex=self.CACHE_TTL)
            logger.debug(f"Saved to cache for product {product_id}")
        except Exception as e:
            logger.warning(f"Failed to save to cache: {e}")

    def _generate_cache_key(
        self, product_id: Any, field_data: dict[str, Any]
    ) -> str:
        """Генерирует ключ на основе хэша данных."""
        data_str = json.dumps(
            field_data,
            cls=CustomJSONEncoder,
            sort_keys=True,
            ensure_ascii=False,
        )
        data_hash = hashlib.md5(data_str.encode()).hexdigest()[:8]
        return f"preprocess_supplier_data:{product_id}:{data_hash}"

    async def _run_processing_pipeline(
        self,
        supplier_product: SupplierProductDetail,
        field_data: dict[str, dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        """Запускает все этапы обработки."""
        result: dict[str, dict[str, Any]] = {}

        # 1. AI обработка описания
        if description_data := field_data.get("description"):
            result.update(
                await self._process_description_with_ai(
                    description_data, supplier_product
                )
            )

        # 2. Определение категории
        if category_data := field_data.get("supplier_category"):
            result.update(
                await self._determine_category(
                    category_data,
                    field_data.get("supplier_subcategory"),
                    supplier_product,
                )
            )

        # 3. Специфичная логика источников
        result.update(
            self._apply_source_specific_processing(
                supplier_product.source,
                field_data,
                supplier_product,
            )
        )

        logger.info(
            f"Preprocessing completed for {supplier_product.name}. "
            f"Fields: {list(result.keys())}"
        )
        return result

    async def _process_description_with_ai(
        self,
        description_data: dict[str, Any],
        supplier_product: SupplierProductDetail,
    ) -> dict[str, dict[str, Any]]:
        """
        Обрабатывает описание товара через AI.

        Args:
            description_data: Данные описания
            supplier_product: Товар поставщика

        Returns:
            Dict[str, Dict[str, Any]]: Обработанные AI данные
        """
        result: dict[str, dict[str, Any]] = {}
        new_description = description_data.get("new_value")
        if not new_description or not isinstance(new_description, str):
            logger.debug(
                "No valid description for AI processing",
                extra={"supplier_product_id": str(supplier_product.id)},
            )
            return result

        try:
            ai_result: ProductSection = (
                await self._openai_service.parse_product_description(
                    description_text=new_description,
                    product_name=supplier_product.name,
                    article=supplier_product.article,
                    brand=supplier_product.brend,
                )
            )

            for ai_field, target_field in self.AI_FIELD_MAPPING.items():
                value = getattr(ai_result, ai_field, None)
                if value:
                    current = getattr(supplier_product, target_field, None)
                    result[target_field] = {
                        "old_value": current,
                        "new_value": value,
                    }
            logger.info(
                "AI description processing completed",
                extra={
                    "supplier_product_id": str(supplier_product.id),
                    "fields_processed": list(result.keys()),
                },
            )
        except Exception as e:
            logger.error(f"AI processing failed: {e}", exc_info=True)

        return result

    async def _determine_category(
        self,
        category_data: dict[str, Any],
        subcategory_data: dict[str, Any] | None,
        supplier_product: SupplierProductDetail,
    ) -> dict[str, dict[str, Any]]:
        """
        Определяет ID категории в CRM по названию категории поставщика.

        Args:
            category_data: Данные категории
            subcategory_data: Данные подкатегории
            supplier_product: Товар поставщика

        Returns:
            Dict[str, Dict[str, Any]]: Данные категории
        """
        result: dict[str, dict[str, Any]] = {
            "internal_section_id": {
                "old_value": supplier_product.internal_section_id,
                "new_value": None,
            }
        }
        try:
            category_cache = await self._get_category_cache(
                supplier_product.source
            )
            if cat_name := category_data.get("new_data"):
                sub_name = (
                    subcategory_data.get("new_data")
                    if subcategory_data
                    else None
                )
                if not sub_name:
                    sub_name = None
                category_id = category_cache.get((cat_name, sub_name))
                if category_id:
                    result["internal_section_id"] = {
                        "old_value": supplier_product.internal_section_id,
                        "new_value": category_id,
                    }
                    logger.debug(
                        "Category determined",
                        extra={
                            "supplier_product_id": str(supplier_product.id),
                            "category": cat_name,
                            "subcategory": sub_name if sub_name else "-",
                            "category_id": category_id,
                        },
                    )
        except Exception as e:
            logger.error(f"Category determination failed: {e}")
        return result

    def _apply_source_specific_processing(
        self,
        source: SourcesProductEnum,
        field_data: dict[str, dict[str, Any]],
        supplier_product: SupplierProductDetail,
    ) -> dict[str, dict[str, Any]]:
        """
        Применяет специфичную для источника обработку данных.

        Args:
            source: Источник данных
            field_data: Данные полей
            supplier_product: Товар поставщика

        Returns:
            Dict[str, Dict[str, Any]]: Обработанные данные
        """
        result: dict[str, dict[str, Any]] = {}
        specific_fields = self.SOURCE_SPECIFIC_FIELDS.get(source, [])

        for field_name in specific_fields:
            if field_value_data := field_data.get(field_name):
                value = field_value_data.get("new_value")
                processed = self._process_source_field(
                    source, field_name, value
                )
                if processed:
                    for key, val in processed.items():
                        result[key] = {"old_value": None, "new_value": val}
        return result

    def _process_source_field(
        self, source: SourcesProductEnum, field_name: str, value: Any
    ) -> dict[str, Any]:
        """
        Обрабатывает специфичное для источника поле.

        Args:
            source: Источник данных
            field_name: Название поля
            field_value: Значение поля

        Returns:
            Any: Обработанное значение
        """
        result: dict[str, Any] = {}
        if source == SourcesProductEnum.LABSET and field_name == "more_photo":
            if isinstance(value, str):
                urls = [url.strip() for url in value.split("|") if url.strip()]
                if urls:
                    result["detail_picture_process"] = urls[0]
                    if len(urls) > 1:
                        result["more_photo_process"] = urls[1:]
        return result

    async def _get_category_cache(
        self, source: SourcesProductEnum
    ) -> dict[tuple[str, str | None], int]:
        """
        Получает кэш соответствия категорий поставщика и CRM.

        Args:
            source: Источник данных

        Returns:
            Dict[Tuple[str, Optional[str]], int]:
            Словарь (категория, подкатегория) -> ID в CRM
        """
        logger.debug(
            "Getting category cache",
            extra={"source": source.value, "cache_size": 0},
        )

        return await self._category_cache.get(source)
