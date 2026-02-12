from fastapi import APIRouter

from .supplier_products import supplier_product_router

suppliers_router = APIRouter()

suppliers_router.include_router(
    supplier_product_router, prefix="", tags=["supplier_products"]
)
