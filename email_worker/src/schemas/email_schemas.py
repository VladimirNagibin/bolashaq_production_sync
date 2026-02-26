from datetime import datetime
from enum import StrEnum, auto
from typing import Any

from pydantic import BaseModel


class TypeEvent(StrEnum):
    """
    Типы событий:
    REQUEST_PRICE - Запрос КП Матест
    BUY_ONE_CLICK - Покупка в один клик Матест
    ORDER - Заказ из корзины Матест
    REQUEST_PRICE_LABSET - Запрос цен от Лабсет
    """

    REQUEST_PRICE = auto()
    BUY_ONE_CLICK = auto()
    ORDER = auto()
    REQUEST_PRICE_LABSET = auto()


EVENT_ROUTING: dict[str, TypeEvent] = {
    ("Запрос цены на товар", "no-reply@matest.kz"): TypeEvent.REQUEST_PRICE,
    ("Запрос цены: Matest Казахстан", "sales@matest.kz"): TypeEvent.ORDER,
    ("Лабсет: новый запрос КП", '"labset.su" <no-reply@labset.su>'): TypeEvent.REQUEST_PRICE_LABSET,
}


class ParsedProduct(BaseModel):  # type: ignore[misc]
    product: str
    product_id: int | None = None
    product_code: str | None = None
    article: str | None = None
    price: float | None = None
    quantity: int | None = None


class ParsedRequest(BaseModel):  # type: ignore[misc]
    product: str | None = None
    product_id: int | None = None
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    bin_company: str | None = None
    comment: str | None = None
    raw_text: str
    products: list[ParsedProduct] | None = None


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
