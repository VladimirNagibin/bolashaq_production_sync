from core.logger import logger
from db.postgres import get_session_generator
from db.redis import get_redis, init_redis, close_redis
from services.bitrix_services.bitrix_api_client import (
    BitrixAPIClient, BitrixOAuthClient
)
from services.leads.lead_services import LeadClient
from services.leads.lead_bitrix_services import LeadBitrixClient
from services.leads.lead_repository import LeadRepository
from services.token_services.token_cipher import TokenCipher
from services.token_services.token_storage import TokenStorage


class LeadServiceFactory:
    """
    Фабрика для создания экземпляров LeadClient вне системы зависимостей.
    """
    def __init__(self):
        """Инициализирует планировщик без зависимостей."""
        self._lead_client: LeadClient | None = None
        self._initialized: bool = False
        self._shutting_down: bool = False
        self._session_generator = None
        self._session = None

    async def initialize(self) -> None:
        """
        Инициализирует все необходимые зависимости.
        Должен быть вызван перед использованием планировщика.
        """
        if self._initialized:
            logger.warning("Scheduler уже инициализирован")
            return

        try:
            # Инициализация Redis
            await init_redis()
            redis = await get_redis()
            
            # Создание сессии базы данных
            self._session_generator = get_session_generator()
            self._session = await self._session_generator.__anext__()
            
            # Инициализация зависимостей
            token_cipher = TokenCipher()
            
            token_storage = TokenStorage(redis, token_cipher)
            oauth_client = BitrixOAuthClient(token_storage)
            bitrix_api_client = BitrixAPIClient(oauth_client)
            
            lead_repo = LeadRepository(self._session)
            lead_bitrix_client = LeadBitrixClient(bitrix_api_client)
            
            self._lead_client = LeadClient(lead_bitrix_client, lead_repo)
            self._initialized = True
            
            logger.info("Scheduler успешно инициализирован")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации Scheduler: {e}", exc_info=True)
            await self.cleanup()
            raise

    async def cleanup(self) -> None:
        """
        Очищает ресурсы при завершении работы.
        Должен быть вызван при остановке приложения.
        """
        try:
            # Закрываем генератор сессии. Это автоматически закроет и саму сессию.
            if self._session_generator:
                try:
                    await self._session_generator.aclose()
                except Exception as e:
                    # Логируем, но не даём упасть, т.к. это уже процесс очистки
                    logger.debug(f"Ошибка при закрытии генератора сессии: {e}")

            # Закрываем Redis
            await close_redis()

            self._lead_client = None
            self._initialized = False
            logger.info("Ресурсы планировщика очищены")

        except Exception as e:
            logger.error(f"Ошибка при очистке ресурсов: {e}", exc_info=True)

    async def send_overdue_leads_notifications(self):
        await self._lead_client.send_overdue_leads_notifications()
