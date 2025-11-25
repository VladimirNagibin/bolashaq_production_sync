from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import logger
from models.department_models import Department as DepartDB
from schemas.department_schemas import Department

from ..base_repositories.base_repository import BaseRepository
from ..bitrix_services.bitrix_api_client import BitrixAPIClient
from ..exceptions import ConflictException


class DepartmentClient(BaseRepository[DepartDB, Department, Department, int]):

    model = DepartDB

    def __init__(
        self,
        bitrix_client: BitrixAPIClient,
        session: AsyncSession,
    ) -> None:
        super().__init__(session)
        self.bitrix_client = bitrix_client

    async def import_from_bitrix(self) -> list[DepartDB]:
        """Импортирует все подразделения из Bitrix"""
        departments = await self._fetch_bitrix_departments()
        results: list[DepartDB] = []

        for dept in departments:
            try:
                department = await self._create_or_update(dept)
                if department:
                    results.append(department)
            except Exception as e:
                logger.error(
                    f"Error processing department {dept.external_id}: {str(e)}"
                )

        return results

    async def _create_or_update(self, data: Department) -> DepartDB | None:
        """Создает или обновляет запись подразделения"""
        try:
            return await self.create(data=data)
        except ConflictException:
            return await self.update(data=data)

    async def _fetch_bitrix_departments(self) -> list[Department]:
        """Получает список подразделений из Bitrix API"""
        response = await self.bitrix_client.call_api("department.get")

        if not response.get("result"):
            logger.warning("No departments received from Bitrix")
            return []

        return [Department(**dept) for dept in response["result"]]
