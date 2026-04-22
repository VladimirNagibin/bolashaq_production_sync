from enum import IntEnum, StrEnum, auto
from typing import Any, Self

CURRENCY = "KZT"
SYSTEM_USER_ID = 37


class StageSemanticEnum(StrEnum):
    """
    Статусы стадии сделки:
    P - В работе(processing)
    S - Успешная(success)
    F - Провал(failed)
    """

    PROSPECTIVE = "P"
    SUCCESS = "S"
    FAIL = "F"

    @classmethod
    def get_display_name(cls, value: str) -> str:
        """Get display name by value"""
        display_name_map: dict[str, str] = {
            "P": "В работе",
            "S": "Успех",
            "F": "Провал",
        }
        return display_name_map.get(value, "Неизвестно")


class EntityTypeAbbr(StrEnum):
    CONTACT = "C"
    COMPANY = "CO"
    LEAD = "L"
    DEAL = "D"
    INVOICE = "SI"
    QUOTE = "Q"
    REQUISITE = "RQ"
    ORDER = "O"


class DealStatusEnum(IntEnum):
    """Статусы состояния сделки."""

    NEW = 45

    ACCEPTED = 47

    OFFER_NO = 49
    OFFER_IN_AGREEMENT_SUPERVISOR = 51
    OFFER_APPROVED_SUPERVISOR = 53
    OFFER_DISMISSED_SUPERVISOR = 55
    OFFER_SENT_CLIENT = 57
    OFFER_APPROVED_CLIENT = 59
    OFFER_DISMISSED_CLIENT = 61

    CONTRACT_NO = 67
    DRAFT_CONTRACT_IN_AGREEMENT_SUPERVISOR = 69
    DRAFT_CONTRACT_APPROVED_SUPERVISOR = 71
    DRAFT_CONTRACT_DISMISSED_SUPERVISOR = 73
    DRAFT_CONTRACT_SENT_CLIENT = 75
    DRAFT_CONTRACT_APPROVED_CLIENT = 77
    DRAFT_CONTRACT_DISMISSED_CLIENT = 79
    CONTRACT_IN_SIGN_SUPERVISOR = 81
    CONTRACT_SIGN_SUPERVISOR = 83
    CONTRACT_UNSIGN_SUPERVISOR = 85
    CONTRACT_SENT_IN_SIGN_CLIENT = 87
    CONTRACT_SIGN_CLIENT = 89
    CONTRACT_UNSIGN_CLIENT = 91

    DEAL_LOSE = 63
    DEAL_WON = 65

    NOT_DEFINE = 0

    @classmethod
    def get_display_name(cls, value: int) -> str:
        """Get display name by value"""
        display_name_map: dict[int, str] = {
            45: "Новый",
            47: "Принят в работу",
            49: "КП - отсутствует",
            51: "КП - на согласовании руководителем",
            53: "КП - подтверждён руководителем",
            55: "КП - отклонен руководителем",
            57: "КП - отправлен клиенту",
            59: "КП - согласован с клиентом",
            61: "КП - отклонён клиентом",
            67: "Договор - отсутствует",
            69: "Проект договора - на согласовании руководителем",
            71: "Проект договора - подтверждён руководителем",
            73: "Проект договора - отклонен руководителем",
            75: "Проект договора - отправлен клиенту",
            77: "Проект договора - согласован с клиентом",
            79: "Проект договора - отклонён клиентом",
            81: "Договор - на подпись руководителем",
            83: "Договор - подписан руководителем",
            85: "Договор - отклонен руководителем",
            87: "Договор - отправлен на подпись клиенту",
            89: "Договор - подписан клиентом",
            91: "Договор - отклонён клиентом",
            63: "Сделка провалена",
            65: "Сделка успешна",
            0: "Не определено",
        }
        return display_name_map.get(value, "Неизвестно")

    @classmethod
    def get_deal_status_by_name(
        cls, status_name: str
    ) -> "DealStatusEnum | None":
        """
        Возвращает элемент DealStatusEnum по его строковому имени.

        Поиск нечувствителен к регистру.

        Args:
            status_name: Строковое имя статуса (например, "NEW", "deal_lose").

        Returns:
            Соответствующий элемент DealStatusEnum или NOT_DEFINE,
            если статус не найден.
        """
        try:
            return DealStatusEnum[status_name.upper()]
        except KeyError:
            # Если элемент с таким именем не найден, возвращаем None
            return DealStatusEnum.NOT_DEFINE


class EntityType(StrEnum):
    """Типы сущностей в системе."""

    CONTACT = "Contact"
    COMPANY = "Company"
    LEAD = "Lead"
    DEAL = "Deal"
    USER = "User"
    INVOICE = "Invoice"
    TIMELINE_COMMENT = "TimelineComment"
    PRODUCT = "Product"
    SUPPLIER_PRODUCT = "SupplierProduct"
    PRODUCT_IMAGE = "ProductImage"


class CommunicationType(StrEnum):
    """Типы коммуникационных каналов."""

    PHONE = auto()
    EMAIL = auto()
    WEB = auto()
    IM = auto()
    LINK = auto()

    @staticmethod
    def has_value(value: str) -> bool:
        """Проверяет, существует ли значение в перечислении."""
        return value in CommunicationType.__members__


COMMUNICATION_TYPES = {
    "phone": CommunicationType.PHONE,
    "email": CommunicationType.EMAIL,
    "web": CommunicationType.WEB,
    "im": CommunicationType.IM,
    "link": CommunicationType.LINK,
}


class DealStagesEnum(IntEnum):
    """Стадии сделки."""

    NEW = 1
    NEEDS_IDENTIFICATION = 2
    OFFER_PREPARE = 3
    CLIENT_CONSIDER = 4
    CONTRACT_CONCLUSION = 5
    PREPAYMENT_INVOICE = 6
    SHIPMENT_PREPARE = 7
    SHIPMENT_APPROVAL = 8
    DELIVERY = 9
    FINALIZATION = 10
    WON = 11
    LOSE = 12
    LOSE_ANALYSIS = 13


class SourcesProductEnum(StrEnum):
    """Источники данных о товарах."""

    MATEST = "matest.kz"  # 107
    RUP = "rup-su.ru"  # 115
    C1 = "1c"  # 117
    LABSET = "labset.su"  # 109
    EQUALIZER = "equalizer.kz"  # 111
    BOLASHAQTRADE = "bolashaqtrade.kz"  # 113

    @classmethod
    def mapping_bitrix_id(cls) -> dict[int, str]:
        """Возвращает маппинг Bitrix ID на значения источников."""
        return {
            107: cls.MATEST.value,
            115: cls.RUP.value,
            117: cls.C1.value,
            109: cls.LABSET.value,
            111: cls.EQUALIZER.value,
            113: cls.BOLASHAQTRADE.value,
        }

    @classmethod
    def get_bitrix_id(cls, source: str | Self) -> int:
        """
        Возвращает Bitrix ID по значению источника или объекту перечисления.
        Пример: SourcesProductEnum.get_bitrix_id("matest.kz") -> 107
        """
        if isinstance(source, cls):
            source = source.value
        # Инвертированный маппинг (значение -> ID)
        reverse_mapping = {v: k for k, v in cls.mapping_bitrix_id().items()}
        return reverse_mapping[source]

    @classmethod
    def get_source_by_bitrix_id(cls, bitrix_id: int) -> str:
        """Возвращает строковое значение источника по Bitrix ID."""
        return cls.mapping_bitrix_id()[bitrix_id]

    @classmethod
    def get_enum_by_bitrix_id(cls, bitrix_id: int) -> Self:
        """Возвращает элемент перечисления по Bitrix ID."""
        source_value = cls.get_source_by_bitrix_id(bitrix_id)
        return cls(source_value)

    @classmethod
    def get_all_bitrix_ids(cls) -> list[int]:
        """Возвращает список всех Bitrix ID."""
        return list(cls.mapping_bitrix_id().keys())


class SourceKeyField(StrEnum):
    """Поля, которые могут быть уникальным идентификатором источника."""

    EXTERNAL_ID = "external_id"
    CODE = "code"


class TypeEvent(StrEnum):
    """
    Типы событий:
    REQUEST_PRICE - Запрос КП Матест
    BUY_ONE_CLICK - Покупка в один клик Матест
    ORDER - Заказ из корзины Матест
    REQUEST_PRICE_LABSET - Запрос цен от Лабсет
    """

    REQUEST_PRICE = "request_price"
    BUY_ONE_CLICK = "buy_one_click"
    ORDER = "order"
    REQUEST_PRICE_LABSET = "request_price_labset"


class LeadFailureReasonEnum(IntEnum):
    """Причины провала лида."""

    SPAM = 109  # Спам
    WRONG_CONTACT = 111  # Ошибочное обращение
    NO_ANSWER = 113  # Недозвон / клиент недоступен
    INVALID_CONTACT_DATA = 115  # Некорректные контактные данные
    TEST_LEAD = 117  # Тестовая заявка
    DUPLICATE = 119  # Дубликат
    NOT_WHOLESALE = 151  # Не относится к процессу продажи
    OTHER = 121  # Другое (укажите в комментарии)


class ImageType(StrEnum):
    """Типы изображений."""

    DETAIL_PICTURE = "detailPicture"
    PREVIEW_PICTURE = "previewPicture"
    MORE_PHOTO = "property101"


class TransformationRule(StrEnum):
    """Правила трансформации данных."""

    STRIP = "strip"
    UPPER = "upper"
    LOWER = "lower"
    TO_FLOAT = "float"
    TO_INT = "int"
    TO_BOOL = "bool"
    REGEX = "re:"
    CUSTOM = "def:"


class BrandEnum(IntEnum):
    """Бренды"""

    MATEST = 93
    STROYPRIBOR = 95
    ZORN = 97
    INMARKON = 99
    TVT = 101
    BIOBASE = 103
    TESTO = 105

    @classmethod
    def display_names(cls) -> dict[int, str]:
        # Маппинг ID на оригинальные названия для отображения
        return {
            93: "Matest",
            95: "Стройприбор",
            97: "Zorn",
            99: "Инмаркон",
            101: "ТВТ",
            103: "Biobase",
            105: "Testo",
        }

    @classmethod
    def get_display_name(cls, value: int) -> str:
        """Получить отображаемое имя бренда по числовому ID"""
        return cls.display_names().get(value, "Неизвестно")

    @classmethod
    def get_original_name(cls, value: int) -> str:
        """Получить оригинальное русское название бренда"""
        return cls.display_names().get(value, "Unknown")

    @classmethod
    def get_by_name(cls, name: str) -> "BrandEnum | None":
        """
        Получить бренд по имени (case-insensitive, поддерживает
        русские и английские названия)
        """
        name_lower = name.lower()
        for brand in cls:
            # Проверка по английскому имени
            if brand.name.lower() == name_lower:
                return brand
            # Проверка по оригинальному русскому названию
            if cls.display_names().get(brand.value, "").lower() == name_lower:
                return brand
        return None

    @classmethod
    def get_by_id(cls, value: int) -> "BrandEnum | None":
        """Получить бренд по числовому ID"""
        try:
            return cls(value)
        except ValueError:
            return None

    @classmethod
    def to_dict(cls) -> list[dict[str, Any]]:
        """Преобразовать все бренды в список словарей"""
        return [
            {
                "id": brand.value,
                "name": brand.name,  # Английское имя (ключ)
                "display_name": cls.get_display_name(
                    brand.value
                ),  # Оригинальное имя
            }
            for brand in cls
        ]

    @classmethod
    def get_all_ids(cls) -> list[int]:
        """Получить все ID брендов"""
        return [brand.value for brand in cls]

    @classmethod
    def exists(cls, value: int) -> bool:
        """Проверить, существует ли бренд с таким ID"""
        try:
            cls(value)
            return True
        except ValueError:
            return False


class MeasureEnum(IntEnum):
    """Единицы измерения"""

    METER = 1  # метр
    LITER = 3  # литр
    GRAM = 5  # грамм
    KILOGRAM = 7  # килограмм
    PIECE = 9  # штука
    PACKAGE = 11  # упаковка
