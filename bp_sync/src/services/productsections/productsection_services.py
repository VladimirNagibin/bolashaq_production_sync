from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import logger
from models.productsection_models import Productsection as ProductsectionDB
from schemas.productsection_schemas import Productsection

from ..base_repositories.base_repository import BaseRepository
from ..bitrix_services.bitrix_api_client import BitrixAPIClient
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
