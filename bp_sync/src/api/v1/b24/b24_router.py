from fastapi import APIRouter

from .auth import auth_router

b24_router = APIRouter()

b24_router.include_router(auth_router, prefix="", tags=["auth"])
