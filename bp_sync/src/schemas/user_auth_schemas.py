from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

# --- Схемы для сущности UserAuth (CRUD) ---


class UserAuthBase(BaseModel):  # type: ignore[misc]
    """Базовая схема с общими полями."""

    role: str = Field(
        default="user",
        max_length=10,
        description="Роль: admin, manager, user, guest",
    )
    is_verified: bool = Field(default=False, description="Email подтвержден")


class UserAuthCreate(UserAuthBase):
    """Схема для создания записи авторизации."""

    user_id: UUID = Field(..., description="ID пользователя из таблицы users")
    password: str = Field(
        ...,
        min_length=6,
        description="Пароль в открытом виде (будет захеширован)",
    )


class UserAuthUpdate(BaseModel):  # type: ignore[misc]
    """Схема для обновления данных авторизации."""

    password: str | None = Field(
        None, min_length=6, description="Новый пароль"
    )
    role: str | None = Field(None, max_length=10)
    is_verified: bool | None = None


class UserAuthRead(UserAuthBase):
    """Схема для чтения/ответа (пароль не возвращаем)."""

    user_id: UUID
    last_login_attempt: datetime | None = None

    class Config:
        from_attributes = True


# --- Схемы для Аутентификации (JWT) ---


class TokenResponse(BaseModel):  # type: ignore[misc]
    """Ответ при успешной выдаче токенов."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # секунд до истечения access token


class TokenPayload(BaseModel):  # type: ignore[misc]
    """Данные, зашифрованные внутри токена (Payload)."""

    sub: str  # Обычно user_id или email
    exp: int  # Timestamp истечения срока действия
    role: str | None = None  # роль для быстрой проверки прав


class LoginRequest(BaseModel):  # type: ignore[misc]
    """
    Запрос на получение токенов (Логин).
    Использует email из модели User и пароль.
    """

    username: EmailStr = Field(
        ...,
        description=(
            "Email пользователя (поле username для совместимости с OAuth2)"
        ),
    )
    password: str = Field(..., description="Пароль")


class RefreshTokenRequest(BaseModel):  # type: ignore[misc]
    """Запрос на обновление Access токена."""

    refresh_token: str = Field(..., description="Действующий Refresh токен")
