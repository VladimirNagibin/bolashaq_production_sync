from datetime import datetime

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.postgres import Base
from schemas.enums import EntityType
from schemas.user_schemas import ManagerCreate, UserCreate

from .bases import IntIdEntity
from .company_models import Company
from .contact_models import Contact
from .deal_models import Deal
from .department_models import Department
from .lead_models import Lead
from .timeline_comment_models import TimelineComment


class User(IntIdEntity):
    """
    Пользователи
    """

    __tablename__ = "users"
    _schema_class = UserCreate

    @property
    def entity_type(self) -> EntityType:
        return EntityType.USER

    # @property
    # def entity_type1(self) -> str:
    #    return "User"

    # @property
    # def tablename(self) -> str:
    #    return self.__tablename__

    @property
    def full_name(self) -> str:
        return f"{self.name} {self.last_name}"

    def __str__(self) -> str:
        return self.full_name

    # Идентификаторы и основные данные
    xml_id: Mapped[str | None] = mapped_column(
        comment="Внешний код"
    )  # XML_ID : Внешний код
    name: Mapped[str | None] = mapped_column(comment="Имя")  # NAME : Имя
    second_name: Mapped[str | None] = mapped_column(
        comment="Отчество"
    )  # SECOND_NAME : Отчество
    last_name: Mapped[str | None] = mapped_column(
        comment="Фамилия"
    )  # LAST_NAME : Фамилия
    personal_gender: Mapped[str | None] = mapped_column(
        comment="Пол"
    )  # PERSONAL_GENDER : Пол M / F
    work_position: Mapped[str | None] = mapped_column(
        comment="Должность"
    )  # WORK_POSITION : Должность
    user_type: Mapped[str | None] = mapped_column(
        comment="Тип пользователя"
    )  # USER_TYPE : Тип пользователя

    # Статусы и флаги
    active: Mapped[bool] = mapped_column(
        default=False, comment="Активность"
    )  # ACTIVE : Активность True / False
    is_online: Mapped[bool] = mapped_column(
        default=False, comment="Онлайн"
    )  # IS_ONLINE : Онлайн (Y/N)

    # Временные метки
    last_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Последняя авторизация"
    )  # LAST_LOGIN : Последняя авторизация (2025-06-18T03:00:00+03:00)
    date_register: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Дата регистрации"
    )  # DATE_REGISTER : Дата регистрации
    personal_birthday: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Дата рождения"
    )  # PERSONAL_BIRTHDAY : Дата рождения
    employment_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Новая дата"
    )  # UF_EMPLOYMENT_DATE : Новая дата
    date_new: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Новая дата"
    )  # UF_USR_1699347879988 : Новая дата

    # География и источники
    time_zone: Mapped[str | None] = mapped_column(
        comment="Часовой пояс"
    )  # TIME_ZONE : Часовой пояс
    personal_city: Mapped[str | None] = mapped_column(
        comment="Город проживания"
    )  # PERSONAL_CITY : Город проживания

    # Коммуникации
    email: Mapped[str | None] = mapped_column(
        comment="E-Mail"
    )  # EMAIL : E-Mail
    personal_mobile: Mapped[str | None] = mapped_column(
        comment="Личный мобильный"
    )  # PERSONAL_MOBILE : Личный мобильный
    work_phone: Mapped[str | None] = mapped_column(
        comment="Телефон компании"
    )  # WORK_PHONE : Телефон компании
    personal_www: Mapped[str | None] = mapped_column(
        comment="Домашняя страничка"
    )  # PERSONAL_WWW : Домашняя страничка

    # Связи с другими сущностями
    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.external_id")
    )  # UF_DEPARTMENT : отдел
    department: Mapped["Department"] = relationship(
        "Department", back_populates="users"
    )
    assigned_deals: Mapped[list["Deal"]] = relationship(
        "Deal",
        back_populates="assigned_user",
        foreign_keys="[Deal.assigned_by_id]",
    )
    created_deals: Mapped[list["Deal"]] = relationship(
        "Deal",
        back_populates="created_user",
        foreign_keys="[Deal.created_by_id]",
    )
    modify_deals: Mapped[list["Deal"]] = relationship(
        "Deal",
        back_populates="modify_user",
        foreign_keys="[Deal.modify_by_id]",
    )
    moved_deals: Mapped[list["Deal"]] = relationship(
        "Deal",
        back_populates="moved_user",
        foreign_keys="[Deal.moved_by_id]",
    )
    last_activity_deals: Mapped[list["Deal"]] = relationship(
        "Deal",
        back_populates="last_activity_user",
        foreign_keys="[Deal.last_activity_by]",
    )
    defect_deals: Mapped[list["Deal"]] = relationship(
        "Deal",
        back_populates="defect_expert",
        foreign_keys="[Deal.defect_expert_id]",
    )

    assigned_leads: Mapped[list["Lead"]] = relationship(
        "Lead",
        back_populates="assigned_user",
        foreign_keys="[Lead.assigned_by_id]",
    )
    created_leads: Mapped[list["Lead"]] = relationship(
        "Lead",
        back_populates="created_user",
        foreign_keys="[Lead.created_by_id]",
    )
    modify_leads: Mapped[list["Lead"]] = relationship(
        "Lead",
        back_populates="modify_user",
        foreign_keys="[Lead.modify_by_id]",
    )
    moved_leads: Mapped[list["Lead"]] = relationship(
        "Lead",
        back_populates="moved_user",
        foreign_keys="[Lead.moved_by_id]",
    )
    last_activity_leads: Mapped[list["Lead"]] = relationship(
        "Lead",
        back_populates="last_activity_user",
        foreign_keys="[Lead.last_activity_by]",
    )

    assigned_contacts: Mapped[list["Contact"]] = relationship(
        "Contact",
        back_populates="assigned_user",
        foreign_keys="[Contact.assigned_by_id]",
    )
    created_contacts: Mapped[list["Contact"]] = relationship(
        "Contact",
        back_populates="created_user",
        foreign_keys="[Contact.created_by_id]",
    )
    modify_contacts: Mapped[list["Contact"]] = relationship(
        "Contact",
        back_populates="modify_user",
        foreign_keys="[Contact.modify_by_id]",
    )
    last_activity_contacts: Mapped[list["Contact"]] = relationship(
        "Contact",
        back_populates="last_activity_user",
        foreign_keys="[Contact.last_activity_by]",
    )

    assigned_companies: Mapped[list["Company"]] = relationship(
        "Company",
        back_populates="assigned_user",
        foreign_keys="[Company.assigned_by_id]",
    )
    created_companies: Mapped[list["Company"]] = relationship(
        "Company",
        back_populates="created_user",
        foreign_keys="[Company.created_by_id]",
    )
    modify_companies: Mapped[list["Company"]] = relationship(
        "Company",
        back_populates="modify_user",
        foreign_keys="[Company.modify_by_id]",
    )
    last_activity_companies: Mapped[list["Company"]] = relationship(
        "Company",
        back_populates="last_activity_user",
        foreign_keys="[Company.last_activity_by]",
    )
    timeline_comments: Mapped[list["TimelineComment"]] = relationship(
        "TimelineComment",
        back_populates="author",
        foreign_keys="[TimelineComment.author_id]",
    )

    manager: Mapped["Manager"] = relationship(
        back_populates="user", uselist=False
    )


class Manager(Base):  # type: ignore[misc]
    """
    Менеджеры
    """

    __tablename__ = "managers"
    _schema_class = ManagerCreate

    def __str__(self) -> str:
        return str(self.user.full_name)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.external_id"),
        unique=True,
        comment="ИД сотрудника",
    )
    user: Mapped["User"] = relationship("User", back_populates="manager")
    is_active: Mapped[bool] = mapped_column(
        default=False, comment="Менеджер активный"
    )
    disk_id: Mapped[int | None] = mapped_column(comment="ИД диска")
    chat_id: Mapped[int | None] = mapped_column(comment="ИД служебного чата")
