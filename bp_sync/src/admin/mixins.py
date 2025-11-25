from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

COLUMN_LABELS: dict[str, str] = {  # Надписи полей в списке
    "external_id": "Внешний код",
    "name": "Название",
    "created_at": "Дата создания",
    "updated_at": "Дата изменения",
    "is_deleted_in_bitrix": "Удалён в Б24",
}


class AdminListAndDetailMixin:
    """
    Mixin class for admin list and detail views with formatting utilities.
    """

    column_default_sort = [("external_id", True)]

    # Constants for formatting
    TITLE_MAX_LENGTH = 35
    DATE_FORMAT = "%d.%m.%Y"
    CURRENCY_DECIMALS = 2
    NUMBER_DECIMALS = 2

    def _get_attribute_value(
        self, model: Any, attribute: str, default: Any = None
    ) -> Any:
        """Safely get attribute value from model with default fallback."""
        return getattr(model, attribute, default)

    def format_title(self, model: Any, attribute: str) -> str:
        """Format title with ellipsis if exceeds max length."""
        title = str(self._get_attribute_value(model, attribute, ""))

        if len(title) > self.TITLE_MAX_LENGTH:
            return title[: self.TITLE_MAX_LENGTH] + "..."
        return title

    def format_currency(
        self,
        model: Any,
        attribute: str,
        currency_symbol: str = "",
        decimals: int | None = None,
    ) -> str:
        """Format numeric value as currency."""
        if decimals is None:
            decimals = self.CURRENCY_DECIMALS

        value = self._get_attribute_value(model, attribute, 0)

        # Handle different numeric types
        if isinstance(value, (int, float, Decimal)):
            formatted_value = f"{value:,.{decimals}f}"
        else:
            # Try to convert to numeric if possible
            try:
                numeric_value = float(value) if value else 0
                formatted_value = f"{numeric_value:,.{decimals}f}"
            except (ValueError, TypeError):
                formatted_value = f"0.{'0' * decimals}"

        if currency_symbol:
            return f"{formatted_value} {currency_symbol}".strip()
        return formatted_value

    def format_enum_display(
        self,
        enum_class: Any,
        model: Any,
        attribute: str,
        default_display: str = "Не указано",
    ) -> str:
        """Format enum values for display."""
        value = self._get_attribute_value(model, attribute)

        if not value:
            return default_display

        display_name = self._get_enum_display_name(enum_class, value)
        if display_name:
            return display_name

        return str(value) or default_display

    def _get_enum_display_name(
        self, enum_class: Any, value: Any
    ) -> str | None:
        """
        Helper method to get display name from enum with proper type handling.
        """
        try:
            # Method 1: Check if enum_class has get_display_name method
            if hasattr(enum_class, "get_display_name") and callable(
                enum_class.get_display_name
            ):
                result = enum_class.get_display_name(value)
                if result and isinstance(result, str):
                    return result  # type: ignore[no-any-return]

            # Method 2: For Python Enum classes - try to get the enum member
            if isinstance(enum_class, type) and issubclass(enum_class, Enum):
                try:
                    # Try to get enum member by value
                    enum_member = enum_class(value)
                    return str(enum_member.value)
                except ValueError:
                    # Try to get enum member by name
                    try:
                        enum_member = getattr(enum_class, str(value))
                        return str(enum_member.value)
                    except (AttributeError, TypeError):
                        pass

            # Method 3: Check for common display name patterns
            display_attrs = [
                "display_name",
                "label",
                "description",
                "verbose_name",
            ]
            for attr in display_attrs:
                method = getattr(enum_class, attr, None)
                if callable(method):
                    result = method(value)
                    if result and isinstance(result, str):
                        return result  # type: ignore[no-any-return]

        except (AttributeError, ValueError, TypeError):
            pass

        return None

    def format_number(
        self,
        model: Any,
        attribute: str,
        decimals: int | None = None,
        default_value: int | float | str = 0,
    ) -> str:
        """Format numeric value with specified decimal places."""
        if decimals is None:
            decimals = self.NUMBER_DECIMALS

        value = self._get_attribute_value(model, attribute, default_value)

        if not value:
            return f"{default_value:,.{decimals}f}"

        try:
            numeric_value = float(value)
            return f"{numeric_value:,.{decimals}f}"
        except (ValueError, TypeError):
            return f"{default_value:,.{decimals}f}"

    def format_opportunity(self, model: Any, attribute: str) -> str:
        """Format opportunity amount (alias for format_number)."""
        return self.format_number(model, attribute)

    def format_date(
        self, model: Any, attribute: str, date_format: str | None = None
    ) -> str:
        """Format date/datetime object."""
        if date_format is None:
            date_format = self.DATE_FORMAT

        value = self._get_attribute_value(model, attribute)

        if not value:
            return "-"

        try:
            if isinstance(value, (datetime, date)):
                return value.strftime(date_format)
            else:
                # Try to parse string to datetime
                if isinstance(value, str):
                    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d.%m.%Y"):
                        try:
                            dt = datetime.strptime(value, fmt)
                            return dt.strftime(date_format)
                        except ValueError:
                            continue
        except (ValueError, AttributeError):
            pass

        return "-"

    def format_boolean(
        self,
        model: Any,
        attribute: str,
        true_display: str = "Да",
        false_display: str = "Нет",
    ) -> str:
        """Format boolean value for display."""
        value = self._get_attribute_value(model, attribute, False)

        # Handle various boolean representations
        if isinstance(value, bool):
            return true_display if value else false_display
        elif isinstance(value, (int, float)):
            return true_display if value else false_display
        elif isinstance(value, str):
            lower_val = value.lower()
            if lower_val in ("true", "yes", "1", "да", "д"):
                return true_display
            elif lower_val in ("false", "no", "0", "нет", "н"):
                return false_display

        return false_display

    def format_percentage(
        self, model: Any, attribute: str, decimals: int = 1
    ) -> str:
        """Format value as percentage."""
        value = self._get_attribute_value(model, attribute, 0)

        try:
            numeric_value = float(value) * 100
            return f"{numeric_value:,.{decimals}f}%"
        except (ValueError, TypeError):
            return f"0.{'0' * decimals}%"

    def format_phone_number(self, model: Any, attribute: str) -> str:
        """Format phone number for display."""
        phone = str(self._get_attribute_value(model, attribute, ""))

        # Remove all non-digit characters
        digits = "".join(filter(str.isdigit, phone))

        # Basic phone formatting
        if len(digits) == 11 and digits.startswith(("7", "8")):
            return (
                f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:]}"
            )
        elif len(digits) == 10:
            return (
                f"+7 ({digits[0:3]}) {digits[3:6]}-{digits[6:8]}-{digits[8:]}"
            )

        return phone  # Return original if format doesn't match

    @staticmethod
    def format_title_(model: Any, attribute: str) -> str:
        title = str(getattr(model, attribute, ""))
        return title[:35] + "..." if len(title) > 35 else title

    @staticmethod
    def format_currency_(
        model: Any, attribute: str, currency_symbol: str = ""
    ) -> str:
        value = getattr(model, attribute, 0)
        return (
            f"{value:,.2f} {currency_symbol}".strip()
            if value
            else f"0 {currency_symbol}".strip()
        )

    @staticmethod
    def format_enum_display_(
        enum_class: Any, model: Any, attribute: str
    ) -> str:
        """Форматирование enum значений для отображения"""
        value = getattr(model, attribute, "")
        return enum_class.get_display_name(value) if value else "Не указано"

    @staticmethod
    def format_opportunity_(model: Any, attribute: str) -> str:
        """Форматирование суммы"""
        value = getattr(model, attribute, 0)
        return f"{value:,.2f}" if value else "0"

    @staticmethod
    def format_date_(model: Any, attribute: str) -> str:
        """Форматирование даты"""
        value = getattr(model, attribute, None)
        return value.strftime("%d.%m.%Y") if value else "-"
