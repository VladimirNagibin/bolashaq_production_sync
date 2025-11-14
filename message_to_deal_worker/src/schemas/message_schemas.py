from datetime import datetime
from typing import Any

from pydantic import UUID4, BaseModel, Field, field_validator


class RequestPrice(BaseModel):  # type: ignore[misc]
    """Схема данных запроса цены."""

    product: str | None = None
    product_id: int
    name: str | None = None
    phone: str
    comment: str | None = None
    raw_text: str | None = None
    message_id: int | None = None

    @field_validator("phone")  # type: ignore[misc]
    def validate_phone(cls, v: str) -> str:
        """Валидация номера телефона."""
        if not v or len(v.strip()) < 3:
            raise ValueError("Номер телефона не может быть пустым")
        return v.strip()


class Email(BaseModel):  # type: ignore[misc]
    """Схема данных email."""

    email_id: int | None = Field(None, alias="message_id")
    subject: str | None = None
    body: str | None = None
    sender: str | None = None
    recipient: str | None = None
    received_date: datetime | None
    attachments_count: int | None = None
    headers: dict[str, str] | None = None
    parsed_body: RequestPrice
    type_event: str | None = None


class MessageData(BaseModel):  # type: ignore[misc]
    """Основная схема сообщения."""

    message_id: UUID4 | None = None
    type_message: str = Field(alias="type")
    email: Email
    processed_at: datetime
    source: str

    @field_validator("processed_at", mode="before")  # type: ignore[misc]
    def parse_processed_at(cls, v: Any) -> datetime:
        """Парсинг даты обработки."""
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        return v  # type: ignore[no-any-return]
