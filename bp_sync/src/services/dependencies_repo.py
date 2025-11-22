from contextvars import ContextVar
from typing import (  # Callable,; Coroutine,; TypeVar,; cast,
    Any,
    AsyncGenerator,
    Type,
)

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import logger
from db.postgres import get_session_generator

# Контекстная переменная для хранения текущей сессии базы данных
_session_ctx: ContextVar[AsyncSession | None] = ContextVar(
    "_session_ctx", default=None
)
# Контекстная переменная для хранения созданных сервисов с проверкой на повтор
_services_cache_ctx: ContextVar[dict[str, Any]] = ContextVar(
    "_services_cache", default={}
)
# Контекстная переменная для хранения проверенных объектов на существование в
# рамках запроса
_exists_cache_ctx: ContextVar[
    dict[tuple[Type[Any], tuple[tuple[str, Any], ...]], bool]
] = ContextVar("_exists_cache", default={})
# Контекстная переменная для хранения проверенных объектов на существование
# либо созданных в рамках запроса
_updated_cache_ctx: ContextVar[set[tuple[Type[Any], int | str]]] = ContextVar(
    "_updated_cache", default=set()
)
# Глобальный кэш для отслеживания создания сущностей в текущем контексте
_creation_cache_ctx: ContextVar[dict[tuple[Type[Any], int | str], bool]] = (
    ContextVar("creation_cache", default={})
)
# Кэш для отслеживания сущностей, требующих обновления
_update_needed_cache_ctx: ContextVar[set[tuple[Type[Any], int | str]]] = (
    ContextVar("update_needed_cache", default=set())
)


# Dependency для установки контекста запроса
async def request_context(
    session: AsyncSession = Depends(get_session_generator),
) -> AsyncGenerator[None, None]:
    """Устанавливает контекст для текущего запроса"""
    # Устанавливаем сессию и кеш сервисов
    session_token = _session_ctx.set(session)
    cache_token = _services_cache_ctx.set({})
    exists_cache_token = _exists_cache_ctx.set({})
    updated_cache_token = _updated_cache_ctx.set(set())
    creation_cache_token = _creation_cache_ctx.set({})
    update_needed_cache_token = _update_needed_cache_ctx.set(set())
    try:
        yield
    finally:
        # Логируем очистку
        cache_stats = {
            "services": len(_services_cache_ctx.get()),
            "exists_checks": len(_exists_cache_ctx.get()),
            "updated_objects": len(_updated_cache_ctx.get()),
            "created_entities": len(_creation_cache_ctx.get()),
            "update_needed": len(_update_needed_cache_ctx.get()),
        }
        logger.debug(f"Cleaning request context. Cache stats: {cache_stats}")

        # Очищаем кеш и сбрасываем контекст после завершения запроса
        _update_needed_cache_ctx.reset(update_needed_cache_token)
        _creation_cache_ctx.reset(creation_cache_token)
        _updated_cache_ctx.reset(updated_cache_token)
        _exists_cache_ctx.reset(exists_cache_token)
        _services_cache_ctx.reset(cache_token)
        _session_ctx.reset(session_token)


def get_session_context() -> AsyncSession:
    """Получает текущую сессию из контекста"""
    session = _session_ctx.get()
    if session is None:
        raise RuntimeError("Session context is not set")
    return session


def get_exists_cache() -> (
    dict[tuple[Type[Any], tuple[tuple[str, Any], ...]], bool]
):
    """Возвращает кэш проверок существования объектов"""
    return _exists_cache_ctx.get()


def reset_exists_cache() -> None:
    """Сбрасывает кэш проверок"""
    _exists_cache_ctx.set({})


def get_updated_cache() -> set[tuple[Type[Any], int | str]]:
    """Возвращает кэш проверок обновлённых объектов"""
    return _updated_cache_ctx.get()


def reset_updated_cache() -> None:
    """Сбрасывает кэш обновлённых объектов"""
    _updated_cache_ctx.set(set())


def get_creation_cache() -> dict[tuple[Type[Any], int | str], bool]:
    """
    Возвращает кэш для отслеживания создания сущностей в текущем контексте
    """
    return _creation_cache_ctx.get()


def reset_creation_cache() -> None:
    """
    Сбрасывает кэш для отслеживания создания сущностей в текущем контексте
    """
    _creation_cache_ctx.set({})


def get_update_needed_cache() -> set[tuple[Type[Any], int | str]]:
    """
    Возвращает кэш для отслеживания сущностей, требующих обновления
    """
    return _update_needed_cache_ctx.get()


def reset_update_needed_cache() -> None:
    """
    Сбрасывает кэш для отслеживания сущностей, требующих обновления
    """
    _update_needed_cache_ctx.set(set())


def reset_cache() -> None:
    """
    Сбрасывает кэш
    """
    _update_needed_cache_ctx.set(set())
    _creation_cache_ctx.set({})
    _updated_cache_ctx.set(set())
    _exists_cache_ctx.set({})
    _services_cache_ctx.set({})
