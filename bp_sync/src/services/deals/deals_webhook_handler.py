import re
from datetime import date
from typing import TYPE_CHECKING, Any

from fastapi import HTTPException, status

from core.logger import logger
from schemas.deal_schemas import DealUpdate
from schemas.enums import DealStagesEnum, DealStatusEnum

if TYPE_CHECKING:
    from .deal_services import DealClient


class DealWebhookHandler:
    """
    Обработчик, который обработывает входящие вебхуки сделок.
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
        repo = self.deal_client.repo
        contract_stage_id = await repo.get_external_id_by_sort_order_stage(
            DealStagesEnum.CONTRACT_CONCLUSION,
        )
        data_deal: dict[str, Any] = {
            "external_id": deal_id,
            "without_offer": True,
            "moved_date": date.today(),
            "status_deal": DealStatusEnum.OFFER_NO,
            "stage_id": contract_stage_id,
        }
        deal_update = DealUpdate(**data_deal)

        await self._update_local_deal(deal_id, deal_update)
        await self.deal_client.bitrix_client.update(deal_update)

    async def _update_local_deal(
        self, deal_id: str, deal_update: DealUpdate
    ) -> None:
        """Update deal in local database with error handling"""
        try:
            await self.deal_client.repo.update_entity(deal_update)
            logger.info(f"Deal {deal_id} source updated in local database")

        except HTTPException as e:
            if e.status_code == status.HTTP_404_NOT_FOUND:
                logger.info(
                    f"Deal {deal_id} not found locally, importing from Bitrix"
                )
                await self.deal_client.import_from_bitrix(deal_id)
                await self.deal_client.repo.update_entity(deal_update)
            else:
                raise
        except Exception as e:
            logger.error(f"Failed to update local deal {deal_id}: {str(e)}")
            raise

    async def set_products_string_field(
        self,
        user_id: str,
        deal_id: str,
        products: str,
    ) -> None:
        """
        Обработчик входящего вебхука сделки установка списка товаров в
        строковое поле.
        """
        logger.info(f"Deal {deal_id} set products string field :{products}")
        products_list_as_string = self._get_products_list_as_string(
            products,
        )
        logger.info(
            f"Deal {deal_id} products list as string :"
            f"{products_list_as_string}"
        )
        data_deal: dict[str, Any] = {
            "external_id": deal_id,
            "products_list_as_string": products_list_as_string,
        }
        deal_update = DealUpdate(**data_deal)

        await self._update_local_deal(deal_id, deal_update)
        await self.deal_client.bitrix_client.update(deal_update)

    def _get_products_list_as_string(self, table_string: str) -> str:
        """
        Преобразует BBCode-таблицу в форматированный текст.

        Args:
            table_string: Строка с таблицей в формате BBCode.

        Returns:
            Отформатированная строка с данными из таблицы.
        """
        # Регулярное выражение для поиска пар [td]...[/td][td]...[/td]
        # (.*?) - ленивый захват любого текста внутри тегов
        pattern = re.compile(r"\[td\](.*?)\[/td\]\[td\](.*?)\[/td\]")

        # Находим все совпадения в строке
        # Результатом будет список кортежей:
        # [('Товар1', 'Цена1'), ('Товар2', 'Цена2')]
        matches = pattern.findall(table_string)

        # Формируем строки из найденных пар
        lines = [f"{product}: {price}" for product, price in matches]

        # Соединяем все строки в единый текст с переносом строки
        return "\n".join(lines)

    async def set_stage_status_deal(
        self,
        deal_id: str,
        stage_deal: int,
        status_deal: str,
        user_id: str | None = None,
    ) -> None:
        """
        Обработчик входящего вебхука сделки без КП.
        """
        repo = self.deal_client.repo
        stage_id = await repo.get_external_id_by_sort_order_stage(
            stage_deal,
        )
        data_deal: dict[str, Any] = {
            "external_id": deal_id,
            "status_deal": DealStatusEnum.get_deal_status_by_name(status_deal),
            "stage_id": stage_id,
        }
        deal_update = DealUpdate(**data_deal)

        await self._update_local_deal(deal_id, deal_update)
        await self.deal_client.bitrix_client.update(deal_update)
