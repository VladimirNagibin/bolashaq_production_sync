import asyncio
from typing import Any, AsyncGenerator

from redis.asyncio import ConnectionPool, Redis
from redis.exceptions import (
    AuthenticationError,
)
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import (
    RedisError,
)

from core.logger import logger
from core.settings import settings


class RedisManager:
    """
    Manager class for Redis connection with connection pooling and health
    checks.
    """

    def __init__(self) -> None:
        self._redis: Redis | None = None
        self._connection_pool: ConnectionPool | None = None
        self._is_initialized: bool = False
        self._is_shutting_down: bool = False

    async def initialize(self) -> None:
        """
        Initialize Redis connection with connection pooling.

        Args:
            redis_url: Redis connection URL. If None, uses settings.REDIS_URL
        """
        if self._is_initialized:
            logger.warning("Redis is already initialized")
            return

        try:
            # Prepare connection kwargs based on SSL setting
            connection_kwargs: dict[str, Any] = {
                "host": settings.REDIS_HOST,
                "port": settings.REDIS_PORT,
                "db": 0,
                "password": settings.REDIS_PASSWORD,
                "decode_responses": True,
                "encoding": "utf-8",
                "socket_connect_timeout": 5,
                "socket_timeout": 5,
                "retry_on_timeout": True,
            }

            # Add SSL parameters only if SSL is enabled
            if getattr(settings, "REDIS_SSL", False):
                connection_kwargs.update(
                    {
                        "ssl": True,
                        "ssl_cert_reqs": None,
                    }
                )
            # Create connection pool with individual parameters
            self._connection_pool = ConnectionPool(
                max_connections=20,
                health_check_interval=30,
                **connection_kwargs
            )

            # Create Redis client with connection pool
            self._redis = Redis(connection_pool=self._connection_pool)

            # Test connection
            if not await self._ping_connection():
                raise RedisConnectionError("Redis ping failed")
            self._is_initialized = True

            logger.info("Redis connection initialized successfully")

        except AuthenticationError:
            logger.error("Authentication error: invalid Redis password")
            await self._cleanup()
            raise
        except RedisConnectionError:
            logger.error("Failed to connect to Redis")
            await self._cleanup()
            raise
        except RedisError as e:
            logger.error("Failed to initialize Redis connection: %s", e)
            await self._cleanup()
            raise

    async def _ping_connection(self) -> bool:
        """Ping Redis connection."""
        if not self._redis or self._is_shutting_down:
            return False

        try:
            # Use cast to handle typing issues with ping method
            ping_result = await self._redis.ping()
            return bool(ping_result)
        except Exception as e:
            logger.debug("Redis ping failed: %s", e)
            return False

    async def close(self) -> None:
        """Close Redis connection and cleanup resources."""
        await self._cleanup()
        logger.info("Redis connection closed")

    async def _cleanup(self) -> None:
        """Cleanup Redis resources."""
        if self._is_shutting_down:
            return

        self._is_shutting_down = True

        try:
            if self._redis:
                # Close Redis client with timeout
                try:
                    # await self._redis.save()
                    await asyncio.wait_for(self._redis.aclose(), timeout=2.0)
                except asyncio.TimeoutError:
                    logger.warning("Redis close timeout, forcing cleanup")
                except RedisConnectionError:
                    logger.debug("Redis already disconnected during cleanup")
                except Exception as e:
                    logger.debug("Error during Redis close: %s", e)

            if self._connection_pool:
                # Disconnect connection pool with timeout
                try:
                    await asyncio.wait_for(
                        self._connection_pool.disconnect(), timeout=2.0
                    )
                except asyncio.TimeoutError:
                    logger.warning("Redis pool disconnect timeout")
                except Exception as e:
                    logger.debug("Error during pool disconnect: %s", e)
        except RedisError as e:
            logger.error("Error during Redis cleanup: %s", e)
        finally:
            self._redis = None
            self._connection_pool = None
            self._is_initialized = False
            logger.info("Redis connection closed")

    @property
    def client(self) -> Redis:
        """
        Get Redis client instance.

        Raises:
            RuntimeError: If Redis is not initialized
        """
        if (
            not self._is_initialized
            or not self._redis
            or self._is_shutting_down
        ):
            raise RuntimeError(
                "Redis is not initialized. Call initialize() first."
            )
        return self._redis

    async def health_check(self) -> bool:
        """Check if Redis connection is healthy."""
        try:
            return await self._ping_connection()
        except RedisError:
            return False

    async def get_info(self) -> dict[str, Any]:
        """Get Redis server information."""
        try:
            if (
                not self._is_initialized
                or not self._redis
                or self._is_shutting_down
            ):
                return {"error": "Redis not initialized"}

            info: dict[str, Any] = await self._redis.info()
            return {
                "version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "keyspace_hits": info.get("keyspace_hits"),
                "keyspace_misses": info.get("keyspace_misses"),
            }
        except RedisError as e:
            return {"error": str(e)}


# Global Redis manager instance
redis_manager = RedisManager()


async def init_redis() -> None:
    """
    Initialize Redis connection using RedisManager with connection pooling.

    This function replaces the original _init_redis function while maintaining
    the same error handling and logging behavior.
    """
    try:
        await redis_manager.initialize()
        logger.info("Успешное подключение к Redis.")
    except AuthenticationError:
        logger.error("Ошибка аутентификации: неверный пароль Redis")
        raise
    except RedisConnectionError:
        logger.error("Не удалось подключиться к Redis")
        raise
    except RedisError as e:
        logger.error("Ошибка при подключении к Redis: %s", e)
        raise


async def close_redis() -> None:
    """Close Redis connection."""
    await redis_manager.close()


async def get_redis() -> Redis:
    """
    Get Redis client instance.

    Returns:
        Redis: Redis client instance

    Raises:
        RuntimeError: If Redis is not initialized
    """
    return redis_manager.client


async def redis_health_check() -> bool:
    """Check Redis connection health."""
    return await redis_manager.health_check()


async def get_redis_info() -> dict[str, Any]:
    """Get Redis server information."""
    return await redis_manager.get_info()


# Context manager for Redis sessions
async def get_redis_session() -> AsyncGenerator[Redis, None]:
    """
    Get Redis session as async context manager.

    Usage:
        async with get_redis_session() as redis:
            await redis.get('key')
    """
    try:
        redis = await get_redis()
        yield redis
    except RedisError as e:
        logger.error("Redis operation failed: %s", e)
        raise


# Backward compatibility
async def get_redis_legacy() -> Redis | None:
    """
    Legacy function for backward compatibility.
    Returns Redis instance or None if not initialized.
    """
    try:
        return await get_redis()
    except RuntimeError:
        return None
