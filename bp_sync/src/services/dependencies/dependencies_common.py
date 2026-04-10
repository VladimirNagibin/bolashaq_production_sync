# from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from services.bitrix_services.bitrix_api_client import BitrixAPIClient
from services.product_images.product_image_bitrix_service import (
    ProductImageService,
)
from services.product_images.product_image_repository import (
    ProductImageRepository,
)
from services.product_images.product_image_services import ProductImageClient
from services.products.product_bitrix_services import ProductBitrixClient
from services.products.product_data_raw import ProductRawDataService
from services.products.product_repository import ProductRepository
from services.users.user_bitrix_services import UserBitrixClient
from services.users.user_repository import UserRepository
from services.users.user_services import UserClient

from ..products.product_services import ProductClient
from ..productsections.productsection_services import ProductsectionClient
from .dependencies_bitrix import get_api_client
from .dependencies_bitrix_entity import (
    get_product_bitrix_client,
    get_user_bitrix_client,
)
from .dependencies_repo import get_session_context
from .dependencies_repo_entity import (
    get_product_image_repo,
    get_product_repo,
    get_user_repo,
)


async def get_product_raw_data_service(
    bitrix_client: BitrixAPIClient = Depends(get_api_client),
) -> ProductRawDataService:
    return ProductRawDataService(bitrix_client=bitrix_client)


async def get_product_image_bitrix_service(
    product_data_raw: ProductRawDataService = Depends(
        get_product_raw_data_service
    ),
) -> ProductImageService:
    return ProductImageService(product_data_raw)


async def get_productsection_service(
    bitrix_client: BitrixAPIClient = Depends(get_api_client),
    session: AsyncSession = Depends(get_session_context),
) -> ProductsectionClient:
    return ProductsectionClient(bitrix_client=bitrix_client, session=session)


async def get_product_image_service(
    product_image_bitrix_client: ProductImageService = Depends(
        get_product_image_bitrix_service
    ),
    product_image_repo: ProductImageRepository = Depends(
        get_product_image_repo
    ),
) -> ProductImageClient:
    return ProductImageClient(
        product_image_bitrix_client,
        product_image_repo,
    )


async def get_user_service(
    user_bitrix_client: UserBitrixClient = Depends(get_user_bitrix_client),
    user_repo: UserRepository = Depends(get_user_repo),
) -> UserClient:
    return UserClient(
        user_bitrix_client=user_bitrix_client,
        user_repo=user_repo,
    )


async def get_product_service(
    product_bitrix_client: ProductBitrixClient = Depends(
        get_product_bitrix_client
    ),
    product_repo: ProductRepository = Depends(get_product_repo),
    image_client: ProductImageClient = Depends(get_product_image_service),
    user_service: UserClient = Depends(get_user_service),
) -> ProductClient:
    return ProductClient(
        product_bitrix_client,
        product_repo,
        image_client,
        user_client=user_service,
    )


# async def get_product_service(
#     product_bitrix_client: ProductBitrixClient = Depends(
#         get_product_bitrix_client
#     ),
#     product_repo: ProductRepository = Depends(get_product_repo),
#     image_client: ProductImageClient = Depends(get_product_image_service),
#     user_service: UserClient = Depends(get_user_service),
# ) -> AsyncGenerator[ProductClient, None]:
#     """Зависимость для сервиса товаров"""
#     service = ProductClient(
#         product_bitrix_client,
#         product_repo,
#         image_client,
#         user_client=user_service,
#     )
#     yield service


# async def get_productsection_service(
#     bitrix_client=Depends(get_product_bitrix_client),
#     # Исправьте на правильный клиент
#     session: AsyncSession = Depends(get_session_context),
# ) -> AsyncGenerator[ProductsectionClient, None]:
#     """Зависимость для сервиса разделов товаров"""
#     from ..productsections.productsection_services import (
#         ProductsectionClient
#     )
#     service = ProductsectionClient(
#         bitrix_client=bitrix_client, session=session
#     )
#     yield service
