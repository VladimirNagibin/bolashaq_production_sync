from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from redis.asyncio import Redis

from db.redis import get_redis_session
from services.contacts.contact_bitrix_services import ContactBitrixClient
from services.dependencies_entity import get_contact_bitrix_client

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
) -> JSONResponse:

    result = await contact_client.get(21)
    print(result)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": await redis.info(),
        },
    )
