from datetime import timedelta
from typing import Any

from core.logger import logger
from core.settings import settings
from models.lead_models import Lead as LeadDB
from services.users.user_services import UserClient

from ..base_services.base_service import BaseEntityClient
from .lead_bitrix_services import LeadBitrixClient
from .lead_repository import LeadRepository

SUPERVISOR_ID = 15
MAPPED_STATUSES = {
    "NEW": "Не обработан",
    "IN_PROCESS": "В работе",
    "PROCESSED": "Обработан",
}


class LeadClient(BaseEntityClient[LeadDB, LeadRepository, LeadBitrixClient]):
    def __init__(
        self,
        lead_bitrix_client: LeadBitrixClient,
        lead_repo: LeadRepository,
        user_client: UserClient | None = None,
    ):
        super().__init__()
        self._bitrix_client = lead_bitrix_client
        self._repo = lead_repo

        if user_client is not None:
            self._repo.set_user_client(user_client)

    @property
    def entity_name(self) -> str:
        return "lead"

    @property
    def bitrix_client(self) -> LeadBitrixClient:
        return self._bitrix_client

    @property
    def repo(self) -> LeadRepository:
        return self._repo

    @property
    def webhook_config(self) -> dict[str, Any]:
        return settings.web_hook_config_lead  # type: ignore
    
    async def send_overdue_leads_notifications(self) -> None:
        """
        Отправляет уведомления ответственным пользователям 
        о просроченных лидах.
        """
        overdue_leads = await self.repo.get_overdue_leads()
        notifications = await self._get_formatted_data_overdue_leads(
            overdue_leads
        )
        for notification in notifications:
            user_id, message = notification
            user_id = 37  # debugging ================
            await self.bitrix_client.send_message_b24(
                user_id, message
            )

    async def _get_formatted_data_overdue_leads(
        self,
        overdue_leads: list[tuple[LeadDB, timedelta]],
    ) -> list[tuple[int, str]]:
        """
        Форматирует данные о просроченных лидах в читаемое сообщение и
        определяем список получателей
        """
        if not overdue_leads:
            return [(SUPERVISOR_ID, "Нет просроченных лидов.")]

        leads_data, supervisor_data = await self._transform_overdue_leads_data(
            overdue_leads
        )
        notifications: list[tuple[int, str]] = []
        title = "Просроченные лиды:"
        for user_key, user_deals in leads_data.items():
            _, user_id = user_key
            message = self._format_manager_message(user_deals)
            notifications.append(
                (user_id, f"{title}\n{message}")
            )
        supervisor_message: list[str] = [] 
        for user_key, user_deals in supervisor_data.items():
            user_name, user_id = user_key
            if user_deals:
                message = self._format_manager_message(user_deals)
                supervisor_message.append("") 
                supervisor_message.append(user_name)
                supervisor_message.append(message)  
 
        if supervisor_message:
            notifications.append(
                (SUPERVISOR_ID, f"{title}\n{"\n".join(supervisor_message)}")
            )
        else:
            notifications.append((SUPERVISOR_ID, "Нет просроченных лидов."))
        return notifications

    async def _transform_overdue_leads_data(
        self, overdue_leads: list[tuple[LeadDB, timedelta]],
    ) -> tuple[
        dict[tuple[str, int], list[dict[str, Any]]],
        dict[tuple[str, int], list[dict[str, Any]]],
    ]:
        """
        Преобразует данные сделок в структурированный формат

        Returns:
            dict: {
                (Имя Фамилия, user_id): ["
                    {
                        link: "ссылка",
                        status: "Стадия",
                        overdue_days: int,  # количество полных дней
                        overdue: timedelta,  # исходный объект
                    }
                ]
            }
        """
        leads_by_user: dict[
            tuple[str, int], list[dict[str, Any]]
        ] = {}
        leads_for_supervisor: dict[
            tuple[str, int], list[dict[str, Any]]
        ] = {}

        for lead, overdue in overdue_leads:
            try:
                user_name = lead.assigned_user.full_name
                assigned_id = lead.assigned_by_id
                lead_link = self.bitrix_client.get_formatted_link(
                    lead.external_id, lead.title
                )
                overdue_days = overdue.days 

                deal_data: dict[str, Any] = {
                    "status": lead.status_id,
                    "link": lead_link,
                    "overdue": overdue,
                    "overdue_days": overdue_days,  
                    "external_id": lead.external_id,
                }
                user_key = (user_name, assigned_id)
                if user_key not in leads_by_user:
                    leads_by_user[user_key] = []
                if user_key not in leads_for_supervisor:
                    leads_for_supervisor[user_key] = []

                leads_by_user[user_key].append(deal_data)

                if overdue_days > 2:
                    leads_for_supervisor[user_key].append(deal_data)

            except Exception as e:
                logger.error(
                    f"Error transforming deal {lead.external_id}: {e}"
                )
                continue

        return leads_by_user, leads_for_supervisor

    def _format_manager_message(
        self,
        leads: list[dict[str, Any]],
    ) -> str:
        "Форматирует сообщение для конкретного менеджера"
        message_parts: list[str] = []

        for lead in leads:
            overdue_days = lead['overdue_days']-1 if lead['overdue_days'] > 1 else 1
            message_parts.append(
                f"  • Стадия: {MAPPED_STATUSES.get(lead['status'], "Не определено")}, "
                f"просрочено: {overdue_days} дн. "
                f"{lead['link']}"
            )
        return "\n".join(message_parts)
