from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from core.logger import logger
from ..schemas.site_request import SiteRequestPayload
from services.dependencies.dependencies_bitrix_entity import (
    get_entity_bitrix_client,
)
from services.entities.entities_bitrix_services import EntitiesBitrixClient

from ..deps import verify_api_key

site_requests_router = APIRouter(prefix="/site_request")


@site_requests_router.get(
    "/site-request-handler",
    summary="Site request handler",
    description="Request handler from the website.",
)  # type: ignore
async def site_request_handler(
    type_event: str,
    phone: str | None = None,
    email: str | None = None,
    product_id: int | None = None,
    product_name: str | None = None,
    name: str | None = None,
    bin_company: str | None = None,
    comment: str | None = None,
    message_id: str | None = None,
    products: list[dict[str, Any]] | None = None,
    entity_client: EntitiesBitrixClient = Depends(get_entity_bitrix_client),
    verify_api_key: str = Depends(verify_api_key),
) -> JSONResponse:
    logger.info(
        f"{type_event}::{phone}::{email}::{product_id}::{product_name}::{name}::{bin_company}::{comment}::{message_id}::{products}"
    )
    try:
        result = await entity_client.handle_request_price_(
            phone,
            product_id,
            product_name,
            name,
            bin_company,
            comment,
            message_id,
        )
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


@site_requests_router.post(
    "/site-request",
    summary="Site request handler",
    description="Process lead/deal creation from website form or parsed email.",
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
        result = await entity_client.handle_request_price(
            payload
        )
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
