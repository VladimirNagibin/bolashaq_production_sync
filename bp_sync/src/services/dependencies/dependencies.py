from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from services.bitrix_services.bitrix_api_client import BitrixAPIClient
from services.companies.company_bitrix_services import CompanyBitrixClient
from services.companies.company_repository import CompanyRepository
from services.companies.company_services import CompanyClient
from services.contacts.contact_bitrix_services import ContactBitrixClient
from services.contacts.contact_repository import ContactRepository
from services.contacts.contact_services import ContactClient
from services.deals.deal_bitrix_services import DealBitrixClient
from services.deals.deal_lock_service import LockService
from services.deals.deal_repository import DealRepository
from services.deals.deal_services import DealClient
from services.departments.department_services import DepartmentClient
from services.entities.entities_bitrix_services import EntitiesBitrixClient
from services.entities.entities_services import EntityClient
from services.leads.lead_bitrix_services import LeadBitrixClient
from services.leads.lead_repository import LeadRepository
from services.leads.lead_services import LeadClient
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
from services.products.product_services import ProductClient
from services.productsections.productsection_services import (
    ProductsectionClient,
)
from services.suppliers.supplier_services import SupplierClient
from services.timeline_comments.timeline_comment_bitrix_services import (
    TimeLineCommentBitrixClient,
)
from services.timeline_comments.timeline_comment_repository import (
    TimelineCommentRepository,
)
from services.timeline_comments.timeline_comment_services import (
    TimelineCommentClient,
)
from services.users.user_bitrix_services import UserBitrixClient
from services.users.user_repository import UserRepository
from services.users.user_services import UserClient

from .dependencies_bitrix import get_api_client, get_redis
from .dependencies_bitrix_entity import (
    get_company_bitrix_client,
    get_contact_bitrix_client,
    get_deal_bitrix_client,
    get_entity_bitrix_client,
    get_lead_bitrix_client,
    get_product_bitrix_client,
    get_timeline_comment_bitrix_client,
    get_user_bitrix_client,
)
from .dependencies_repo import get_session_context
from .dependencies_repo_entity import (
    get_company_repo,
    get_contact_repo,
    get_deal_repo,
    get_lead_repo,
    get_product_image_repo,
    get_product_repo,
    get_timeline_comment_repo,
    get_user_repo,
)
from .dependencies_suppliers import get_supplier_service


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


async def get_department_service(
    bitrix_client: BitrixAPIClient = Depends(get_api_client),
    session: AsyncSession = Depends(get_session_context),
) -> DepartmentClient:
    return DepartmentClient(bitrix_client=bitrix_client, session=session)


async def get_productsection_service(
    bitrix_client: BitrixAPIClient = Depends(get_api_client),
    session: AsyncSession = Depends(get_session_context),
) -> ProductsectionClient:
    return ProductsectionClient(bitrix_client=bitrix_client, session=session)


async def get_user_service(
    user_bitrix_client: UserBitrixClient = Depends(get_user_bitrix_client),
    user_repo: UserRepository = Depends(get_user_repo),
) -> UserClient:
    return UserClient(
        user_bitrix_client=user_bitrix_client,
        user_repo=user_repo,
    )


async def get_contact_service(
    contact_bitrix_client: ContactBitrixClient = Depends(
        get_contact_bitrix_client
    ),
    contact_repo: ContactRepository = Depends(get_contact_repo),
    user_service: UserClient = Depends(get_user_service),
) -> ContactClient:
    return ContactClient(
        contact_bitrix_client,
        contact_repo,
        user_client=user_service,
    )


async def get_company_service(
    company_bitrix_client: CompanyBitrixClient = Depends(
        get_company_bitrix_client
    ),
    company_repo: CompanyRepository = Depends(get_company_repo),
    user_service: UserClient = Depends(get_user_service),
) -> CompanyClient:
    return CompanyClient(
        company_bitrix_client,
        company_repo,
        user_client=user_service,
    )


async def get_lead_service(
    lead_bitrix_client: LeadBitrixClient = Depends(get_lead_bitrix_client),
    lead_repo: LeadRepository = Depends(get_lead_repo),
    user_service: UserClient = Depends(get_user_service),
) -> LeadClient:
    return LeadClient(
        lead_bitrix_client,
        lead_repo,
        user_client=user_service,
    )


async def get_timeline_comment_service(
    timeline_comment_bitrix_client: TimeLineCommentBitrixClient = Depends(
        get_timeline_comment_bitrix_client
    ),
    timeline_comment_repo: TimelineCommentRepository = Depends(
        get_timeline_comment_repo
    ),
    user_service: UserClient = Depends(get_user_service),
) -> TimelineCommentClient:
    return TimelineCommentClient(
        timeline_comment_bitrix_client,
        timeline_comment_repo,
        user_client=user_service,
    )


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


async def get_lock_service(redis: Redis = Depends(get_redis)) -> LockService:
    return LockService(redis)


async def get_deal_service(
    deal_bitrix_client: DealBitrixClient = Depends(get_deal_bitrix_client),
    deal_repo: DealRepository = Depends(get_deal_repo),
    user_service: UserClient = Depends(get_user_service),
    lock_service: LockService = Depends(get_lock_service),
    contact_service: ContactClient = Depends(get_contact_service),
    company_service: CompanyClient = Depends(get_company_service),
    lead_service: LeadClient = Depends(get_lead_service),
    timeline_comment_service: TimelineCommentClient = Depends(
        get_timeline_comment_service
    ),
    product_service: ProductClient = Depends(get_product_service),
) -> DealClient:
    return DealClient(
        deal_bitrix_client,
        deal_repo,
        lock_service=lock_service,
        user_client=user_service,
        contact_client=contact_service,
        company_client=company_service,
        lead_client=lead_service,
        timeline_comment_client=timeline_comment_service,
        product_client=product_service,
    )


async def get_entity_service(
    bitrix_client: EntitiesBitrixClient = Depends(get_entity_bitrix_client),
    supplier_client: SupplierClient = Depends(get_supplier_service),
) -> EntityClient:
    return EntityClient(
        bitrix_client=bitrix_client, supplier_client=supplier_client
    )
