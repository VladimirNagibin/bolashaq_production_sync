from contextlib import asynccontextmanager
from functools import lru_cache
from typing import Any, AsyncGenerator, Literal

from fastapi import Depends
from redis.asyncio import Redis
from redis.exceptions import RedisError

from core.logger import logger
from core.settings import settings
from db.redis import get_redis_session

from ..exceptions import (
    TokenEncryptionError,
    TokenStorageConnectionError,
)
from .token_cipher import TokenCipher, get_token_cipher

TokenType = Literal["refresh_token", "access_token"]
DEFAULT_REFRESH_TTL = 15_552_000  # 180 дней в секундах
DEFAULT_ACCESS_TTL = 1800  # 30 минут в секундах


class TokenStorage:
    """Сервис для безопасного хранения токенов в Redis с шифрованием."""

    def __init__(self, redis: Redis, token_cipher: TokenCipher):
        self.redis = redis
        self.token_cipher = token_cipher

    def _build_key(
        self, token_type: TokenType, user_id: str, provider: str
    ) -> str:
        """
        Строит ключ для хранения токена в Redis.

        Args:
            token_type: Тип токена
            user_id: ID пользователя
            provider: Провайдер OAuth

        Returns:
            Строка ключа
        """
        return f"token:{token_type}:user:{user_id}:provider:{provider}"

    def _get_default_ttl(self, token_type: TokenType) -> int:
        """
        Возвращает TTL по умолчанию для типа токена.

        Args:
            token_type: Тип токена

        Returns:
            TTL в секундах
        """
        ttl_map = {
            "refresh_token": DEFAULT_REFRESH_TTL,
            "access_token": DEFAULT_ACCESS_TTL,
        }
        return ttl_map.get(token_type, DEFAULT_REFRESH_TTL)

    async def save_token(
        self,
        token: str,
        token_type: TokenType,
        user_id: str = str(settings.SERVICE_USER),
        provider: str = settings.PROVIDER_B24,
        expire_seconds: int | None = None,
    ) -> str:
        """
        Сохраняет токен с шифрованием и TTL.

        Args:
            token: Токен для сохранения
            token_type: Тип токена
            user_id: ID пользователя
            provider: Провайдер OAuth
            expire_seconds: Время жизни в секундах

        Returns:
            Ключ под которым сохранен токен

        Raises:
            TokenStorageConnectionError: Ошибка соединения с Redis
            TokenEncryptionError: Ошибка шифрования токена
        """

        if expire_seconds is None:
            expire_seconds = self._get_default_ttl(token_type)

        key = self._build_key(token_type, user_id, provider)

        try:
            encrypted_token = await self.token_cipher.encrypt(token)
            await self.redis.setex(
                name=key, time=expire_seconds, value=encrypted_token
            )
            logger.debug(
                "Token saved successfully",
                extra={
                    "key": key,
                    "token_type": token_type,
                    "user_id": user_id,
                    "provider": provider,
                    "ttl_seconds": expire_seconds,
                },
            )

            return key

        except RedisError as e:
            logger.error(
                "Redis connection error while saving token",
                extra={"key": key, "error": str(e)},
            )
            raise TokenStorageConnectionError(
                f"Token storage unavailable: {e}"
            ) from e
        except Exception as e:
            logger.error(
                "Unexpected error while saving token",
                extra={"key": key, "error": str(e)},
            )
            raise TokenEncryptionError(
                f"Token encryption/save failed: {e}"
            ) from e

    async def get_token(
        self,
        token_type: TokenType,
        user_id: str = str(settings.SERVICE_USER),
        provider: str = settings.PROVIDER_B24,
    ) -> str | None:
        """
        Получает и расшифровывает токен из хранилища.

        Args:
            token_type: Тип токена
            user_id: ID пользователя
            provider: Провайдер OAuth

        Returns:
            Расшифрованный токен или None если не найден

        Raises:
            TokenStorageConnectionError: Ошибка соединения с Redis
        """
        key = self._build_key(token_type, user_id, provider)

        try:
            encrypted_token = await self.redis.get(key)

            if encrypted_token is None:
                logger.debug("Token not found in storage", extra={"key": key})
                return None

            decrypted_token = await self.token_cipher.decrypt(encrypted_token)

            logger.debug(
                "Token retrieved successfully",
                extra={"key": key, "token_type": token_type},
            )

            return decrypted_token

        except RedisError as e:
            logger.error(
                "Redis connection error while retrieving token",
                extra={"key": key, "error": str(e)},
            )
            raise TokenStorageConnectionError(
                f"Token retrieval failed: {e}"
            ) from e
        except Exception as e:
            logger.error(
                "Unexpected error while retrieving token",
                extra={"key": key, "error": str(e)},
            )
            # Не поднимаем исключение при ошибке дешифрования, возвращаем None
            return None

    async def delete_token(
        self,
        token_type: TokenType,
        user_id: str = str(settings.SERVICE_USER),
        provider: str = settings.PROVIDER_B24,
    ) -> bool:
        """
        Удаляет токен из хранилища.

        Args:
            token_type: Тип токена
            user_id: ID пользователя
            provider: Провайдер OAuth

        Returns:
            True если токен был удален, False если не найден

        Raises:
            TokenStorageConnectionError: Ошибка соединения с Redis
        """
        key = self._build_key(token_type, user_id, provider)

        try:
            deleted = await self.redis.delete(key)
            success = deleted > 0

            if success:
                logger.debug("Token deleted successfully", extra={"key": key})
            else:
                logger.debug(
                    "Token not found for deletion", extra={"key": key}
                )

            return bool(success)

        except RedisError as e:
            logger.error(
                "Redis connection error while deleting token",
                extra={"key": key, "error": str(e)},
            )
            raise TokenStorageConnectionError(
                f"Token deletion failed: {e}"
            ) from e
        except Exception as e:
            logger.error(
                "Unexpected error while delete token",
                extra={"key": key, "error": str(e)},
            )
            return False

    async def get_token_ttl(
        self,
        token_type: TokenType,
        user_id: str = str(settings.SERVICE_USER),
        provider: str = settings.PROVIDER_B24,
    ) -> int | None:
        """
        Получает оставшееся время жизни токена в секундах.

        Args:
            token_type: Тип токена
            user_id: ID пользователя
            provider: Провайдер OAuth

        Returns:
            TTL в секундах или None если токен не найден
        """
        key = self._build_key(token_type, user_id, provider)

        try:
            ttl = await self.redis.ttl(key)
            return ttl if ttl >= 0 else None
        except RedisError as e:
            logger.error(
                "Error getting token TTL", extra={"key": key, "error": str(e)}
            )
            return None

    async def exists(
        self,
        token_type: TokenType,
        user_id: str = str(settings.SERVICE_USER),
        provider: str = settings.PROVIDER_B24,
    ) -> bool:
        """
        Проверяет существование токена в хранилище.

        Args:
            token_type: Тип токена
            user_id: ID пользователя
            provider: Провайдер OAuth

        Returns:
            True если токен существует
        """
        key = self._build_key(token_type, user_id, provider)

        try:
            exists = await self.redis.exists(key)
            return bool(exists > 0)
        except RedisError as e:
            logger.error(
                "Error checking token existence",
                extra={"key": key, "error": str(e)},
            )
            return False

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[Any, Any]:
        """
        Контекстный менеджер для транзакционных операций с токенами.
        """
        async with self.redis.pipeline(transaction=True) as pipe:
            try:
                yield pipe
                await pipe.execute()
            except RedisError as e:
                logger.error(f"Token storage transaction failed: {e}")
                raise TokenStorageConnectionError(
                    f"Token transaction failed: {e}"
                ) from e


@lru_cache(maxsize=1)
def get_token_storage(
    redis: Redis = Depends(get_redis_session),
    token_cipher: TokenCipher = Depends(get_token_cipher),
) -> TokenStorage:
    """
    Фабрика для внедрения зависимостей TokenStorage.

    Returns:
        Экземпляр TokenStorage
    """
    return TokenStorage(redis, token_cipher)
