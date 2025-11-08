from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from redis.asyncio import Redis

from db.redis import get_redis_session

test_router = APIRouter()  # dependencies=[Depends(request_context)])


@test_router.get(
    "/",
    summary="check",
    description="Information about.",
)  # type: ignore
async def check(
    id_entity: int | str | None = None,
    redis: Redis = Depends(get_redis_session),
) -> JSONResponse:

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": await redis.info(),
        },
    )
