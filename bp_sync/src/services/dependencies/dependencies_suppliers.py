from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from services.suppliers.repositories.import_config_repo import (
    ImportConfigRepository,
)
from services.suppliers.supplier_services import SupplierClient

from .dependencies_repo import get_session_context


async def get_import_config_repo(
    session: AsyncSession = Depends(get_session_context),
) -> ImportConfigRepository:
    return ImportConfigRepository(session=session)


async def get_supplier_service(
    import_config_repo: ImportConfigRepository = Depends(
        get_import_config_repo
    ),
) -> SupplierClient:
    return SupplierClient(import_config_repo=import_config_repo)
