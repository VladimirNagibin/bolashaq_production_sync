from enum import IntEnum, StrEnum, auto

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

    MATEST = "matest.kz"
    RUP = "rup-su.ru"
    C1 = "1c"
    LABSET = "labset.su"


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
