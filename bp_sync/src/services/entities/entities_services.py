from typing import Any

from fastapi import HTTPException, status

from api.v1.schemas.site_request import SiteRequestPayload
from core.logger import logger

from ..exceptions import DealCreationError, SiteRequestProcessingError
from ..suppliers.supplier_services import SupplierClient
from .entities_bitrix_services import EntitiesBitrixClient
from .supplier_product_resolver import SupplierProductResolver


class EntityClient:
    def __init__(
        self,
        bitrix_client: EntitiesBitrixClient,
        supplier_client: SupplierClient,
        supplier_product_resilver: SupplierProductResolver | None = None,
    ):
        super().__init__()
        self._bitrix_client = bitrix_client
        self._supplier_client = supplier_client
        self._supplier_product_resolver = supplier_product_resilver

    @property
    def bitrix_client(self) -> EntitiesBitrixClient:
        return self._bitrix_client

    @property
    def supplier_client(self) -> SupplierClient:
        return self._supplier_client

    @property
    def supplier_product_resilver(self) -> SupplierProductResolver:
        if not self._supplier_product_resolver:
            self._supplier_product_resolver = SupplierProductResolver(self)
        return self._supplier_product_resolver

    async def handle_request_price(
        self, payload: SiteRequestPayload
    ) -> dict[str, Any]:
        """
        Обрабатывает запрос цены с сайта.

        Создает сделку, привязывает контакт/компанию,
        добавляет товары и комментарии.

        Args:
            payload: Данные запроса с сайта

        Returns:
            dict: Результат обработки с деталями операции

        Raises:
            HTTPException: При критических ошибках обработки
        """
        self._log_request_start(payload)
        site_request_handler = self.bitrix_client.site_request_handler
        try:
            deal_id = await site_request_handler.create_deal_from_payload(
                payload
            )
        except DealCreationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Not create deal. Exception: {e}",
            )
        except Exception as e:
            self._log_unexpected_error(payload, e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    f"Unexpected error during creating deal. Exception: {e}"
                ),
            )

        result = self._create_success_result(deal_id)
        try:
            await self.supplier_product_resilver.process_deal_products(
                deal_id, payload, result
            )
        except Exception as e:
            self._log_unexpected_error(payload, e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    f"Unexpected error during adding product. Exception: {e}"
                ),
            )
        try:
            await site_request_handler.add_timeline_comment(deal_id, payload)
        except Exception as e:
            self._log_unexpected_error(payload, e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    "Unexpected error during adding timeline comment. "
                    f"Exception: {e}"
                ),
            )
        self._log_request_success(deal_id, result)
        return result

    def _create_success_result(self, deal_id: int) -> dict[str, Any]:
        """Создает базовый результат успешной обработки."""
        return {
            "success": True,
            "deal_id": deal_id,
            "message": "Запрос успешно обработан",
        }

    # --- Логирование ---

    def _log_request_start(self, payload: SiteRequestPayload) -> None:
        """Логирует начало обработки запроса."""
        logger.info(
            "Начало обработки запроса с сайта",
            extra={
                "type_event": payload.type_event,
                "phone": payload.phone if payload.phone else "-",
                "email": payload.email if payload.email else "-",
                "contact_name": payload.name if payload.name else "-",
                "message_id": (
                    payload.message_id if payload.message_id else "-"
                ),
            },
        )

    def _log_request_success(
        self,
        deal_id: int,
        result: dict[str, Any],
    ) -> None:
        """Логирует успешное завершение обработки."""
        logger.info(
            "Запрос успешно обработан",
            extra={"deal_id": deal_id, "result": result},
        )

    def _log_processing_error(
        self,
        payload: SiteRequestPayload,
        error: SiteRequestProcessingError,
    ) -> None:
        """Логирует ошибку обработки."""
        logger.error(
            "Ошибка обработки запроса",
            extra={
                "type_event": payload.type_event,
                "error": str(error),
                "error_type": type(error).__name__,
            },
            exc_info=True,
        )

    def _log_unexpected_error(
        self,
        payload: SiteRequestPayload,
        error: Exception,
    ) -> None:
        """Логирует неожиданную ошибку."""
        logger.error(
            "Критическая ошибка при обработке запроса",
            extra={
                "type_event": payload.type_event,
                "phone": payload.phone,
                "error": str(error),
                "error_type": type(error).__name__,
            },
            exc_info=True,
        )
