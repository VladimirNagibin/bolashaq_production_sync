from fastapi import APIRouter

from .auth import auth_router
from .deals import deals_router
from .departments import departments_router
from .site_requests_handler import site_requests_router

b24_router = APIRouter()

b24_router.include_router(auth_router, prefix="", tags=["auth"])
b24_router.include_router(deals_router, prefix="", tags=["deals"])
b24_router.include_router(departments_router, prefix="", tags=["departments"])
b24_router.include_router(
    site_requests_router, prefix="", tags=["site_requests"]
)
