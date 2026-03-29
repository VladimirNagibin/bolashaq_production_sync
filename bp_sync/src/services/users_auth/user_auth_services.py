from datetime import datetime, timezone

from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.settings import settings
from models.user_models import User, UserAuth
from schemas.user_auth_schemas import TokenResponse

from .security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)


class UserAuthService:
    """Репозиторий авторизации."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_user_auth(
        self,
        email: str,
        password: str,
    ) -> None:

        # Ищем пользователя по email
        result = await self.session.execute(
            select(User)
            .where(User.email == email)
            .options(selectinload(User.auth))
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Not found user in Bitrix",
            )

        if user.auth:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Auth user already exist",
            )

        auth = UserAuth(
            user_id=user.id,
            hashed_password=hash_password(password),
            role="user",
        )
        self.session.add(auth)
        await self.session.commit()

    async def create_tokens(
        self, form_data: OAuth2PasswordRequestForm
    ) -> TokenResponse:

        # Ищем пользователя по email
        result = await self.session.execute(
            select(User)
            .where(User.email == form_data.username)
            .options(selectinload(User.auth))
        )
        user = result.scalar_one_or_none()

        if not user or not user.auth:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        # Проверяем пароль
        if not verify_password(form_data.password, user.auth.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        # Обновляем время последней попытки входа
        user.auth.last_login_attempt = datetime.now(timezone.utc)
        await self.session.commit()

        # Создаем токены
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "role": user.auth.role,
                "user_bitrix_id": user.external_id,
            }
        )

        refresh_token = create_refresh_token(
            data={
                "sub": str(user.id),
                "role": user.auth.role,
                "user_bitrix_id": user.external_id,
            }
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.TOKEN_EXPIRY_MINUTES * 60,
        )
