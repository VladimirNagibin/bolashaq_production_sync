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
SUPERVISOR_OVERDUE_THRESHOLD_DAYS = 2
MIN_OVERDUE_DAYS_FOR_DISPLAY = 1


class LeadClient(BaseEntityClient[LeadDB, LeadRepository, LeadBitrixClient]):
    """Клиент для управления лидами."""

    def __init__(
        self,
        lead_bitrix_client: LeadBitrixClient,
        lead_repo: LeadRepository,
        user_client: UserClient | None = None,
    ) -> None:
        """
        Инициализирует клиент лидов.

        Args:
            lead_bitrix_client: Клиент Bitrix для работы с лидами
            lead_repo: Репозиторий лидов
            user_client: Клиент пользователей (опционально)
        """
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
        try:
            overdue_leads = await self.repo.get_overdue_leads()
            notifications = await self._prepare_overdue_leads_notifications(
                overdue_leads
            )
            await self._send_notifications(notifications)
        except Exception as e:
            logger.error(f"Failed to send overdue leads notifications: {e}", exc_info=True)
    
    async def _prepare_overdue_leads_notifications(
        self,
        overdue_leads: list[tuple[LeadDB, timedelta]],
    ) -> list[tuple[int, str]]:
        """
        Подготавливает уведомления о просроченных лидах.

        Args:
            overdue_leads: Список просроченных лидов с временем просрочки

        Returns:
            Список кортежей (ID пользователя, сообщение)
        """
        if not overdue_leads:
            logger.info("No overdue leads found")
            return [(SUPERVISOR_ID, "Нет просроченных лидов.")]
        
        try:
            leads_by_user, critical_leads = await self._group_overdue_leads_by_user(
                overdue_leads
            )
            notifications = self._build_notifications(leads_by_user, critical_leads)
            return notifications

        except Exception as e:
            logger.error(f"Failed to prepare notifications: {e}", exc_info=True)
            return [(SUPERVISOR_ID, "Ошибка при формировании списка просроченных лидов.")]

    async def _group_overdue_leads_by_user(
        self, overdue_leads: list[tuple[LeadDB, timedelta]],
    ) -> tuple[
        dict[tuple[str, int], list[dict[str, Any]]],
        dict[tuple[str, int], list[dict[str, Any]]],
    ]:
        """
        Группирует просроченные лиды по ответственным пользователям.

        Args:
            overdue_leads: Список просроченных лидов

        Returns:
            Кортеж из двух словарей:
            - все лиды по пользователям
            - критически просроченные лиды (>2 дней)
        """
        all_leads: dict[
            tuple[str, int], list[dict[str, Any]]
        ] = {}
        critical_leads: dict[
            tuple[str, int], list[dict[str, Any]]
        ] = {}

        for lead, overdue_delta in overdue_leads:
            try:
                lead_info = await self._extract_lead_notification_info(
                    lead, overdue_delta
                )

                user_key = (lead_info["user_name"], lead_info["assigned_id"])
                if user_key not in all_leads:
                    all_leads[user_key] = []
                all_leads[user_key].append(lead_info)

                if lead_info["overdue_days"] > SUPERVISOR_OVERDUE_THRESHOLD_DAYS:
                    if user_key not in critical_leads:
                        critical_leads[user_key] = []
                    critical_leads[user_key].append(lead_info)

            except Exception as e:
                logger.error(
                    f"Error processing lead {getattr(lead, 'external_id', 'unknown')}: {e}",
                    exc_info=True
                )
                continue

        return all_leads, critical_leads

    async def _extract_lead_notification_info(
        self, 
        lead: LeadDB, 
        overdue_delta: timedelta
    ) -> dict[str, Any]:
        """
        Извлекает информацию о лиде для уведомления.

        Args:
            lead: Модель лида
            overdue_delta: Время просрочки

        Returns:
            Словарь с информацией о лиде
        """
        user_name = getattr(lead.assigned_user, 'full_name', 'Неизвестный пользователь')
        assigned_id = getattr(lead, 'assigned_by_id', 0)
        
        lead_link = self.bitrix_client.get_formatted_link(
            lead.external_id, lead.title
        )
        
        overdue_days = overdue_delta.days
        display_days = max(overdue_days - 1, MIN_OVERDUE_DAYS_FOR_DISPLAY) if overdue_days > 1 else 1

        return {
            "user_name": user_name,
            "assigned_id": assigned_id,
            "status": lead.status_id,
            "status_display": MAPPED_STATUSES.get(lead.status_id, "Не определено"),
            "link": lead_link,
            "overdue_delta": overdue_delta,
            "overdue_days": overdue_days,
            "display_days": display_days,
            "external_id": lead.external_id,
            "title": lead.title,
        }

    def _build_notifications(
        self,
        all_leads: dict[tuple[str, int], list[dict[str, Any]]],
        critical_leads: dict[tuple[str, int], list[dict[str, Any]]],
    ) -> list[tuple[int, str]]:
        """
        Формирует уведомления для менеджеров и супервизора.

        Args:
            all_leads: Все лиды, сгруппированные по пользователям
            critical_leads: Критически просроченные лиды

        Returns:
            Список уведомлений
        """
        notifications: list[tuple[int, str]] = []
        title = "Просроченные лиды:"

        # Уведомления для менеджеров
        for user_key, user_leads in all_leads.items():
            _, user_id = user_key
            message = self._format_manager_message(user_leads)
            notifications.append((user_id, f"{title}\n{message}"))
            logger.info(
                f"Prepared notification for user {user_id} with "
                f"{len(user_leads)} overdue leads"
            )

        # Уведомление для супервизора
        supervisor_message = self._format_supervisor_message(critical_leads)
        notifications.append((SUPERVISOR_ID, f"{title}\n{supervisor_message}"))
        
        return notifications

    def _format_supervisor_message(
        self, 
        critical_leads: dict[tuple[str, int], list[dict[str, Any]]]
    ) -> str:
        """
        Форматирует сообщение для супервизора.

        Args:
            critical_leads: Критически просроченные лиды по менеджерам

        Returns:
            Отформатированное сообщение
        """
        if not critical_leads:
            return "Нет просроченных лидов."

        supervisor_parts: list[str] = []
        
        for (user_name, user_id), user_leads in critical_leads.items():
            if user_leads:
                supervisor_parts.append("")  # Пустая строка для разделения
                supervisor_parts.append(user_name)
                supervisor_parts.append(
                    self._format_manager_message(user_leads)
                )

        return "\n".join(supervisor_parts) if supervisor_parts else "Нет критически просроченных лидов."

    def _format_manager_message(
        self,
        leads: list[dict[str, Any]],
    ) -> str:
        """
        Форматирует сообщение для конкретного менеджера.

        Args:
            leads: Список лидов менеджера

        Returns:
            Отформатированное сообщение
        """
        if not leads:
            return "  • Нет просроченных лидов."

        message_parts: list[str] = []

        for lead in leads:
            message_parts.append(
                f"  • Стадия: {lead['status_display']}, "
                f"просрочено: {lead['display_days']} дн. "
                f"{lead['link']}"
            )

        return "\n".join(message_parts)

    async def _send_notifications(self, notifications: list[tuple[int, str]]) -> None:
        """
        Отправляет уведомления через Bitrix.

        Args:
            notifications: Список уведомлений для отправки
        """
        for user_id, message in notifications:
            try:
                # Временно для отладки
                debug_user_id = 37
                await self.bitrix_client.send_message_b24(debug_user_id, message)
                logger.info(f"Notification sent to user {debug_user_id} (original: {user_id})")
            except Exception as e:
                logger.error(f"Failed to send notification to user {user_id}: {e}", exc_info=True)
