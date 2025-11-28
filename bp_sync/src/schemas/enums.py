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
            63: "Сделка провалена",
            65: "Сделка успешна",
            0: "Не определено",
        }
        return display_name_map.get(value, "Неизвестно")


class EntityType(StrEnum):
    """Типы сущностей в системе."""

    CONTACT = "Contact"
    COMPANY = "Company"
    LEAD = "Lead"
    DEAL = "Deal"
    USER = "User"
    INVOICE = "Invoice"
    TIMELINE_COMMENT = "TimelineComment"


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
