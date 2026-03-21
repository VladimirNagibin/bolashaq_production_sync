import time

from fastapi import APIRouter, Depends, File, UploadFile, status  # Request,
from fastapi.responses import JSONResponse

from core.logger import logger
from services.dependencies.dependencies_suppliers import (
    get_supplier_service,
)
from services.suppliers.supplier_services import SupplierClient

from ..schemas.response_schemas import SuccessResponse

supplier_product_router = APIRouter()


@supplier_product_router.post("/import/{config}")  # type: ignore
async def import_products(
    config: str,
    file: UploadFile = File(...),
    config_name: str | None = None,
    supplier_client: SupplierClient = Depends(get_supplier_service),
) -> SuccessResponse:
    """
    Импорт товаров из файла с заданной конфигурацией.
    """
    import_result = await supplier_client.import_products(
        config, file, config_name
    )
    return SuccessResponse(
        message="Success import",
        data=import_result,
    )


@supplier_product_router.post("/test")  # type: ignore
async def test(
    # request: Request,
    supp_client: SupplierClient = Depends(get_supplier_service),
) -> JSONResponse:
    """
    test
    """

    logger.info("test supplier service")
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
        # import uuid

        from schemas.enums import SourcesProductEnum

        # repo = supp_client.supplier_product_repo
        # su = SupplierProductCreate(
        #     external_id=12,
        #     name="str",
        #     source=SourcesProductEnum.LABSET,
        # )
        # p, d, di = await supp_client.get_supplier_product_review_data(
        #     uuid.UUID("b8025b0b-b7e6-4616-a377-c989872a101e")
        # )
        cats = await supp_client._category_cache.get(SourcesProductEnum.LABSET)
        logger.info(f"{cats}========================================")
        # logger.info(dik1)
        # logger.info(dik2)

        # res = [r.model_dump_json() for r in result]
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content="result.model_dump_json()",
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
