from typing import Any

from core.logger import logger
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
            if message.email.type_event != "request_price":
                logger.warning(
                    f"Неизвестный тип события: {message.email.type_event}"
                )
                return False

            request_data = message.email.parsed_body
            request_data.message_id = message.email.email_id

            params = self._prepare_request_params(request_data)

            success, _ = await self.site_request_service.send_request(
                "api/v1/b24/site_request/site-request", params
            )

            return success

        except Exception as e:
            logger.error(f"Ошибка при отправке сделки: {e}")
            return False

    def _prepare_request_params(self, request_data: Any) -> dict[str, Any]:
        """
        Подготавливает параметры запроса.

        Args:
            request_data: Данные запроса

        Returns:
            Словарь с параметрами
        """
        params: dict[str, Any] = {
            "phone": request_data.phone,
            "product_id": request_data.product_id,
        }

        # Добавляем опциональные параметры
        optional_params = {
            "product_name": request_data.product,
            "name": request_data.name,
            "comment": request_data.comment,  # or request_data.raw_text,
            "message_id": request_data.message_id,
        }

        for key, value in optional_params.items():
            if value:
                params[key] = value

        return params
