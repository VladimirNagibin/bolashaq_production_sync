import asyncio
from datetime import date, timedelta
from typing import Any

from schemas.deal_schemas import DealCreate, DealUpdate

from ..bitrix_services.base_bitrix_services import BaseBitrixEntityClient


class DealBitrixClient(BaseBitrixEntityClient[DealCreate, DealUpdate]):

    entity_name = "deal"
    create_schema = DealCreate
    update_schema = DealUpdate

    DEALS_BATCH_SIZE = 50
    DEALS_SLEEP_INTERVAL = 2

    async def get_deal_ids_for_period(
        self, start_date: date, end_date: date
    ) -> list[int]:
        """Получить ID сделок за период"""
        end_date_plus_one = end_date + timedelta(days=1)
        start_str = start_date.strftime("%Y-%m-%d 00:00:00")
        end_str = end_date_plus_one.strftime("%Y-%m-%d 00:00:00")

        filter_entity: dict[str, Any] = {
            ">=BEGINDATE": start_str,
            "<BEGINDATE": end_str,
            "CATEGORY_ID": 0,
        }

        deal_ids: list[int] = []
        select = ["ID"]
        start = 0

        while True:
            result = await self.list(
                select=select, filter_entity=filter_entity, start=start
            )

            if not result:
                break

            deals_batch = result.result
            deal_ids.extend(
                int(deal.external_id)
                for deal in deals_batch
                if deal.external_id is not None
                and str(deal.external_id).isdigit()
            )

            if not result.next or len(deals_batch) < self.DEALS_BATCH_SIZE:
                break

            start = result.next
            await asyncio.sleep(self.DEALS_SLEEP_INTERVAL)

        return deal_ids
