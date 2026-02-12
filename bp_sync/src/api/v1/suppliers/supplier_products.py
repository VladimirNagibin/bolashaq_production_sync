import time

from fastapi import APIRouter, Depends, status  # Request,
from fastapi.responses import JSONResponse

from core.logger import logger
from services.dependencies.dependencies_repo import request_context
from services.dependencies.dependencies_suppliers import (
    get_supplier_repo,
    get_supplier_service,
)
from services.suppliers.supplier_repository import SupplierRepository
from services.suppliers.supplier_services import SupplierClient

supplier_product_router = APIRouter(
    prefix="/suppliers", dependencies=[Depends(request_context)]
)


@supplier_product_router.post("/test")  # type: ignore
async def test(
    # request: Request,
    supp_repo: SupplierRepository = Depends(get_supplier_repo),
    supp_client: SupplierClient = Depends(get_supplier_service),
) -> JSONResponse:
    """
    test
    """
    logger.info("Received Bitrix24 webhook request")
    from schemas.enums import SourcesProductEnum

    try:
        result = await supp_client.get_supplier_config(
            source=SourcesProductEnum.MATEST,
            config_name="main",
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=result.model_dump_json() if result else "NULL",
        )
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "fail",
                "message": "processing failed",
                "error": str(e),
                "timestamp": time.time(),
            },
        )
