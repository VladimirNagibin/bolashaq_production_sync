from datetime import datetime
from typing import Any

from pydantic import BaseModel


class EmailMessage(BaseModel):  # type: ignore[misc]
    message_id: str
    subject: str
    body: str
    sender: str
    recipient: str
    received_date: datetime
    attachments_count: int = 0
    headers: dict[str, Any] = {}
