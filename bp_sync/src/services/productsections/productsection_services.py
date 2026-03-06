import time
from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import logger
from core.settings import settings
from models.productsection_models import Productsection as ProductsectionDB
from schemas.productsection_schemas import Productsection

from ..base_repositories.base_repository import BaseRepository
from ..bitrix_services.bitrix_api_client import BitrixAPIClient
from ..bitrix_services.webhook_service import WebhookService
from ..exceptions import ConflictException


class ProductsectionClient(
    BaseRepository[ProductsectionDB, Productsection, Productsection, int]
):

    model = ProductsectionDB

    def __init__(
        self,
        bitrix_client: BitrixAPIClient,
        session: AsyncSession,
    ) -> None:
        super().__init__(session)
        self.bitrix_client = bitrix_client
        self._webhook_service: WebhookService | None = None

    @property
    def webhook_service(self) -> WebhookService:
        """Сервис для обработки вебхуков с индивидуальной конфигурацией"""
        if self._webhook_service is None:
            self._webhook_service = WebhookService(
                **settings.web_hook_config_productsection
            )
        return self._webhook_service

    async def import_from_bitrix(
        self, start: int = 0
    ) -> tuple[list[ProductsectionDB], int, int]:
        """Импортирует все разделы из Bitrix"""
        productsections, next, total = (
            await self._fetch_bitrix_productsections(start)
        )
        results: list[ProductsectionDB] = []

        for sect in productsections:
            try:
                department = await self._create_or_update(sect)
                if department:
                    results.append(department)
            except Exception as e:
                logger.error(
                    f"Error processing department {sect.external_id}: {str(e)}"
                )

        return results, next, total

    async def _create_or_update(
        self, data: Productsection
    ) -> ProductsectionDB | None:
        """Создает или обновляет запись подразделения"""
        try:
            return await self.create(data=data)
        except ConflictException:
            return await self.update(data=data)

    async def _fetch_bitrix_productsections(
        self, start: int = 0
    ) -> tuple[list[Productsection], int, int]:
        """Получает список подразделений из Bitrix API"""
        response = await self.bitrix_client.call_api(
            "crm.productsection.list", params={"start": start}
        )
        next = response.get("next", 0)
        total = response.get("total", 0)
        if not response.get("result"):
            logger.warning("No sections received from Bitrix")
            return [], next, total

        return (
            [Productsection(**sect) for sect in response["result"]],
            next,
            total,
        )

    async def _get_bitrix_productsection(
        self, productsection_id: int
    ) -> Productsection | None:
        """Получает подразделение из Bitrix API"""
        response = await self.bitrix_client.call_api(
            "crm.productsection.get", params={"id": productsection_id}
        )
        productsection_response = response.get("result")
        if not productsection_response:
            logger.warning(f"Section {productsection_id} not found in Bitrix")
            return None
        return Productsection(**productsection_response)

    async def create_in_bitrix(
        self, data: Productsection
    ) -> Productsection | None:
        params: dict[str, Any] = {
            "fields": data.model_dump(
                by_alias=True,
                exclude_unset=True,
                exclude_none=True,
            )
        }
        response = await self.bitrix_client.call_api(
            "crm.productsection.add", params=params
        )
        if not response.get("result"):
            logger.warning("No departments received from Bitrix")
            return None
        data.external_id = int(response.get("result"))  # type:ignore[arg-type]
        return data

    async def create_in_bitrix_and_db(
        self, data: Productsection
    ) -> ProductsectionDB | None:
        productsection = await self.create_in_bitrix(data)
        if not productsection:
            return None
        return await self._create_or_update(productsection)

    async def productsection_processing(
        self, request: Request
    ) -> JSONResponse:
        """
        Основной метод обработки вебхука секции товаров
        """
        try:
            logger.info("Starting productsection processing webhook")

            webhook_payload = await self.webhook_service.process_webhook(
                request
            )

            if not webhook_payload or not webhook_payload.entity_id:
                logger.warning("Webhook received but no product ID found")
                return self._success_response(
                    "Webhook received but no product ID found",
                    webhook_payload.event if webhook_payload else "--",
                )

            productsection_id = webhook_payload.entity_id
            logger.info(f"Processing product ID: {productsection_id}")
            if webhook_payload.event == "ONCRMPRODUCTSECTIONDELETE":
                await self.set_deleted_in_bitrix(productsection_id)
                return self._success_response(
                    "Product is deleted in Bitrix", webhook_payload.event
                )
            productsection_schema = await self._get_bitrix_productsection(
                productsection_id
            )
            if productsection_schema:
                await self._create_or_update(productsection_schema)
            logger.info(
                "Successfully processed productsection ID: "
                f"{productsection_id}"
            )
            return self._success_response(
                f"Successfully processed product ID: {productsection_id}",
                webhook_payload.event,
            )
        except Exception as e:
            logger.error(
                f"Error in product_processing: {str(e)}", exc_info=True
            )
            return self._error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                f"Error in product_processing: {str(e)}",
                "error",
            )

    def _success_response(self, message: str, event: str) -> JSONResponse:
        """Успешный ответ"""
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": message,
                "event": event,
                "timestamp": time.time(),
            },
        )

    def _error_response(
        self, status_code: int, message: str, error_type: str
    ) -> JSONResponse:
        """Ответ с ошибкой"""
        return JSONResponse(
            status_code=status_code,
            content={
                "status": "error",
                "message": message,
                "error_type": error_type,
                "timestamp": time.time(),
            },
        )
