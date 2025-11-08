from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BitrixWebhookAuth(BaseModel):  # type: ignore[misc]
    """
    Модель аутентификации вебхука Битрикс.

    Attributes:
        domain: Домен Битрикс24
        client_endpoint: Endpoint клиента
        server_endpoint: Endpoint сервера
        member_id: ID участника
        application_token: Токен приложения
    """

    domain: str
    client_endpoint: str
    server_endpoint: str
    member_id: str
    application_token: str

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
        extra="forbid",
    )

    @property
    def is_valid(self) -> bool:
        """Проверяет валидность данных аутентификации."""
        return all(
            [
                self.domain,
                self.client_endpoint,
                self.server_endpoint,
                self.member_id,
                self.application_token,
            ]
        )


class BitrixWebhookPayload(BaseModel):  # type: ignore[misc]
    """
    Модель полезной нагрузки вебхука Битрикс.

    Attributes:
        event: Тип события
        event_handler_id: ID обработчика события
        data: Данные события
        ts: Временная метка
        auth: Данные аутентификации
    """

    event: str
    event_handler_id: str
    data: dict[str, Any] = Field(default_factory=dict[str, Any])
    ts: str
    auth: BitrixWebhookAuth

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
    )

    @property
    def entity_id(self) -> int | None:
        """
        Извлекает ID сущности из данных.

        Returns:
            ID сущности или None если не удалось извлечь
        """
        return self._extract_numeric_id("ID")

    @property
    def entity_type_id(self) -> int | None:
        """
        Извлекает ID типа сущности из данных.

        Returns:
            ID типа сущности или None если не удалось извлечь
        """
        return self._extract_numeric_id("ENTITY_TYPE_ID")

    @property
    def fields(self) -> dict[str, Any]:
        """
        Возвращает поля сущности из данных.

        Returns:
            Словарь с полями сущности
        """
        return self.data.get("FIELDS", {})  # type: ignore[no-any-return]

    @property
    def timestamp(self) -> datetime | None:
        """
        Преобразует временную метку в datetime.

        Returns:
            Объект datetime или None если преобразование невозможно
        """
        try:
            return datetime.fromisoformat(self.ts.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None

    def _extract_numeric_id(self, field_name: str) -> int | None:
        """
        Извлекает числовой ID из данных.

        Args:
            field_name: Имя поля для извлечения

        Returns:
            Числовой ID или None
        """
        try:
            value = self.fields.get(field_name)
            if value is None:
                return None
            return int(value)
        except (ValueError, TypeError):
            return None

    def get_field(self, field_name: str, default: Any = None) -> Any:
        """
        Безопасно получает значение поля из данных.

        Args:
            field_name: Имя поля
            default: Значение по умолчанию

        Returns:
            Значение поля или default
        """
        return self.fields.get(field_name, default)

    def validate_event_type(self, expected_event: str) -> bool:
        """
        Проверяет соответствие типа события.

        Args:
            expected_event: Ожидаемый тип события

        Returns:
            True если события совпадают
        """
        return self.event == expected_event
