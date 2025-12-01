from typing import TYPE_CHECKING

# from core.logger import logger

if TYPE_CHECKING:
    from .deal_services import DealClient


class DealWebhookHandler:
    """
    Обработчик, который применяет бизнес-логику к сделке в зависимости от ее
    состояния.
    """

    def __init__(self, deal_client: "DealClient") -> None:
        self.deal_client = deal_client

    async def handle_deal_without_offer(
        self,
        user_id: str,
        deal_id: str,
    ) -> None:
        """
        Обработчик входящего вебхука сделки без КП.
        """
        ...
