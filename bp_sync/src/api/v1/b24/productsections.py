from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from services.dependencies.dependencies import get_productsection_service
from services.dependencies.dependencies_repo import request_context
from services.productsections.productsection_services import (
    ProductsectionClient,
)

productsections_router = APIRouter(
    prefix="/productsections", dependencies=[Depends(request_context)]
)


@productsections_router.get(
    "/update-productsections",
    summary="Update productsections",
    description="Update productsections from Bitrix24",
)  # type: ignore
async def update_productsections(
    start: int = 0,
    productsection_client: ProductsectionClient = Depends(
        get_productsection_service
    ),
) -> JSONResponse:
    result, next, total = await productsection_client.import_from_bitrix(start)
    # from core.logger import logger
    # from schemas.productsection_schemas import Productsection

    # prod = Productsection(name="TEST777", catalog_id=25)
    # cat = await productsection_client.create_in_bitrix(prod)
    # logger.info(cat)
    return JSONResponse(
        status_code=200,
        content={
            "updated": len(result),
            "next": next,
            "total": total,
            # "res": "res"
        },
    )
