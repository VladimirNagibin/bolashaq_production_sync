from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from services.dependencies_entity import get_entity_bitrix_client
from services.entities.entities_bitrix_services import EntitiesBitrixClient

site_requests_router = APIRouter(prefix="/site_request")


@site_requests_router.get(
    "/site-request",
    summary="Site request handler",
    description="Request handler from the website.",
)  # type: ignore
async def site_request(
    phone: str,
    product_id: int,
    product_name: str | None = None,
    name: str | None = None,
    comment: str | None = None,
    message_id: str | None = None,
    entity_client: EntitiesBitrixClient = Depends(get_entity_bitrix_client),
) -> JSONResponse:
    try:
        result = await entity_client.handle_request_price(
            phone,
            product_id,
            product_name,
            name,
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
