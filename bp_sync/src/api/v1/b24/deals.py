from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from services.deals.deal_bitrix_services import DealBitrixClient
from services.dependencies_bitrix_entity import get_deal_bitrix_client

deals_router = APIRouter(prefix="/deals")


@deals_router.get(
    "/test-deals",
    summary="Test deals",
    description="Testing deals.",
)  # type: ignore
async def test_deals(
    deal_client: DealBitrixClient = Depends(get_deal_bitrix_client),
) -> JSONResponse:
    try:
        result = await deal_client.handle_request_price("11111111", 35)

    except Exception as e:
        result = e
    print(result)
    return JSONResponse(content="result")
