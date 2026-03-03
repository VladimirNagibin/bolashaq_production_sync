import asyncio

from datetime import date, timedelta
from typing import Any

from schemas.lead_schemas import LeadCreate, LeadUpdate

from ..bitrix_services.base_bitrix_services import BaseBitrixEntityClient


class LeadBitrixClient(BaseBitrixEntityClient[LeadCreate, LeadUpdate]):
    entity_name = "lead"
    create_schema = LeadCreate
    update_schema = LeadUpdate

    LEADS_BATCH_SIZE = 50
    LEADS_SLEEP_INTERVAL = 2

    async def get_lead_ids_for_period(
        self, start_date: date, end_date: date
    ) -> list[int]:
        "Получить ID сделок за период"
        end_date_plus_one = end_date + timedelta(days=1)
        start_str = start_date.strftime("%Y-%m-%d 00:00:00")
        end_str = end_date_plus_one.strftime("%Y-%m-%d 00:00:00")

        filter_entity: dict[str, Any] = {
            ">=BEGINDATE": start_str,
            "<BEGINDATE": end_str,
            "CATEGORY_ID": 0,
        }

        lead_ids: list[int] = []
        select = ["ID"]
        start = 0

        while True:
            result = await self.list(
                select=select, filter_entity=filter_entity, start=start
            )

            if not result:
                break

            leads_batch = result.result
            lead_ids.extend(
                int(lead.external_id)
                for lead in leads_batch
                if lead.external_id is not None
                and str(lead.external_id).isdigit()
            )

            if not result.next or len(leads_batch) < self.LEADS_BATCH_SIZE:
                break

            start = result.next
            await asyncio.sleep(self.LEADS_SLEEP_INTERVAL)

        return lead_ids
