from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from services.users.user_repository import UserRepository

from .dependencies_repo import get_session_context


async def get_user_repo(
    session: AsyncSession = Depends(get_session_context),
) -> UserRepository:
    return UserRepository(session=session)
