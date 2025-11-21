from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from schemas.contact_schemas import ContactCreate
from schemas.enums import EntityType

from .bases import CommunicationIntIdEntity

if TYPE_CHECKING:
    from .deal_models import Deal


class Contact(CommunicationIntIdEntity):
    """
    Контакты
    """

    __tablename__ = "contacts"
    # __table_args__ = (
    #    CheckConstraint("opportunity >= 0", name="non_negative_opportunity"),
    # )
    _schema_class = ContactCreate

    @property
    def entity_type(self) -> EntityType:
        return EntityType.CONTACT

    @property
    def tablename(self) -> str:
        return self.__tablename__

    def __str__(self) -> str:
        return f"{self.name} {self.second_name} {self.last_name}"

    # Идентификаторы и основные данные
    name: Mapped[str | None] = mapped_column(
        comment="Имя контакта"
    )  # NAME : Имя контакта
    second_name: Mapped[str | None] = mapped_column(
        comment="Отчество контакта"
    )  # SECOND_NAME : Отчество контакта
    last_name: Mapped[str | None] = mapped_column(
        comment="Фамилия контакта"
    )  # LAST_NAME : Фамилия контакта
    post: Mapped[str | None] = mapped_column(
        comment="Должность"
    )  # POST : Должность
    origin_version: Mapped[str | None] = mapped_column(
        comment="Версия данных о контакте во внешней системе"
    )  # ORIGIN_VERSION : Версия данных о контакте во внешней системе

    # Статусы и флаги
    export: Mapped[bool] = mapped_column(
        default=False, comment="Участвует в экспорте контактов"
    )  # EXPORT : Участвует в экспорте контактов

    # Временные метки
    birthdate: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Дата рождения"
    )  # BIRTHDATE : Дата рождения (2025-06-18T03:00:00+03:00)

    # Связи с другими сущностями
    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="contact", foreign_keys="[Deal.contact_id]"
    )

    type_id: Mapped[str | None] = mapped_column(
        comment="Тип контакта"
    )  # TYPE_ID : Тип контакта
    company_id: Mapped[int | None] = mapped_column(
        comment="Ид компании"
    )  # COMPANY_ID : Ид компании
    lead_id: Mapped[int | None] = mapped_column(
        comment="Ид лида"
    )  # LEAD_ID : Ид лида
    source_id: Mapped[str | None] = mapped_column(
        comment="Идентификатор источника"
    )  # SOURCE_ID : Идентификатор источника
