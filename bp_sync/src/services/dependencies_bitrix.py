from typing import Any, AsyncGenerator, Type, TypeVar

from redis.asyncio import Redis

from db.redis import get_redis as get_redis_client
from schemas.base_schemas import CommonFieldMixin

from .bitrix_services.base_bitrix_services import BaseBitrixEntityClient
from .bitrix_services.bitrix_api_client import BitrixAPIClient
from .bitrix_services.bitrix_oauth_client import BitrixOAuthClient
from .token_services.token_cipher import TokenCipher
from .token_services.token_storage import TokenStorage

SchemaTypeCreate = TypeVar("SchemaTypeCreate", bound=CommonFieldMixin)
SchemaTypeUpdate = TypeVar("SchemaTypeUpdate", bound=CommonFieldMixin)
T = TypeVar("T", bound=BaseBitrixEntityClient[Any, Any])


class DependencyContainer:
    """
    Контейнер зависимостей для управления жизненным циклом сервисов
    """

    def __init__(self) -> None:
        self._redis: Redis | None = None
        self._token_cipher: TokenCipher | None = None
        self._token_storage: TokenStorage | None = None
        self._oauth_client: BitrixOAuthClient | None = None
        self._api_client: BitrixAPIClient | None = None
        self._entity_clients: dict[
            Type[BaseBitrixEntityClient[Any, Any]],
            BaseBitrixEntityClient[Any, Any],
        ] = {}

    async def get_redis(self) -> Redis:
        """Получает Redis клиент"""
        if self._redis is None:
            self._redis = await get_redis_client()
        return self._redis

    async def get_token_cipher(self) -> TokenCipher:
        """Получает шифровальщик токенов"""
        if self._token_cipher is None:
            self._token_cipher = TokenCipher()
        return self._token_cipher

    async def get_token_storage(self) -> TokenStorage:
        """Получает хранилище токенов"""
        if self._token_storage is None:
            redis = await self.get_redis()
            cipher = await self.get_token_cipher()
            self._token_storage = TokenStorage(redis, cipher)
        return self._token_storage

    async def get_oauth_client(self) -> BitrixOAuthClient:
        """Получает OAuth клиент Bitrix"""
        if self._oauth_client is None:
            token_storage = await self.get_token_storage()
            self._oauth_client = BitrixOAuthClient(token_storage=token_storage)
        return self._oauth_client

    async def get_api_client(self) -> BitrixAPIClient:
        """Получает API клиент Bitrix"""
        if self._api_client is None:
            oauth_client = await self.get_oauth_client()
            self._api_client = BitrixAPIClient(oauth_client=oauth_client)
        return self._api_client

    async def get_entity_client(self, entity_class: Type[T]) -> T:
        """Получает клиент для работы с сущностью Bitrix"""
        if entity_class not in self._entity_clients:
            api_client = await self.get_api_client()
            self._entity_clients[entity_class] = entity_class(api_client)
        return self._entity_clients[entity_class]  # type: ignore

    async def shutdown(self) -> None:
        """Корректное завершение работы контейнера"""
        self._token_cipher = None
        self._token_storage = None
        self._oauth_client = None
        self._api_client = None
        self._entity_clients.clear()


dependency_container: DependencyContainer = DependencyContainer()


async def get_dependency_container() -> (
    AsyncGenerator[DependencyContainer, None]
):
    """
    Зависимость для получения контейнера зависимостей
    """
    try:
        yield dependency_container
    finally:
        # Контейнер не закрывается здесь, так как он глобальный
        # Закрытие происходит при остановке приложения
        pass


async def get_redis() -> AsyncGenerator[Redis, None]:
    """
    Зависимость для получения Redis клиента
    """
    container = dependency_container
    redis = await container.get_redis()
    try:
        yield redis
    finally:
        # Redis соединение управляется контейнером
        pass


async def get_token_cipher() -> AsyncGenerator[TokenCipher, None]:
    """
    Зависимость для получения шифровальщика токенов
    """
    container = dependency_container
    cipher = await container.get_token_cipher()
    yield cipher


async def get_token_storage() -> AsyncGenerator[TokenStorage, None]:
    """
    Зависимость для получения хранилища токенов
    """
    container = dependency_container
    storage = await container.get_token_storage()
    yield storage


async def get_oauth_client() -> AsyncGenerator[BitrixOAuthClient, None]:
    """
    Зависимость для получения OAuth клиента Bitrix
    """
    container = dependency_container
    oauth_client = await container.get_oauth_client()
    yield oauth_client


async def get_api_client() -> AsyncGenerator[BitrixAPIClient, None]:
    """
    Зависимость для получения API клиента Bitrix
    """
    container = dependency_container
    api_client = await container.get_api_client()
    yield api_client


def get_entity_client(entity_class: Type[T]) -> AsyncGenerator[T, None]:
    """
    Фабрика для создания зависимостей entity клиентов

    Args:
        entity_class: Класс entity клиента

    Returns:
        Зависимость для FastAPI
    """

    async def _get_entity_client() -> AsyncGenerator[T, None]:
        container = dependency_container
        entity_client = await container.get_entity_client(entity_class)
        yield entity_client

    return _get_entity_client  # type: ignore


# Утилиты для работы с контейнером
async def initialize_container() -> None:
    """
    Предварительная инициализация контейнера
    """
    # Предзагружаем часто используемые зависимости
    await dependency_container.get_redis()
    await dependency_container.get_api_client()


async def shutdown_container() -> None:
    """
    Корректное завершение работы контейнера
    """
    await dependency_container.shutdown()
