from enum import StrEnum


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
