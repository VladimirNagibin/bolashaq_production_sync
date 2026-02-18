from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from services.products.product_services import ProductClient
from services.suppliers.file_import_service import FileImportService
from services.suppliers.repositories.import_config_repo import (
    ImportConfigRepository,
)
from services.suppliers.repositories.supplier_product_repo import (
    SupplierProductRepository,
)
from services.suppliers.supplier_services import SupplierClient

from .dependencies import get_product_service
from .dependencies_repo import get_session_context


async def get_import_config_repo(
    session: AsyncSession = Depends(get_session_context),
) -> ImportConfigRepository:
    return ImportConfigRepository(session=session)


async def get_supplier_product_repo(
    session: AsyncSession = Depends(get_session_context),
) -> SupplierProductRepository:
    return SupplierProductRepository(session=session)


async def get_file_import_service(
    supplier_product_repo: SupplierProductRepository = Depends(
        get_supplier_product_repo
    ),
    product_client: ProductClient = Depends(get_product_service),
) -> FileImportService:
    return FileImportService(supplier_product_repo, product_client)


async def get_supplier_service(
    import_config_repo: ImportConfigRepository = Depends(
        get_import_config_repo
    ),
    supplier_product_repo: SupplierProductRepository = Depends(
        get_supplier_product_repo
    ),
    file_import_service: FileImportService = Depends(get_file_import_service),
) -> SupplierClient:
    return SupplierClient(
        import_config_repo=import_config_repo,
        supplier_product_repo=supplier_product_repo,
        file_import_service=file_import_service,
    )
