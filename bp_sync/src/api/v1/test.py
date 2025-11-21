from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from redis.asyncio import Redis

from db.redis import get_redis_session
from services.contacts.contact_bitrix_services import ContactBitrixClient
from services.deals.deal_bitrix_services import DealBitrixClient
from services.dependencies_entity import (
    get_contact_bitrix_client,
    get_deal_bitrix_client,
    get_user_bitrix_client,
)
from services.users.user_bitrix_services import UserBitrixClient

test_router = APIRouter()  # dependencies=[Depends(request_context)])


@test_router.get(
    "/",
    summary="check",
    description="Information about.",
)  # type: ignore
async def check(
    id_entity: int | str | None = None,
    redis: Redis = Depends(get_redis_session),
    contact_client: ContactBitrixClient = Depends(get_contact_bitrix_client),
    deal_client: DealBitrixClient = Depends(get_deal_bitrix_client),
    user_client: UserBitrixClient = Depends(get_user_bitrix_client),
) -> JSONResponse:
    try:
        result = await deal_client.get(141)
        result_ = result.model_dump_json()
    except Exception as e:
        result_ = str(e)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "result": result_,
        },
    )
