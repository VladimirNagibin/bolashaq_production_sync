import asyncio
import random
from contextlib import asynccontextmanager
from typing import AsyncIterator

from redis.asyncio import Redis
from redis.exceptions import LockError

from core.logger import logger

from ..exceptions import LockAcquisitionError, MaxRetriesExceededError

TIMEOUT = 300
MAX_RETRIES = 4
BASE_DELAY = 1.0
MAX_DELAY = 30.0


class LockService:
    """
    Сервис для управления распределенными блокировками с повторными попытками
    """

    def __init__(self, redis: Redis):
        self.redis_client: Redis = redis
        self._lock_prefix = "deal_lock:"

    @asynccontextmanager
    async def acquire_deal_lock_with_retry(
        self,
        deal_id: int,
        timeout: int = TIMEOUT,
        max_retries: int = MAX_RETRIES,
        base_delay: float = BASE_DELAY,
        max_delay: float = MAX_DELAY,
        jitter: bool = True,
    ) -> AsyncIterator[None]:
        """
        Контекстный менеджер для получения блокировки сделки с повторными
        попытками

        Args:
            deal_id: ID сделки
            timeout: время жизни блокировки в секундах
            max_retries: максимальное количество попыток
            base_delay: базовая задержка между попытками (в секундах)
            max_delay: максимальная задержка между попытками
            jitter: добавлять случайность к задержкам
        """
        if not self.redis_client:
            raise RuntimeError("Redis client is not connected")

        lock_key = f"{self._lock_prefix}{deal_id}"

        for attempt in range(max_retries + 1):
            try:
                lock = self.redis_client.lock(
                    name=lock_key,
                    timeout=timeout,
                    blocking_timeout=0,  # Не блокируем, используем свои ретраи
                    thread_local=False,
                )

                acquired = await lock.acquire()

                if acquired:
                    logger.info(
                        f"Acquired lock for deal {deal_id} "
                        f"(attempt {attempt + 1}/{max_retries + 1})"
                    )
                    try:
                        yield
                        return  # Успешно выполнили
                    finally:
                        try:
                            await lock.release()
                            logger.info(f"Released lock for deal {deal_id}")
                        except Exception as e:
                            logger.warning(
                                f"Error releasing lock for deal {deal_id}: {e}"
                            )

                # Если не удалось получить блокировку
                if attempt < max_retries:
                    delay = self._calculate_retry_delay(
                        attempt, base_delay, max_delay, jitter
                    )

                    remaining_time = await self.get_remaining_lock_time(
                        deal_id
                    )
                    if remaining_time:
                        logger.warning(
                            f"Deal {deal_id} is locked, "
                            f"remaining: {remaining_time:.1f}s, "
                            f"retrying in {delay:.1f}s "
                            f"(attempt {attempt + 1}/{max_retries})"
                        )
                    else:
                        logger.warning(
                            f"Failed to acquire lock for deal {deal_id}, "
                            f"retrying in {delay:.1f}s "
                            f"(attempt {attempt + 1}/{max_retries})"
                        )

                    await asyncio.sleep(delay)
                else:
                    # Последняя попытка тоже не удалась
                    raise MaxRetriesExceededError(
                        f"Failed to acquire lock for deal {deal_id} "
                        f"after {max_retries + 1} attempts"
                    )

            except LockError as e:
                if attempt < max_retries:
                    delay = self._calculate_retry_delay(
                        attempt, base_delay, max_delay, jitter
                    )
                    logger.warning(
                        f"Lock error for deal {deal_id}: {e}, "
                        f"retrying in {delay:.1f}s "
                        f"(attempt {attempt + 1}/{max_retries})"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"Lock error for deal {deal_id} after all retries: {e}"
                    )
                    raise LockAcquisitionError(
                        f"Lock error for deal {deal_id}: {e}"
                    )

    def _calculate_retry_delay(
        self, attempt: int, base_delay: float, max_delay: float, jitter: bool
    ) -> float:
        """
        Вычисляет задержку для повторной попытки
        (exponential backoff with jitter)
        """
        # Exponential backoff
        delay = min(base_delay * (2**attempt), max_delay)

        # Добавляем jitter для предотвращения stampede effect
        if jitter:
            delay = random.uniform(0.5 * delay, 1.5 * delay)

        return float(delay)

    async def is_deal_locked(self, deal_id: int) -> bool:
        """Проверяет, заблокирована ли сделка в данный момент"""
        if not self.redis_client:
            return False

        lock_key = f"{self._lock_prefix}{deal_id}"
        try:
            return bool(await self.redis_client.exists(lock_key) == 1)
        except Exception as e:
            logger.error(f"Error checking lock status for deal {deal_id}: {e}")
            return False

    async def get_remaining_lock_time(self, deal_id: int) -> float | None:
        """Возвращает оставшееся время блокировки в секундах"""
        if not self.redis_client:
            return None

        lock_key = f"{self._lock_prefix}{deal_id}"
        try:
            ttl = await self.redis_client.ttl(lock_key)
            return ttl if ttl > 0 else None
        except Exception as e:
            logger.error(f"Error getting lock TTL for deal {deal_id}: {e}")
            return None
