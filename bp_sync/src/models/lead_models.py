from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from schemas.enums import EntityType, StageSemanticEnum
from schemas.lead_schemas import LeadCreate

from .bases import CommunicationIntIdEntity
from .user_models import User

if TYPE_CHECKING:
    from .deal_models import Deal


class Lead(CommunicationIntIdEntity):
    """
    Лиды
    """

    __tablename__ = "leads"
    __table_args__ = (
        CheckConstraint("opportunity >= 0", name="non_negative_opportunity"),
    )
    _schema_class = LeadCreate

    @property
    def entity_type(self) -> EntityType:
        return EntityType.LEAD

    @property
    def tablename(self) -> str:
        return self.__tablename__

    def __str__(self) -> str:
        return str(self.title)

    # Идентификаторы и основные данные
    title: Mapped[str] = mapped_column(
        comment="Название лида"
    )  # TITLE : Название
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
    company_title: Mapped[str | None] = mapped_column(
        comment="Название компании, привязанной к лиду"
    )  # COMPANY_TITLE : Название компании, привязанной к лиду

    # Статусы и флаги
    is_manual_opportunity: Mapped[bool] = mapped_column(
        default=False, comment="Ручной ввод суммы"
    )  # IS_MANUAL_OPPORTUNITY : Сумма заполнена вручную
    is_return_customer: Mapped[bool] = mapped_column(
        default=False, comment="Повторный клиент"
    )  # IS_RETURN_CUSTOMER : Признак повторного лида (Y/N)

    # Финансовые данные
    opportunity: Mapped[float] = mapped_column(
        default=0.0, comment="Сумма сделки"
    )  # OPPORTUNITY : Сумма

    # Временные метки
    birthdate: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Дата рождения"
    )  # BIRTHDATE : Дата рождения (2025-06-18T03:00:00+03:00)
    moved_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Время перемещения"
    )  # MOVED_TIME : Дата перемещения элемента на текущую стадию
    date_closed: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Дата закрытия"
    )  # DATE_CLOSED : Дата закрытия

    # Перечисляемые типы
    status_semantic_id: Mapped[StageSemanticEnum] = mapped_column(
        PgEnum(
            StageSemanticEnum,
            name="deal_stage_enum",
            create_type=False,
            default=StageSemanticEnum.PROSPECTIVE,
            server_default=StageSemanticEnum.PROSPECTIVE.value,
        ),
        comment="Семантика стадии",
    )  # STATUS_SEMANTIC_ID : Статусы стадии лида

    # Связи с другими сущностями
    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="lead", foreign_keys="[Deal.lead_id]"
    )

    currency_id: Mapped[str | None] = mapped_column(
        comment="Ид валюты"
    )  # CURRENCY_ID : Ид валюты
    status_id: Mapped[str] = mapped_column(
        comment="Идентификатор стадии лида"
    )  # STATUS_ID : Идентификатор стадии лида
    company_id: Mapped[int | None] = mapped_column(
        comment="Ид компании"
    )  # COMPANY_ID : Ид компании
    contact_id: Mapped[int | None] = mapped_column(
        comment="Ид контакта"
    )  # CONTACT_ID : Ид контакта
    source_id: Mapped[str | None] = mapped_column(
        comment="Идентификатор источника (сводно)"
    )  # SOURCE_ID : Идентификатор источника (сводно)

    # Пользователи
    moved_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.external_id"),
        comment="ID переместившего",
    )  # MOVED_BY_ID : Ид автора, который переместил элемент на текущую стадию
    moved_user: Mapped["User"] = relationship(
        "User", foreign_keys=[moved_by_id], back_populates="moved_leads"
    )
