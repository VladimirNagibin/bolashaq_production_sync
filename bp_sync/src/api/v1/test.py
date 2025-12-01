from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from redis.asyncio import Redis

from db.redis import get_redis_session

# from services.companies.company_services import CompanyClient
from services.contacts.contact_bitrix_services import ContactBitrixClient
from services.deals.deal_bitrix_services import DealBitrixClient
from services.deals.deal_services import DealClient
from services.dependencies.dependencies import (
    get_deal_service,
    get_product_service,
)
from services.dependencies.dependencies_bitrix_entity import (
    get_contact_bitrix_client,
    get_deal_bitrix_client,
    get_product_bitrix_client,
)
from services.dependencies.dependencies_repo import request_context
from services.products.product_bitrix_services import ProductBitrixClient
from services.products.product_services import ProductClient

# from services.users.user_bitrix_services import UserBitrixClient

# from services.users.user_services import UserClient

test_router = APIRouter(dependencies=[Depends(request_context)])


@test_router.get(
    "/",
    summary="check",
    description="Information about.",
)  # type: ignore
async def check(
    id_entity: int | str | None = None,
    redis: Redis = Depends(get_redis_session),
    contact_bitrix_client: ContactBitrixClient = Depends(
        get_contact_bitrix_client
    ),
    deal_bitrix_client: DealBitrixClient = Depends(get_deal_bitrix_client),
    deal_client: DealClient = Depends(get_deal_service),
    product_bitrix_client: ProductBitrixClient = Depends(
        get_product_bitrix_client
    ),
    product_client: ProductClient = Depends(get_product_service),
) -> JSONResponse:
    try:
        # result_ = ""
        await deal_client.handle_deal(141)
        # result_ = result[0].to_pydantic().model_dump_json()
        # result = await product_client.import_from_bitrix(801)
        # result_ = await result[0].to_pydantic()
        # print(result_)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(e)},
        )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "result": "result_.model_dump_json()",
        },
    )
