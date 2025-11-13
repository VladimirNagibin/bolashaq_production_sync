from .base_schemas import (
    AddressMixin,
    BaseCreateSchema,
    BaseUpdateSchema,
    HasCommunicationCreateMixin,
    HasCommunicationUpdateMixin,
)


class BaseContact:
    """Base schema of Contact"""

    ...


class ContactCreate(
    BaseCreateSchema, BaseContact, AddressMixin, HasCommunicationCreateMixin
):
    """Contact create schema"""

    ...


class ContactUpdate(
    BaseUpdateSchema, BaseContact, AddressMixin, HasCommunicationUpdateMixin
):
    """Contact create schema"""

    ...
