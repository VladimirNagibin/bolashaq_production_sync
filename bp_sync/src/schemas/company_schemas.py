from .base_schemas import (
    AddressMixin,
    BaseCreateSchema,
    BaseUpdateSchema,
    HasCommunicationCreateMixin,
    HasCommunicationUpdateMixin,
)


class BaseCompany:
    """Base schema of Contact"""

    ...


class CompanyCreate(
    BaseCreateSchema, BaseCompany, AddressMixin, HasCommunicationCreateMixin
):
    """Contact create schema"""

    ...


class CompanyUpdate(
    BaseUpdateSchema, BaseCompany, AddressMixin, HasCommunicationUpdateMixin
):
    """Contact create schema"""

    ...
