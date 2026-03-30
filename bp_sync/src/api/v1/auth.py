from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Request,
    Response,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates

from core.logger import logger
from core.settings import settings
from schemas.user_auth_schemas import TokenResponse
from services.dependencies.dependencies_repo import request_context
from services.dependencies.dependencies_repo_entity import (
    get_user_auth_service,
)
from services.users_auth.user_auth_services import UserAuthService

auth_router = APIRouter(dependencies=[Depends(request_context)])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
templates = Jinja2Templates(directory=f"{settings.BASE_DIR}/templates")


@auth_router.get(  # type: ignore[misc]
    "/register", response_class=HTMLResponse
)
async def register_page(request: Request) -> HTMLResponse:
    """Страница регистрации (установки пароля)."""
    return templates.TemplateResponse("register.html", {"request": request})


# Регистрация
@auth_router.post("/register")  # type: ignore[misc]
async def register(
    request: Request,
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    auth_service: UserAuthService = Depends(get_user_auth_service),
) -> RedirectResponse:
    """Обработка формы регистрации."""
    try:
        # Ваш метод создания авторизации (ищет юзера по email, создает пароль)
        await auth_service.create_user_auth(email=email, password=password)

        # Редирект обратно с флагом успеха
        return RedirectResponse(
            url="/api/v1/auth/register?success=1", status_code=303
        )

    except HTTPException as e:
        # Возвращаем ошибку обратно на форму
        return RedirectResponse(
            url=f"/api/v1/auth/register?error={e.detail}", status_code=303
        )
    except Exception as e:
        logger.error(
            f"Unexpected error during registration: {e}", exc_info=True
        )
        return RedirectResponse(
            url="/register?error=unexpected_error", status_code=303
        )


@auth_router.get("/login", response_class=HTMLResponse)  # type: ignore[misc]
async def login_page(request: Request) -> HTMLResponse:
    """Страница регистрации (установки пароля)."""
    return templates.TemplateResponse("login.html", {"request": request})


# Логин (получение токена)
@auth_router.post("/token")  # type: ignore[misc]
async def login(
    response: Response,
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: UserAuthService = Depends(get_user_auth_service),
) -> RedirectResponse:
    """
    Обработка входа.
    Получает токены от сервиса и устанавливает их в HttpOnly куки.
    """
    try:
        # 1. Вызываем ваш сервис, который проверяет пароль и генерирует токены
        token_response: TokenResponse = await auth_service.create_tokens(
            form_data
        )

        # 2. Создаем ответ-редирект (например, на главную страницу)
        response = RedirectResponse(url="/api/v1/suppliers/", status_code=303)

        # 3. Устанавливаем куки на сервере
        # Access Token (короткий)
        response.set_cookie(
            key="access_token",
            value=token_response.access_token,
            httponly=True,  # Недоступен через JS
            max_age=token_response.expires_in,
            expires=token_response.expires_in,
            path="/",
            samesite="lax",  # Защита от CSRF
        )

        # Refresh Token (длинный)
        refresh_max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        response.set_cookie(
            key="refresh_token",
            value=token_response.refresh_token,
            httponly=True,
            max_age=refresh_max_age,
            expires=refresh_max_age,
            path="/",
            samesite="lax",
        )

        return response

    except HTTPException as e:
        # При ошибке редиректим обратно на логин с параметром ошибки
        # e.detail обычно "Incorrect email or password"
        return RedirectResponse(
            url=f"/api/v1/auth/login?error={e.detail}", status_code=303
        )


@auth_router.get("/logout")  # type: ignore[misc]
async def logout() -> RedirectResponse:
    """Удаляет куки и редиректит на логин."""
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response
