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
    get_lead_service,
    get_product_service,
)
from services.dependencies.dependencies_bitrix_entity import (
    get_contact_bitrix_client,
    get_deal_bitrix_client,
    get_product_bitrix_client,
)
from services.dependencies.dependencies_repo import request_context
from services.dependencies.dependencies_repo_entity import (
    get_product_image_repo,
)
from services.leads.lead_services import LeadClient
from services.product_images.product_image_repository import (
    ProductImageRepository,
)
from services.products.product_bitrix_services import ProductBitrixClient
from services.products.product_services import ProductClient

# from schemas.product_schemas import FieldValue, ProductUpdate


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
    lead_client: LeadClient = Depends(get_lead_service),
    product_bitrix_client: ProductBitrixClient = Depends(
        get_product_bitrix_client
    ),
    product_image_repo: ProductImageRepository = Depends(
        get_product_image_repo
    ),
    product_client: ProductClient = Depends(get_product_service),
) -> JSONResponse:
    external_id = 0
    try:
        ...
        # from core.logger import logger
        # from schemas.enums import SourcesProductEnum
        # from schemas.product_image_schemas import ProductImageCreate
        # product_image_create = ProductImageCreate(
        #     external_id=3,
        #     name="test77777777777",
        #     product_id=801,
        #     source=SourcesProductEnum.MATEST,
        #     detail_url="https:",
        #     image_type="MORE_IMAGE",
        # )
        # await product_image_repo.create_or_update(product_image_create)
        # image = await product_image_repo.get(3)
        # logger.info(type(image))
        # from datetime import date

        # lead_ids = await lead_client.bitrix_client.get_lead_ids_for_period(
        #     date(2025, 10, 20), date(2026, 3, 4)
        # )
        # for lead_id in lead_ids:
        #     # logger.info(f"lead_id: {lead_id}")
        #     await lead_client.import_from_bitrix(entity_id=lead_id)
        # await lead_client.send_overdue_leads_notifications()
        # leads = await lead_client.repo.get_overdue_leads()
        # for lead, idle_time in leads:
        #     logger.info(
        #         f"Лид {lead.title} Ответственный {lead.assigned_user.name} "
        #         f"Стадия {lead.status_id} лежит без продвижения {idle_time}"
        #     )
        # result_ = ""
        # await deal_client.handle_deal(257)

        # for external_id in range(2001, 2148, 2):
        #     product_update = ProductUpdate(
        #         external_id=external_id, brend=FieldValue(value="93")
        #     )
        #     await product_bitrix_client.update(product_update)
        #     print(f"UPDATED {external_id}")
        # pr = await product_bitrix_client.get(349)
        # print(product_update)

        # result_ = result[0].to_pydantic().model_dump_json()
        # result = await product_client.import_from_bitrix(801)
        # result_ = await result[0].to_pydantic()
        # print(result_)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(e), "external_id": f"{external_id}"},
        )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "result": "result_.model_dump_json()",
        },
    )
