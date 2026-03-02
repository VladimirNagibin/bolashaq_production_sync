from typing import Any

from core.logger import logger
from core.settings import settings
from schemas.message_schemas import MessageData

from .sender_request import SiteRequestService


class Sender:
    """Сервис для отправки данных о сделках."""

    def __init__(
        self,
        site_request_service: SiteRequestService | None = None,
    ):
        """
        Args:
            site_request_service: Сервис для работы с API
        """
        self.site_request_service = (
            site_request_service or SiteRequestService()
        )

    async def send_to_deal(self, message: MessageData) -> bool:
        """
        Отправляет данные о сделке во внешнюю систему.

        Args:
            message: Данные сообщения

        Returns:
            True если отправка успешна, иначе False
        """
        try:
            type_events = set(
                [
                    type_event.strip()
                    for type_event in settings.TYPE_EVENTS.split(",")
                ]
            )
            email_type_event = message.email.type_event
            if email_type_event not in type_events:
                logger.warning(f"Неизвестный тип события: {email_type_event}")
                return False

            request_data = message.email.parsed_body
            request_data.message_id = message.email.email_id

            params = self._prepare_request_params(
                request_data, email_type_event
            )

            success, _ = await self.site_request_service.send_request(
                "api/v1/b24/site_request/site-request", params
            )

            return success

        except Exception as e:
            logger.error(f"Ошибка при отправке сделки: {e}")
            return False

    def _prepare_request_params(
        self, request_data: Any, email_type_event: str
    ) -> dict[str, Any]:
        """
        Подготавливает параметры запроса.

        Args:
            request_data: Данные запроса

        Returns:
            Словарь с параметрами
        """
        params: dict[str, Any] = {
            "type_event": email_type_event,
        }

        # Добавляем опциональные параметры
        optional_params = {
            "phone": request_data.phone,
            "email": request_data.email,
            "product_id": request_data.product_id,
            "product_name": request_data.product,
            "name": request_data.name,
            "bin_company": request_data.bin_company,
            "comment": request_data.comment,  # or request_data.raw_text,
            "message_id": request_data.message_id,
        }

        for key, value in optional_params.items():
            if value:
                params[key] = value
        if request_data.products:
            params["products"] = [
                product.dict() for product in request_data.products
            ]
        return params
