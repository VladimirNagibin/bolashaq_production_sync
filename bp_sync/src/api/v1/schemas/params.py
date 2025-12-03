from typing import Annotated

from fastapi import Query
from pydantic import BaseModel


class CommonWebhookParams(BaseModel):  # type: ignore[misc]
    """Общие параметры для всех вебхуков сделок."""

    user_id: Annotated[
        str, Query(..., description="ID пользователя из шаблона")
    ]
    deal_id: Annotated[str, Query(..., description="ID сделки")]
