from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from services.suppliers.supplier_repository import SupplierRepository
from services.suppliers.supplier_services import SupplierClient

from .dependencies_repo import get_session_context


async def get_supplier_repo(
    session: AsyncSession = Depends(get_session_context),
) -> SupplierRepository:
    return SupplierRepository(session=session)


async def get_supplier_service(
    supplier_repo: SupplierRepository = Depends(get_supplier_repo),
) -> SupplierClient:
    return SupplierClient(supplier_repo=supplier_repo)
