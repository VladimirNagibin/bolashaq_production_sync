from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from services.bitrix_services.bitrix_api_client import BitrixAPIClient
from services.departments.department_services import DepartmentClient
from services.users.user_bitrix_services import UserBitrixClient
from services.users.user_repository import UserRepository
from services.users.user_services import UserClient

from .dependencies_bitrix import get_api_client
from .dependencies_bitrix_entity import get_user_bitrix_client
from .dependencies_repo import get_session_context
from .dependencies_repo_entity import get_user_repo


async def get_department_service(
    bitrix_client: BitrixAPIClient = Depends(get_api_client),
    session: AsyncSession = Depends(get_session_context),
) -> DepartmentClient:
    return DepartmentClient(bitrix_client=bitrix_client, session=session)


async def get_user_service(
    user_bitrix_client: UserBitrixClient = Depends(get_user_bitrix_client),
    user_repo: UserRepository = Depends(get_user_repo),
) -> UserClient:
    return UserClient(
        user_bitrix_client=user_bitrix_client,
        user_repo=user_repo,
    )
