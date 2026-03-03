from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from core.logger import logger
from services.dependencies.dependencies_bitrix_entity import (
    get_entity_bitrix_client,
)
from services.entities.entities_bitrix_services import EntitiesBitrixClient

from ..deps import verify_api_key
from ..schemas.site_request import SiteRequestPayload

site_requests_router = APIRouter(prefix="/site_request")


@site_requests_router.post(
    "/site-request",
    summary="Site request handler",
    description=(
        "Process lead/deal creation from website form or parsed email."
    ),
)  # type: ignore
async def site_request(
    payload: SiteRequestPayload,  # Данные из JSON-тела запроса
    entity_client: EntitiesBitrixClient = Depends(get_entity_bitrix_client),
    verify_api_key: str = Depends(verify_api_key),
) -> JSONResponse:
    logger.info(
        f"Site request received: type={payload.type_event}, "
        f"message_id={payload.message_id}, "
        f"has_email={bool(payload.email)}, "
        f"has_phone={bool(payload.phone)}, "
        f"products_count={len(payload.products or [])}"
    )

    try:
        result = await entity_client.handle_request_price(payload)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=result,
        )
    except HTTPException:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "Deal not created",
            },
        )
