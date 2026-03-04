from fastapi import APIRouter

health_router = APIRouter()


@health_router.get(
    "/health",
    summary="check health",
    description="Check health.",
)  # type: ignore
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}
