import time

from fastapi import APIRouter, Depends, status  # Request,
from fastapi.responses import JSONResponse

from core.logger import logger
from services.dependencies.dependencies_repo import request_context
from services.dependencies.dependencies_suppliers import (
    get_supplier_service,
)
from services.suppliers.supplier_services import SupplierClient

supplier_product_router = APIRouter(
    prefix="/suppliers", dependencies=[Depends(request_context)]
)


@supplier_product_router.post("/test")  # type: ignore
async def test(
    # request: Request,
    supp_client: SupplierClient = Depends(get_supplier_service),
) -> JSONResponse:
    """
    test
    """
    logger.info("Received Bitrix24 webhook request")
    # from schemas.enums import SourcesProductEnum  # SourceKeyField,
    # from schemas.supplier_schemas import (
    #     SupplierProductCreate,
    # )
    # ImportConfigUpdate,;
    # ImportConfigCreate,;
    # SupplierCharacteristicUpdate,;
    # SupplierComplectUpdate,;
    # SupplierProductUpdate,
    try:
        repo = supp_client.supplier_product_repo
        # su = SupplierProductCreate(
        #     external_id=12,
        #     name="str",
        #     source=SourcesProductEnum.LABSET,
        # )
        result = await repo.count_by_filters(
            search="COD"
            # "1e496625-896c-47ca-aaae-491dc8a6aa74",
            # SupplierProductUpdate(name="asdfg", code="CODE")
        )
        print(result)
        # res = [r.model_dump_json() for r in result]
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=result.model_dump_json(),
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
