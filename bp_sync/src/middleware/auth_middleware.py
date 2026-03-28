from fastapi import HTTPException, Request, Response
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.types import ASGIApp

from api.v1.deps import get_current_user_from_cookie
from core.logger import logger
from core.settings import settings


class AuthMiddleware(BaseHTTPMiddleware):  # type: ignore[misc]
    """Middleware для автоматического обновления токенов"""

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        # Список путей, которые не требуют аутентификации
        self.excluded_paths = [
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/health",
            "/docs",
            "/openapi.json",
            "/redoc",
        ]
        self.included_paths = [
            "/api/v1/suppliers",
        ]

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Проверяем, нужно ли обрабатывать этот путь
        if not any(
            request.url.path.startswith(path) for path in self.included_paths
        ):
            return await call_next(request)

        # Создаем объект response для модификации
        response = Response()

        try:
            # Получаем токены и данные пользователя
            token_data, new_cookies = await get_current_user_from_cookie(
                request
            )

            # Сохраняем данные пользователя в request.state
            # для использования в эндпоинтах
            request.state.user = token_data

            # Передаем запрос дальше
            response = await call_next(request)

            # Устанавливаем новые cookie, если они есть
            if new_cookies:
                logger.info("Setting new cookies via middleware")
                response.set_cookie(
                    key="access_token",
                    value=new_cookies["access_token"],
                    httponly=True,
                    max_age=settings.TOKEN_EXPIRY_MINUTES * 60,
                    path="/",
                    samesite="lax",
                    # secure=False,
                )
                response.set_cookie(
                    key="refresh_token",
                    value=new_cookies["refresh_token"],
                    httponly=True,
                    max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
                    path="/",
                    samesite="lax",
                    # secure=False,
                )

            return response

        except HTTPException as e:
            # Если нет аутентификации, возвращаем ошибку или редирект
            if e.status_code == 303:
                return Response(
                    status_code=303,
                    headers={
                        "Location": (
                            e.headers["Location"]
                            if e.headers
                            else "/api/v1/auth/login"
                        )
                    },
                )
            return Response(
                status_code=e.status_code, content={"detail": e.detail}
            )
        except Exception as e:
            logger.error(f"Auth middleware error: {e}", exc_info=True)
            return Response(
                status_code=500, content={"detail": "Internal server error"}
            )
