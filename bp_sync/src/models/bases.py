from datetime import datetime
from typing import TYPE_CHECKING, Any, ClassVar, Type, TypeVar

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import (
    Mapped,
    class_mapper,
    mapped_column,
    relationship,
)

from db.postgres import Base
from schemas.base_schemas import CommonFieldMixin
from schemas.enums import CommunicationType, EntityType

if TYPE_CHECKING:
    from .communications import CommunicationChannel
    from .user_models import User

T = TypeVar("T", bound=CommonFieldMixin)


class IntIdEntity(Base):  # type: ignore[misc]
    """Базовый класс для сущностей с внешними ID"""

    __abstract__ = True

    # Аннотация для схемы класса
    _schema_class: ClassVar[Type[CommonFieldMixin] | None] = None

    external_id: Mapped[int] = mapped_column(
        unique=True,
        comment="ID во внешней системе",
    )

    @classmethod
    def _get_schema_class(cls) -> Type[CommonFieldMixin] | None:
        """Автоматически определяет класс схемы на основе имени модели"""
        if cls._schema_class:
            return cls._schema_class

        # Попытка автоматического определения имени схемы
        try:
            module_name = f"schemas.{cls.__module__.split('.')[-1]}_schemas"
            import importlib

            schemas_module = importlib.import_module(module_name)

            schema_name = f"{cls.__name__}Create"
            schema_class = getattr(schemas_module, schema_name, None)

            if schema_class and issubclass(schema_class, CommonFieldMixin):
                cls._schema_class = schema_class
                return schema_class  # type: ignore[no-any-return]

        except (ImportError, AttributeError, TypeError):
            pass
        return None

    def to_pydantic(
        self,
        schema_class: Type[CommonFieldMixin] | None = None,
        exclude_relationships: bool = True,
    ) -> CommonFieldMixin:
        """
        Преобразует объект SQLAlchemy в Pydantic схему

        Args:
            schema_class: Класс Pydantic схемы
            exclude_relationships: Исключать ли связи из преобразования

        Returns:
            Экземпляр Pydantic схемы

        Raises:
            ValueError: Если не удалось определить класс схемы
        """
        schema_class = schema_class or self._get_schema_class()
        if schema_class is None:
            raise ValueError(
                "Cannot automatically determine schema class for "
                f"{self.__class__.__name__}. Please provide schema_class "
                "parameter or set _schema_class."
            )
        data: dict[str, Any] = {}

        # Получаем все поля схемы
        for field_name in schema_class.model_fields:
            # Пропускаем поля, которые являются связями и должны быть исключены
            if exclude_relationships and self._is_relationship_field(
                field_name
            ):
                continue

            if hasattr(self, field_name):
                value = getattr(self, field_name)
                data.update(self._transform_field_value(field_name, value))
        if hasattr(self, "id"):
            data["internal_id"] = self.id
        return schema_class(**data)

    def _transform_field_value(self, field_name: str, value: Any) -> Any:
        """Трансформирует значение поля при необходимости."""
        if field_name == "external_id" and value:
            return {"ID": value}
        return {field_name: value}

    def _is_relationship_field(self, field_name: str) -> bool:
        """Проверяет, является ли поле связью"""
        try:
            mapper = class_mapper(self.__class__)
            return field_name in mapper.relationships
        except Exception:
            return False


class NameIntIdEntity(IntIdEntity):
    """Базовый класс для сущностей с внешними ID и name"""

    __abstract__ = True

    name: Mapped[str] = mapped_column(comment="Название")

    def __str__(self) -> str:
        return str(self.name)


class NameStrIdEntity(Base):  # type: ignore[misc]
    """Базовый класс для сущностей со строчным внешними ID и name"""

    __abstract__ = True

    external_id: Mapped[str] = mapped_column(
        unique=True,
        comment="ID во внешней системе",
    )
    name: Mapped[str] = mapped_column(comment="Название")

    def __str__(self) -> str:
        return str(self.name)


class TimestampsMixin:
    """Миксин для временных меток."""

    date_create: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), comment="Дата создания"
    )  # DATE_CREATE : Дата создания  (2025-06-18T03:00:00+03:00)
    date_modify: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), comment="Дата изменения"
    )  # DATE_MODIFY : Дата изменения
    last_activity_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Время последней активности"
    )  # LAST_ACTIVITY_TIME : Время последней активности
    last_communication_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False), comment="Время последней коммуникации"
    )  # LAST_COMMUNICATION_TIME : Дата 02.02.2024  15:21:08


class UserRelationsMixin:
    """Миксин для отношений с пользователями"""

    assigned_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.external_id"),
        comment="ID ответственного",
    )
    created_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.external_id"),
        comment="ID создателя",
    )
    modify_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.external_id"),
        comment="ID изменившего",
    )
    last_activity_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.external_id"),
        comment="ID последней активности",
    )

    @property
    def entity_type(self) -> EntityType:
        """Должен быть переопределен в дочерних классах."""
        raise NotImplementedError("Должно быть реализовано в дочернем классе")

    @declared_attr  # type: ignore[misc]
    def assigned_user(cls) -> Mapped["User"]:
        """Отношение с ответственным пользователем."""
        return relationship(
            "User",
            foreign_keys=[cls.assigned_by_id],
            back_populates=(
                f"assigned_{cls.__tablename__}"  # type: ignore[attr-defined]
            ),
        )

    @declared_attr  # type: ignore[misc]
    def created_user(cls) -> Mapped["User"]:
        """Отношение с создавшим пользователем."""
        return relationship(
            "User",
            foreign_keys=[cls.created_by_id],
            back_populates=(
                f"created_{cls.__tablename__}"  # type: ignore[attr-defined]
            ),
        )

    @declared_attr  # type: ignore[misc]
    def modify_user(cls) -> Mapped["User"]:
        """Отношение с изменившим пользователем."""
        return relationship(
            "User",
            foreign_keys=[cls.modify_by_id],
            back_populates=(
                f"modify_{cls.__tablename__}"  # type: ignore[attr-defined]
            ),
        )

    @declared_attr  # type: ignore[misc]
    def last_activity_user(cls) -> Mapped["User"]:
        """Отношение с пользователем последней активности."""
        tablename = cls.__tablename__  # type: ignore[attr-defined]
        return relationship(
            "User",
            foreign_keys=[cls.last_activity_by],
            back_populates=(f"last_activity_{tablename}"),
        )


class MarketingMixinUTM:
    utm_source: Mapped[str | None] = mapped_column(
        comment="Рекламная система"
    )  # UTM_SOURCE : Рекламная система (Yandex-Direct, Google-Adwords и др)
    utm_medium: Mapped[str | None] = mapped_column(
        comment="Тип трафика"
    )  # UTM_MEDIUM : Тип трафика: CPC (объявления), CPM (баннеры)
    utm_campaign: Mapped[str | None] = mapped_column(
        comment="Обозначение рекламной кампании"
    )  # UTM_CAMPAIGN : Обозначение рекламной кампании
    utm_content: Mapped[str | None] = mapped_column(
        comment="Содержание кампании"
    )  # UTM_CONTENT : Содержание кампании. Например, для контекстных
    # объявлений
    utm_term: Mapped[str | None] = mapped_column(
        comment="Тип трафика"
    )  # UTM_TERM : Условие поиска кампании. Например, ключевые слова
    # контекстной рекламы


class MarketingMixin:
    mgo_cc_entry_id: Mapped[str | None] = mapped_column(
        comment="ID звонка"
    )  # UF_CRM_MGO_CC_ENTRY_ID : ID звонка
    mgo_cc_channel_type: Mapped[str | None] = mapped_column(
        comment="Канал обращения"
    )  # UF_CRM_MGO_CC_CHANNEL_TYPE : Канал обращения
    mgo_cc_result: Mapped[str | None] = mapped_column(
        comment="Результат обращения"
    )  # UF_CRM_MGO_CC_RESULT : Результат обращения
    mgo_cc_entry_point: Mapped[str | None] = mapped_column(
        comment="Точка входа обращения"
    )  # UF_CRM_MGO_CC_ENTRY_POINT : Точка входа обращения
    mgo_cc_create: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Дата/время создания обращения"
    )  # UF_CRM_MGO_CC_CREATE : Дата/время создания обращения
    mgo_cc_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Дата/время завершения обращения"
    )  # UF_CRM_MGO_CC_END : Дата/время завершения обращения
    mgo_cc_tag_id: Mapped[str | None] = mapped_column(
        comment="Тематики обращения"
    )  # UF_CRM_MGO_CC_TAG_ID : Тематики обращения
    calltouch_site_id: Mapped[str | None] = mapped_column(
        comment="ID сайта в Calltouch"
    )  # - : ID сайта в Calltouch
    calltouch_call_id: Mapped[str | None] = mapped_column(
        comment="ID звонка в Calltouch"
    )  # - : ID звонка в Calltouch
    calltouch_request_id: Mapped[str | None] = mapped_column(
        comment="ID заявки в Calltouch"
    )  # - : ID заявки в Calltouch


class CommunicationMixin:
    """Миксин для автоматического получения телефонов, email и т.д."""

    has_phone: Mapped[bool] = mapped_column(
        default=False, comment="Признак заполненности поля телефон"
    )  # HAS_PHONE : Признак заполненности поля телефон (Y/N)
    has_email: Mapped[bool] = mapped_column(
        default=False, comment="Признак заполненности электронной почты"
    )  # HAS_EMAIL : Признак заполненности поля электронной почты (Y/N)
    has_imol: Mapped[bool] = mapped_column(
        default=False, comment="Признак наличия привязанной открытой линии"
    )  # HAS_IMOL : Признак наличия привязанной открытой линии (Y/N)

    @declared_attr  # type: ignore[misc]
    def communications(cls) -> Mapped[list["CommunicationChannel"]]:
        """Отношение с коммуникационными каналами."""
        condition = (
            "and_("
            "foreign(CommunicationChannel.entity_type) == '{}',"
            "foreign(CommunicationChannel.entity_id) == {}.external_id"
            ")"
        ).format(
            cls.__name__, cls.__name__  # type: ignore[attr-defined]
        )
        return relationship(
            "CommunicationChannel",
            primaryjoin=condition,
            viewonly=True,
            lazy="selectin",
            overlaps="communications",
        )

    @property
    def phones(self) -> list[str]:
        """Список телефонных номеров"""
        return self._get_communication_values(CommunicationType.PHONE)

    @property
    def emails(self) -> list[str]:
        """Список email-адресов"""
        return self._get_communication_values(CommunicationType.EMAIL)

    @property
    def webs(self) -> list[str]:
        """Список сайтов"""
        return self._get_communication_values(CommunicationType.WEB)

    @property
    def ims(self) -> list[str]:
        """Список мессенджеров"""
        return self._get_communication_values(CommunicationType.IM)

    @property
    def links(self) -> list[str]:
        """Список ссылок"""
        return self._get_communication_values(CommunicationType.LINK)

    def _get_communication_values(
        self, comm_type: CommunicationType
    ) -> list[str]:
        """Вспомогательный метод для получения значений коммуникаций."""
        return [
            channel.value
            for channel in self.communications
            if channel.channel_type.type_id == comm_type
        ]


class SocialProfilesMixin:
    wz_instagram: Mapped[str | None] = mapped_column(
        comment="Instagram"
    )  # UF_CRM_INSTAGRAM_WZ : Instagram Лиды и Контакты
    wz_vc: Mapped[str | None] = mapped_column(
        comment="VC"
    )  # UF_CRM_VK_WZ : VC
    wz_telegram_username: Mapped[str | None] = mapped_column(
        comment="Telegram username"
    )  # UF_CRM_TELEGRAMUSERNAME_WZ : Telegram username
    wz_telegram_id: Mapped[str | None] = mapped_column(
        comment="Telegram Id"
    )  # UF_CRM_TELEGRAMID_WZ : Telegram Id
    wz_avito: Mapped[str | None] = mapped_column(
        comment="Avito"
    )  # UF_CRM_AVITO_WZ : Avito


class AddressMixin:
    # Адрес
    address: Mapped[str | None] = mapped_column(
        comment="Адрес контакта"
    )  # ADDRESS : Адрес контакта
    address_2: Mapped[str | None] = mapped_column(
        comment="Вторая страница адреса"
    )  # ADDRESS_2 :  Вторая страница адреса. В некоторых странах принято
    # разбивать адрес на 2 части
    address_city: Mapped[str | None] = mapped_column(
        comment="Город"
    )  # ADDRESS_CITY : Город
    address_postal_code: Mapped[str | None] = mapped_column(
        comment="Почтовый индекс"
    )  # ADDRESS_POSTAL_CODE : Почтовый индекс
    address_region: Mapped[str | None] = mapped_column(
        comment="Район"
    )  # ADDRESS_REGION : Район
    address_province: Mapped[str | None] = mapped_column(
        comment="Область"
    )  # ADDRESS_PROVINCE : Область
    address_country: Mapped[str | None] = mapped_column(
        comment="Страна"
    )  # ADDRESS_COUNTRY : Страна
    address_country_code: Mapped[str | None] = mapped_column(
        comment="Код страны"
    )  # ADDRESS_COUNTRY_CODE : Код страны
    address_loc_addr_id: Mapped[int | None] = mapped_column(
        comment="Идентификатор адреса из модуля местоположений"
    )  # ADDRESS_LOC_ADDR_ID : Идентификатор адреса из модуля местоположений


class BusinessEntityCore(
    IntIdEntity,
    TimestampsMixin,
    UserRelationsMixin,
    # MarketingMixin,
    # SocialProfilesMixin,
):
    """Базовый класс для бизнес-сущностей."""

    __abstract__ = True

    comments: Mapped[str | None] = mapped_column(
        comment="Комментарии"
    )  # COMMENTS : Коментарии
    source_description: Mapped[str | None] = mapped_column(
        comment="Описание источника"
    )  # SOURCE_DESCRIPTION : Дополнительно об источнике
    opened: Mapped[bool] = mapped_column(
        default=True, comment="Доступна для всех"
    )  # OPENED : Доступен для всех (Y/N)


class BusinessEntity(BusinessEntityCore, MarketingMixinUTM):
    """Расширенный класс бизнес-сущностей с UTM метками."""

    __abstract__ = True

    originator_id: Mapped[str | None] = mapped_column(
        comment="ID источника данных"
    )  # ORIGINATOR_ID : Идентификатор источника данных
    origin_id: Mapped[str | None] = mapped_column(
        comment="ID элемента в источнике"
    )  # ORIGIN_ID : Идентификатор элемента в источнике данных


class CommunicationIntIdEntity(
    BusinessEntity, CommunicationMixin, AddressMixin
):
    """Базовая модель с внешним ID и коммуникациями"""

    __abstract__ = True
