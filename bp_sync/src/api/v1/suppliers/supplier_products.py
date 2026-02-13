import time

from fastapi import APIRouter, Depends, status  # Request,
from fastapi.responses import JSONResponse

from core.logger import logger
from services.dependencies.dependencies_repo import request_context
from services.dependencies.dependencies_suppliers import (
    get_import_config_repo,
    get_supplier_service,
)
from services.suppliers.repositories.import_config_repo import (
    ImportConfigRepository,
)
from services.suppliers.supplier_services import SupplierClient

supplier_product_router = APIRouter(
    prefix="/suppliers", dependencies=[Depends(request_context)]
)


@supplier_product_router.post("/test")  # type: ignore
async def test(
    # request: Request,
    supp_client: SupplierClient = Depends(get_supplier_service),
    import_config_repo: ImportConfigRepository = Depends(
        get_import_config_repo
    ),
) -> JSONResponse:
    """
    test
    """
    logger.info("Received Bitrix24 webhook request")
    # from schemas.enums import SourceKeyField, SourcesProductEnum
    # from schemas.supplier_schemas import (  # ImportConfigUpdate,
    #     ImportColumnMappingUpdate,
    #     ImportConfigCreate,
    # )

    try:
        # result = await supp_client.get_supplier_config(
        #     source=SourcesProductEnum.MATEST,
        #     config_name="main",
        # )
        # imp = ImportConfigCreate(
        #     source=SourcesProductEnum.MATEST,
        #     config_name="main999",
        #     source_key_field=SourceKeyField.CODE,
        # )
        # mapps = [
        #     ImportColumnMappingUpdate(
        #         target_field="asd",
        #         source_column_name="None",
        #         source_column_index=5,
        #     ),
        #     ImportColumnMappingUpdate(
        #         target_field="asd555",
        #         source_column_name="None555",
        #         source_column_index=58,
        #     ),
        # ]
        result = await import_config_repo.get_all(
            # "73a424d6-d354-4a85-a238-e50e97acd65c",
        )
        # print(result.column_mappings)
        # res = [r.model_dump_json() for r in result]
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=[resul.model_dump_json() for resul in result],
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
