from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from services.companies.company_repository import CompanyRepository
from services.contacts.contact_repository import ContactRepository
from services.deals.deal_repository import DealRepository
from services.leads.lead_repository import LeadRepository
from services.products.product_repository import ProductRepository
from services.timeline_comments.timeline_comment_repository import (
    TimelineCommentRepository,
)
from services.users.user_repository import UserRepository

from .dependencies_repo import get_session_context


async def get_user_repo(
    session: AsyncSession = Depends(get_session_context),
) -> UserRepository:
    return UserRepository(session=session)


async def get_contact_repo(
    session: AsyncSession = Depends(get_session_context),
) -> ContactRepository:
    return ContactRepository(session=session)


async def get_company_repo(
    session: AsyncSession = Depends(get_session_context),
) -> CompanyRepository:
    return CompanyRepository(session=session)


async def get_lead_repo(
    session: AsyncSession = Depends(get_session_context),
) -> LeadRepository:
    return LeadRepository(session=session)


async def get_deal_repo(
    session: AsyncSession = Depends(get_session_context),
) -> DealRepository:
    return DealRepository(session=session)


async def get_timeline_comment_repo(
    session: AsyncSession = Depends(get_session_context),
) -> TimelineCommentRepository:
    return TimelineCommentRepository(session=session)


async def get_product_repo(
    session: AsyncSession = Depends(get_session_context),
) -> ProductRepository:
    return ProductRepository(session=session)
