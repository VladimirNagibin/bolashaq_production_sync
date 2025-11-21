from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from schemas.company_schemas import CompanyCreate
from schemas.enums import EntityType

from .bases import CommunicationIntIdEntity
from .deal_models import Deal


class Company(CommunicationIntIdEntity):
    """
    Компании
    """

    __tablename__ = "companies"
    _schema_class = CompanyCreate

    @property
    def entity_type(self) -> EntityType:
        return EntityType.COMPANY

    # @property
    # def entity_type1(self) -> str:
    #    return "Company"

    @property
    def tablename(self) -> str:
        return self.__tablename__

    def __str__(self) -> str:
        return str(self.title)

    # Идентификаторы и основные данные
    title: Mapped[str] = mapped_column(
        comment="Название сделки"
    )  # TITLE : Название
    origin_version: Mapped[str | None] = mapped_column(
        comment="Версия данных о контакте во внешней системе"
    )  # ORIGIN_VERSION : Версия данных о контакте во внешней системе
    employees: Mapped[str | None] = mapped_column(
        comment="Численность сотрудников"
    )  # EMPLOYEES : Численность сотрудников

    # Финансы
    banking_details: Mapped[str | None] = mapped_column(
        comment="Банковские реквизиты"
    )  # BANKING_DETAILS : Банковские реквизиты
    revenue: Mapped[float] = mapped_column(
        default=0.0, comment="Годовой оборот"
    )  # REVENUE : Годовой оборот

    # Адреса
    address_legal: Mapped[str | None] = mapped_column(
        comment="Юридический адрес"
    )  # ADDRESS_LEGAL : Юридический адрес

    # Статусы и флаги
    is_my_company: Mapped[bool] = mapped_column(
        default=False, comment="Моя компания"
    )  # IS_MY_COMPANY : Моя компания

    # Связи с другими сущностями
    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="company", foreign_keys="[Deal.company_id]"
    )
