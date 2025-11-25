from typing import AsyncGenerator  # , Callable

from fastapi import Depends

from ..bitrix_services.bitrix_api_client import BitrixAPIClient
from ..companies.company_bitrix_services import CompanyBitrixClient
from ..contacts.contact_bitrix_services import ContactBitrixClient
from ..deals.deal_bitrix_services import DealBitrixClient
from ..entities.entities_bitrix_services import EntitiesBitrixClient
from ..users.user_bitrix_services import UserBitrixClient
from .dependencies_bitrix import dependency_container, get_api_client


async def get_deal_bitrix_client() -> AsyncGenerator[DealBitrixClient, None]:
    """Зависимость для клиента сделок"""
    client = await dependency_container.get_entity_client(DealBitrixClient)
    yield client


async def get_contact_bitrix_client() -> (
    AsyncGenerator[ContactBitrixClient, None]
):
    """Зависимость для клиента сделок"""
    client = await dependency_container.get_entity_client(ContactBitrixClient)
    yield client


async def get_company_bitrix_client() -> (
    AsyncGenerator[CompanyBitrixClient, None]
):
    """Зависимость для клиента сделок"""
    client = await dependency_container.get_entity_client(CompanyBitrixClient)
    yield client


async def get_user_bitrix_client(
    api_client: BitrixAPIClient = Depends(get_api_client),
) -> AsyncGenerator[UserBitrixClient, None]:
    """Зависимость для клиента пользователей"""
    yield UserBitrixClient(api_client)


async def get_entity_bitrix_client(
    deal_client: DealBitrixClient = Depends(get_deal_bitrix_client),
    contact_client: ContactBitrixClient = Depends(get_contact_bitrix_client),
    company_client: CompanyBitrixClient = Depends(get_company_bitrix_client),
    user_client: UserBitrixClient = Depends(get_user_bitrix_client),
) -> AsyncGenerator[EntitiesBitrixClient, None]:
    """Зависимость для агрегированного клиента сущностей"""
    entity_client = EntitiesBitrixClient(
        contact_bitrix_client=contact_client,
        company_bitrix_client=company_client,
        deal_bitrix_client=deal_client,
        user_bitrix_client=user_client,
    )
    yield entity_client


# def get_deal_client_() -> AsyncGenerator[DealBitrixClient, None]:
#    """Зависимость для клиента сделок"""
#    # Явно указываем тип
#    entity_client_func: Callable[
#        [], AsyncGenerator[DealBitrixClient, None]
#    ] = get_entity_client(DealBitrixClient)
#    return entity_client_func()
