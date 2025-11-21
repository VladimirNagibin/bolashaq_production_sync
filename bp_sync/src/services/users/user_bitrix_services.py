from fastapi import HTTPException, status

from core.logger import logger
from schemas.user_schemas import UserCreate

from ..bitrix_services.bitrix_api_client import BitrixAPIClient
from ..decorators import handle_bitrix_errors


class UserBitrixClient:
    entity_name = "user"

    def __init__(self, bitrix_client: BitrixAPIClient):
        self.bitrix_client = bitrix_client

    @handle_bitrix_errors()
    async def get(
        self, entity_id: int, entity_type_id: int | None = None
    ) -> UserCreate:
        """Получение сущности по ID"""
        logger.debug(f"Fetching {self.entity_name} ID={entity_id}")
        response = await self.bitrix_client.call_api(
            f"{self.entity_name}.get", {"id": entity_id}
        )
        if not (entity_data := response.get("result")):
            logger.warning(
                f"{self.entity_name.capitalize()} not found: ID={entity_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.entity_name.capitalize()} not found",
            )
        return UserCreate(**entity_data[0])
