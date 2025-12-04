from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.postgres import Base
from schemas.deal_schemas import DealCreate
from schemas.enums import (
    DealStatusEnum,
    EntityType,
    EntityTypeAbbr,
    StageSemanticEnum,
)

from .bases import BusinessEntity
from .company_models import Company
from .contact_models import Contact
from .deal_stage_models import DealStage
from .lead_models import Lead
from .product_models import ProductEntity
from .timeline_comment_models import TimelineComment
from .user_models import User


class Deal(BusinessEntity):
    """Сделки"""

    __tablename__ = "deals"
    __table_args__ = (
        CheckConstraint("opportunity >= 0", name="non_negative_opportunity"),
        CheckConstraint(
            "probability IS NULL OR (probability BETWEEN 0 AND 100)",
            name="valid_probability_range",
        ),
        CheckConstraint("external_id > 0", name="external_id_positive"),
    )
    _schema_class = DealCreate

    @property
    def entity_type(self) -> EntityType:
        return EntityType.DEAL

    # @property
    # def entity_type1(self) -> str:
    #    return "Deal"

    @property
    def tablename(self) -> str:
        return self.__tablename__

    def __str__(self) -> str:
        return str(self.title)

    # Идентификаторы и основные данные
    title: Mapped[str] = mapped_column(
        comment="Название сделки"
    )  # TITLE : Название
    additional_info: Mapped[str | None] = mapped_column(
        comment="Дополнительная информация"
    )  # ADDITIONAL_INFO : Дополнительная информация
    repeat_sale_segment_id: Mapped[str | None] = mapped_column(
        comment="Сегмент повторных продаж"
    )  # REPEAT_SALE_SEGMENT_ID : Сегмент повторных продаж
    introduction_offer: Mapped[str | None] = mapped_column(
        comment="Представление в КП"
    )  # UF_CRM_1759510370 : Представление в КП
    location_id: Mapped[str | None] = mapped_column(
        comment="Расположение ИД"
    )  # LOCATION_ID : Расположение ИД

    # Условия сделки
    delivery_days: Mapped[int | None] = mapped_column(
        comment="Срок поставки (дни)"
    )  # UF_CRM_1759510532 : Срок поставки (дни)
    warranty_months: Mapped[int | None] = mapped_column(
        comment="Гарантия (мес)"
    )  # UF_CRM_1759510662 : Гарантия (мес)
    contract: Mapped[str | None] = mapped_column(
        comment="Договор"
    )  # UF_CRM_1760952984 : Договор
    begining_condition_payment_percentage: Mapped[int | None] = mapped_column(
        comment="Процент оплаты для начала сделки"
    )  # UF_CRM_1759510807 : Процент оплаты для начала сделки
    shipping_condition_payment_percentage: Mapped[int | None] = mapped_column(
        comment="Процент оплаты для отгрузки сделки"
    )  # UF_CRM_1759510842 : Процент оплаты для отгрузки сделки

    # Статусы и флаги
    probability: Mapped[int | None] = mapped_column(
        comment="Вероятность успеха (0-100)"
    )  # PROBABILITY : Вероятность
    is_manual_opportunity: Mapped[bool] = mapped_column(
        default=False, comment="Ручной ввод суммы"
    )  # IS_MANUAL_OPPORTUNITY : Сумма заполнена вручную
    closed: Mapped[bool] = mapped_column(
        default=False, comment="Завершена"
    )  # CLOSET : Завершена ли сделка (Y/N)
    is_new: Mapped[bool] = mapped_column(
        default=False, comment="Новая сделка"
    )  # IS_NEW : Флаг новой сделки (Y/N)
    is_recurring: Mapped[bool] = mapped_column(
        default=False, comment="Регулярная сделка"
    )  # IS_RECURRING : Флаг шаблона регулярной сдели. Если Y, то шаблон (Y/N)
    is_return_customer: Mapped[bool] = mapped_column(
        default=False, comment="Повторный клиент"
    )  # IS_RETURN_CUSTOMER : Признак повторного лида (Y/N)
    is_repeated_approach: Mapped[bool] = mapped_column(
        default=False, comment="Повторное обращение"
    )  # IS_REPEATED_APPROACH : Повторное обращение (Y/N)
    without_offer: Mapped[bool | None] = mapped_column(
        default=False, comment="Без КП"
    )  # UF_CRM_1763633586 : Без КП
    without_contract: Mapped[bool | None] = mapped_column(
        default=False, comment="Без договора"
    )  # UF_CRM_1763633629 : Без договора

    # Финансовые данные
    opportunity: Mapped[float] = mapped_column(
        default=0.0, comment="Сумма сделки"
    )  # OPPORTUNITY : Сумма
    tax_value: Mapped[float | None] = mapped_column(
        comment="Сумма НДС"
    )  # TAX_VALUE : Сумма НДС
    half_amount: Mapped[float | None] = mapped_column(
        comment="Половино суммы"
    )  # UF_CRM_1760872964 : Половино суммы

    # Временные метки
    begindate: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), comment="Дата начала"
    )  # BEGINDATE : Дата начала (2025-06-18T03:00:00+03:00)
    closedate: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), comment="Дата завершения"
    )  # CLOSEDATE : Дата завершения
    moved_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Время перемещения"
    )  # MOVED_TIME : Дата перемещения элемента на текущую стадию
    date_answer_client: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Ожидаемая дата ответа от клиента"
    )  # UF_CRM_1763626692 : Ожидаемая дата ответа от клиента

    # Перечисляемые типы
    stage_semantic_id: Mapped[StageSemanticEnum] = mapped_column(
        PgEnum(
            StageSemanticEnum,
            name="deal_stage_enum",
            create_type=False,
            default=StageSemanticEnum.PROSPECTIVE,
            server_default=StageSemanticEnum.PROSPECTIVE.value,
        ),
        comment="Семантика стадии",
    )  # STAGE_SEMANTIC_ID : Статусы стадии сделки
    status_deal: Mapped[DealStatusEnum] = mapped_column(
        PgEnum(
            DealStatusEnum,
            name="deal_status_enum",
            create_type=False,
            default=DealStatusEnum.NOT_DEFINE,
            server_default=0,
        ),
        comment="Статус обработки",
    )  # UF_CRM_1763479557 : Статус обработки

    # Связи с другими сущностями
    timeline_comments: Mapped[list["TimelineComment"]] = relationship(
        "TimelineComment",
        primaryjoin=(
            "and_(Deal.external_id == foreign(TimelineComment.entity_id), "
            "TimelineComment.entity_type == 'Deal')"
        ),
        viewonly=True,
        lazy="selectin",
        back_populates="deal",
    )

    currency_id: Mapped[str | None] = mapped_column(
        comment="Ид валюты"
    )  # CURRENCY_ID : Ид валюты
    type_id: Mapped[str | None] = mapped_column(
        comment="Тип сделки"
    )  # TYPE_ID : Тип сделки
    stage_id: Mapped[str] = mapped_column(
        ForeignKey("deal_stages.external_id")
    )  # STAGE_ID : Идентификатор стадии сделки
    stage: Mapped["DealStage"] = relationship(
        "DealStage", back_populates="deals", foreign_keys=stage_id
    )
    lead_id: Mapped[int | None] = mapped_column(
        ForeignKey("leads.external_id")
    )  # LEAD_ID : Ид лида
    lead: Mapped["Lead"] = relationship(
        "Lead", back_populates="deals", foreign_keys=[lead_id]
    )
    company_id: Mapped[int | None] = mapped_column(
        ForeignKey("companies.external_id")
    )  # COMPANY_ID : Ид компании
    company: Mapped["Company"] = relationship(
        "Company", back_populates="deals", foreign_keys=[company_id]
    )
    contact_id: Mapped[int | None] = mapped_column(
        ForeignKey("contacts.external_id")
    )  # CONTACT_ID : Ид контакта
    contact: Mapped["Contact"] = relationship(
        "Contact", back_populates="deals", foreign_keys=[contact_id]
    )
    category_id: Mapped[int] = mapped_column(
        comment="Идентификатор направления"
    )  # CATEGORY_ID : Идентификатор направления
    source_id: Mapped[str | None] = mapped_column(
        comment="Идентификатор источника"
    )  # SOURCE_ID : Идентификатор источника
    quote_id: Mapped[int | None] = mapped_column(
        comment="Предложение"
    )  # QUOTE_ID : Предложение
    offer_link: Mapped[str | None] = mapped_column(
        comment="Ссылка на КП"
    )  # UF_CRM_1763483026 : Ссылка на КП

    # Пользователи
    moved_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.external_id"),
        comment="ID переместившего",
    )  # MOVED_BY_ID : Ид автора, который переместил элемент на текущую стадию
    moved_user: Mapped["User"] = relationship(
        "User", foreign_keys=[moved_by_id], back_populates="moved_deals"
    )
    add_info: Mapped["AdditionalInfo"] = relationship(
        back_populates="deal", uselist=False
    )

    # Социальные профили
    wz_instagram: Mapped[str | None] = mapped_column(
        comment="Инстаграм"
    )  # UF_CRM_6909F9E973085 : Инстаграм
    wz_vc: Mapped[str | None] = mapped_column(
        comment="ВК"
    )  # UF_CRM_6909F9E984D21 : ВК
    wz_telegram_username: Mapped[str | None] = mapped_column(
        comment="Телеграм имя"
    )  # UF_CRM_6909F9E9A38DA : Телеграм имя
    wz_telegram_id: Mapped[str | None] = mapped_column(
        comment="Телеграм ИД"
    )  # UF_CRM_6909F9E9ADB80 : Телеграм ИД
    wz_avito: Mapped[str | None] = mapped_column(
        comment="Авито"
    )  # UF_CRM_6909F9E98F0B8 : Авито
    wz_maxid: Mapped[str | None] = mapped_column(
        comment="Макс"
    )  # UF_CRM_6909F9E9994A9 : Макс

    products_list_as_string: Mapped[str | None] = mapped_column(
        comment="Список товаров преобразованном в строку"
    )  # UF_CRM_1764696465 : Список товаров преобразованном в строку

    # Вспомогательное поле для хранения реальной даты перехода на стадию
    moved_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),  # Текущее время по умолчанию
        comment="Дата перемещения (резервное поле)",
    )

    products_agreement_supervisor: Mapped[
        list["ProductAgreementSupervisor"]
    ] = relationship(
        "ProductAgreementSupervisor",
        back_populates="deal",
        foreign_keys="[ProductAgreementSupervisor.deal_id]",
    )

    # Связь с товарами
    @declared_attr  # type: ignore[misc]
    def product_entities(cls) -> Mapped[list["ProductEntity"]]:
        """Товары в сделке."""
        condition = (
            "and_("
            "foreign(ProductEntity.owner_type) == '{}',"
            "foreign(ProductEntity.owner_id) == {}.external_id"
            ")"
        ).format(EntityTypeAbbr.DEAL, cls.__name__)
        return relationship(
            "ProductEntity",
            primaryjoin=condition,
            viewonly=True,
            lazy="selectin",
            overlaps="product_entities",
        )


class AdditionalInfo(Base):  # type: ignore[misc]
    """
    Дополнительная информация сделки
    """

    __tablename__ = "additional_info"

    deal_id: Mapped[int] = mapped_column(
        ForeignKey("deals.external_id"),
        unique=True,
        comment="ID сделки",
    )
    deal: Mapped["Deal"] = relationship("Deal", back_populates="add_info")
    comment: Mapped[str] = mapped_column(
        default="", comment="Дополнительная информация"
    )


class ProductAgreementSupervisor(Base):  # type: ignore[misc]
    """
    Товары из согласованного КП
    """

    __tablename__ = "product_agreement_supervisor"
    # _schema_class = ManagerCreate

    def __str__(self) -> str:
        return str(self.deal.title)

    deal_id: Mapped[int] = mapped_column(
        ForeignKey("deals.external_id"),
        unique=True,
        comment="ID сделки",
    )
    deal: Mapped["Deal"] = relationship(
        "Deal", back_populates="products_agreement_supervisor"
    )
    product_id: Mapped[int] = mapped_column(comment="ИД товара")
    status_deal: Mapped[DealStatusEnum] = mapped_column(
        PgEnum(
            DealStatusEnum,
            name="deal_status_enum",
            create_type=False,
            default=DealStatusEnum.NOT_DEFINE,
            server_default=0,
        ),
        comment="Статус обработки",
    )
