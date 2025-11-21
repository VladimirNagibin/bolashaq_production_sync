from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .bases import NameStrIdEntity

if TYPE_CHECKING:
    from .deal_models import Deal

DEAL_STAGE_VALUES = [
    ("Новая", "NEW", 1),
    ("Выявление потребностей", "UC_2ZE891", 2),
    ("Формирование КП", "PREPARATION", 3),
    ("На рассмотрении покупателем", "UC_4IBXSC", 4),
    ("Заключение договора", "UC_ACQNNK", 5),
    ("Выставление счёта", "PREPAYMENT_INVOICE", 6),
    ("Подготовка к отгрузке", "EXECUTING", 7),
    ("Разрешение отгрузки", "UC_Q4L94H", 8),
    ("Доставка товара", "UC_VIZABN", 9),
    ("Проверка завершения сделки", "FINAL_INVOICE", 10),
    ("Сделка успешная", "WON", 11),
    ("Сделка провалена", "LOSE", 12),
    ("Анализ причины провала", "APOLOGY", 13),
]


class DealStage(NameStrIdEntity):
    """
    Стадии сделок:
    1. NEW: Новая
    2. UC_2ZE891: Выявление потребностей
    3. PREPARATION: Формирование КП
    4. UC_4IBXSC: На рассмотрении покупателем
    5. UC_ACQNNK: Заключение договора
    6. PREPAYMENT_INVOICE: Выставление счёта
    7. EXECUTING: Подготовка к отгрузке
    8. UC_Q4L94H: Разрешение отгрузки
    9. UC_VIZABN: Доставка товара
    10. FINAL_INVOICE: Проверка завершения сделки
    11. WON: Сделка успешная
    12. LOSE: Сделка провалена
    13. APOLOGY: Анализ причины провала
    """

    __tablename__ = "deal_stages"

    def __str__(self) -> str:
        return str(self.name)

    sort_order: Mapped[int] = mapped_column(
        unique=True, comment="Порядковый номер стадии"
    )
    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="stage", foreign_keys="[Deal.stage_id]"
    )
