from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, Request, status
from jose import jwt
from jose.exceptions import JWTError
from sqladmin.authentication import AuthenticationBackend

from core.logger import logger
from core.settings import settings


class BasicAuthBackend(AuthenticationBackend):  # type: ignore
    def __init__(
        self,
        username: str = settings.USER_ADMIN,
        password: str = settings.PASS_ADMIN,
        secret_key: str = settings.SECRET_KEY,
        algorithm: str = settings.ALGORITHM,
        token_expiry_minutes: int = settings.TOKEN_EXPIRY_MINUTES,
    ):
        super().__init__(secret_key)
        self.username = username
        self.password = password
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.token_expiry_minutes = token_expiry_minutes

    async def login(self, request: Request) -> bool:
        """
        Verify user credentials and create JWT token.
        """
        try:
            form = await request.form()
            username = form.get("username")
            password = form.get("password")

            username_validate = self._convert_to_string(username)
            password_validate = self._convert_to_string(password)

            if not self._validate_credentials(
                username_validate, password_validate
            ):
                logger.warning(
                    "Failed login attempt for username: %s", username_validate
                )
                return False

            logger.info("Successful login for user: %s", username_validate)
            if not username_validate:
                return False
            token = self._create_jwt_token(username_validate)
            request.session.update({"token": token})

            return True

        except Exception as e:
            logger.error("Login error: %s", str(e))
            return False

    async def logout(self, request: Request) -> bool:
        """
        Clear user session.
        """
        try:
            request.session.clear()
            logger.info("User logged out successfully")
            return True
        except Exception as e:
            logger.error("Logout error: %s", str(e))
            return False

    async def authenticate(self, request: Request) -> bool:
        """
        Authenticate user using JWT token from session.
        """
        try:
            token = request.session.get("token")

            if not token:
                logger.debug("No token found in session")
                return False

            username = self._validate_jwt_token(token)
            if not username:
                return False

            logger.debug("Successful authentication for user: %s", username)
            return True

        except Exception as e:
            logger.error("Authentication error: %s", str(e))
            return False

    def _convert_to_string(self, value: Any) -> str | None:
        """
        Convert form value to string if it's not None.
        Handles UploadFile and other types.
        """
        if value is None:
            return None

        if hasattr(value, "read"):  # UploadFile-like object
            return None

        return str(value)

    def _validate_credentials(
        self, username: str | None, password: str | None
    ) -> bool:
        """
        Validate username and password against stored credentials.
        """
        if not username or not password:
            return False

        return username == self.username and password == self.password

    def _create_jwt_token(self, username: str) -> str:
        """
        Create JWT token for authenticated user.
        """
        try:
            now = datetime.now(timezone.utc)
            expire = now + timedelta(minutes=self.token_expiry_minutes)

            payload: dict[str, Any] = {
                "sub": username,
                "exp": expire,
                "iat": now,
            }

            return jwt.encode(  # type: ignore[no-any-return]
                payload,
                self.secret_key,
                algorithm=self.algorithm,
            )

        except Exception as e:
            logger.error("Token creation error: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not create authentication token",
            )

    def _validate_jwt_token(self, token: str) -> str | None:
        """
        Validate JWT token and return username if valid.
        """
        try:
            payload = jwt.decode(
                token, self.secret_key, algorithms=[self.algorithm]
            )

            username = payload.get("sub")
            if not username:
                logger.warning("No username in token payload")
                return None

            # Check if token is expired
            if "exp" in payload:
                exp_timestamp = payload["exp"]
                exp_datetime = datetime.fromtimestamp(
                    exp_timestamp, timezone.utc
                )
                if datetime.now(timezone.utc) > exp_datetime:
                    logger.warning("Token has expired")
                    return None

            return username if username == self.username else None

        except JWTError as e:
            logger.warning("JWT validation error: %s", str(e))
            return None
        except Exception as e:
            logger.error("Unexpected token validation error: %s", str(e))
            return None

    def get_current_user(self, request: Request) -> str | None:
        """
        Get current authenticated username from session.
        """
        try:
            token = request.session.get("token")
            if token:
                return self._validate_jwt_token(token)
            return None
        except Exception:
            return None
