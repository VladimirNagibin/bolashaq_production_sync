# from typing import TYPE_CHECKING

from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from db.redis import get_redis
from services.products.product_services import ProductClient
from services.productsections.productsection_services import (
    ProductsectionClient,
)
from services.suppliers.file_import_service import FileImportService
from services.suppliers.repositories.import_config_repo import (
    ImportConfigRepository,
)
from services.suppliers.repositories.supplier_product_repo import (
    SupplierProductRepository,
)
from services.suppliers.supplier_services import SupplierClient

from .dependencies_common import (
    get_product_service,
    get_productsection_service,
)
from .dependencies_repo import get_session_context

# if TYPE_CHECKING:
#     from services.products.product_services import ProductClient
#     from services.productsections.productsection_services import (
#         ProductsectionClient,
#     )


async def get_import_config_repo(
    session: AsyncSession = Depends(get_session_context),
) -> ImportConfigRepository:
    return ImportConfigRepository(session=session)


async def get_supplier_product_repo(
    session: AsyncSession = Depends(get_session_context),
) -> SupplierProductRepository:
    return SupplierProductRepository(session=session)


# async def get_product_service_lazy(
#     service: "ProductClient" = Depends(
#         ".dependencies.get_product_service"
#     )
# ) -> "ProductClient":
#     """Ленивая загрузка зависимости product_service"""
#     # from .dependencies import get_product_service  # Локальный импорт
#     # return await get_product_service()
#     return service


# async def get_productsection_service_lazy(
#     service: "ProductsectionClient" = Depends(
#         ".dependencies.get_productsection_service"
#     )
# ) -> "ProductsectionClient":
#     """Ленивая загрузка зависимости productsection_service"""
#     # from .dependencies import get_productsection_service
#     # Локальный импорт
#     # return await get_productsection_service()
#     return service


async def get_file_import_service(
    supplier_product_repo: SupplierProductRepository = Depends(
        get_supplier_product_repo
    ),
    product_client: "ProductClient" = Depends(get_product_service),
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
    redis_client: Redis = Depends(get_redis),
    product_client: "ProductClient" = Depends(get_product_service),
    product_section_client: "ProductsectionClient" = Depends(
        get_productsection_service
    ),
) -> SupplierClient:
    return SupplierClient(
        import_config_repo=import_config_repo,
        supplier_product_repo=supplier_product_repo,
        file_import_service=file_import_service,
        redis_client=redis_client,
        product_client=product_client,
        product_section_client=product_section_client,
    )
