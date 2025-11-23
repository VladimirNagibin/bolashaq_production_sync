from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from services.bitrix_services.bitrix_api_client import BitrixAPIClient
from services.departments.department_services import DepartmentClient

from .dependencies_bitrix import get_api_client
from .dependencies_repo import get_session_context


async def get_department_service(
    bitrix_client: BitrixAPIClient = Depends(get_api_client),
    session: AsyncSession = Depends(get_session_context),
) -> DepartmentClient:
    return DepartmentClient(bitrix_client=bitrix_client, session=session)
