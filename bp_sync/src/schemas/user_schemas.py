from .base_schemas import CommonFieldMixin


class BaseUser(CommonFieldMixin):
    """Base schema of User"""

    ...


class UserCreate(BaseUser):
    """User create schema"""

    ...


class ManagerCreate:
    """Manager create schema"""

    ...
