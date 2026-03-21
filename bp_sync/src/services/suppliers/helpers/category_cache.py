import json
from typing import Any

from redis.asyncio import Redis

from core.logger import logger
from schemas.enums import SourcesProductEnum

from ..repositories.supplier_product_repo import SupplierProductRepository

TTL = 3600


class CategoryCacheService:
    """
    Сервис для кэширования маппинга категорий.
    Хранит данные в формате JSON, преобразуя словарь с tuple-ключами
    в список словарей для сохранения.
    """

    def __init__(
        self,
        redis_client: Redis,
        supplier_product_repo: SupplierProductRepository,
        ttl: int = TTL,
    ):
        """
        Args:
            redis_client: Асинхронный клиент Redis
            ttl: Время жизни кэша в секундах (по умолчанию 1 час)
        """
        self.redis = redis_client
        self.supplier_product_repo = supplier_product_repo
        self.ttl = ttl

    def _serialize(self, data: dict[tuple[str, str | None], int]) -> str:
        """
        Преобразует словарь {(cat, sub): id} в JSON-строку.
        Пример: {("A", "B"): 1} -> [{"cat": "A", "sub": "B", "id": 1}]
        """
        payload: list[dict[str, Any]] = [
            {"c": key[0], "s": key[1], "id": value}
            for key, value in data.items()
        ]
        return json.dumps(payload)

    def _deserialize(self, raw_data: str) -> dict[tuple[str, str | None], int]:
        """
        Преобразует JSON-строку обратно в словарь.
        """
        if not raw_data:
            return {}
        payload = json.loads(raw_data)
        return {(item["c"], item["s"]): item["id"] for item in payload}

    async def get(
        self,
        source: SourcesProductEnum,
    ) -> dict[tuple[str, str | None], int]:
        """
        Получает данные из кэша. Если данных нет, вызывает загрузку из БД.

        Args:
            source: Источник данных (для формирования ключа)

        Returns:
            Словарь соответствий категорий
        """
        cache_key = f"category_map:{source.value}"

        # 1. Пытаемся получить из Redis
        cached_data = await self.redis.get(cache_key)
        if cached_data:
            logger.info(f"Category cache hit for {source.value}")
            return self._deserialize(cached_data)

        # 2. Если кэш пуст - грузим из БД
        logger.info(
            f"Category cache miss for {source.value}. Loading from DB..."
        )
        fresh_data = await self.supplier_product_repo.get_category_mapping(
            source
        )

        # 3. Сохраняем в Redis
        await self.set(source, fresh_data)

        return fresh_data

    async def set(
        self,
        source: SourcesProductEnum,
        data: dict[tuple[str, str | None], int],
    ) -> None:
        """Сохраняет данные в кэш."""
        cache_key = f"category_map:{source.value}"
        serialized = self._serialize(data)
        await self.redis.set(cache_key, serialized, ex=self.ttl)
        logger.debug(
            f"Category cache saved for {source.value} (TTL: {self.ttl}s)"
        )

    async def invalidate(self, source: SourcesProductEnum) -> None:
        """Удаляет кэш для конкретного источника."""
        cache_key = f"category_map:{source.value}"
        await self.redis.delete(cache_key)
        logger.info(f"Category cache invalidated for {source.value}")
