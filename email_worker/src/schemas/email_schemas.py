from datetime import datetime
from enum import StrEnum, auto
from typing import Any

from pydantic import BaseModel


class TypeEvent(StrEnum):
    """
    Типы событий:
    REQUEST_PRICE - Запрос цены позиции
    BUY_ONE_CLICK - Покупка в один клик
    ORDER - Заказ из корзины
    """

    REQUEST_PRICE = auto()
    BUY_ONE_CLICK = auto()
    ORDER = auto()


EVENT_ROUTING: dict[str, TypeEvent] = {
    "Запрос цены на товар": TypeEvent.REQUEST_PRICE,
}


class ParsedRequest(BaseModel):  # type: ignore[misc]
    product: str
    product_id: int
    name: str | None = None
    phone: str
    comment: str | None = None
    raw_text: str


class EmailMessage(BaseModel):  # type: ignore[misc]
    message_id: str
    subject: str
    body: str
    sender: str
    recipient: str
    received_date: datetime
    attachments_count: int = 0
    headers: dict[str, Any] = {}
    parsed_body: ParsedRequest | None = None
    type_event: TypeEvent | None = None
