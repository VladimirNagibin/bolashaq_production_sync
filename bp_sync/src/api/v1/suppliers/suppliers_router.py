from fastapi import APIRouter, Depends

from services.dependencies.dependencies_repo import request_context

from .product_review import supplier_product_review
from .supplier_products import supplier_product_router

suppliers_router = APIRouter(dependencies=[Depends(request_context)])

suppliers_router.include_router(
    supplier_product_router, prefix="", tags=["supplier_products"]
)
suppliers_router.include_router(
    supplier_product_review, prefix="", tags=["supplier_product_review"]
)
