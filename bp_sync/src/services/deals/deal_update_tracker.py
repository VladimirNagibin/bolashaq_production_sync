from typing import Any, Dict

from schemas.deal_schemas import DealCreate, DealUpdate


class DealUpdateTracker:
    """Трекер изменений для сделки"""

    def __init__(self) -> None:
        self._update_flags: Dict[str, bool] = {}
        self._deal_update = DealUpdate()

    def init_deal(self, external_id: int) -> None:
        setattr(self._deal_update, "external_id", external_id)

    def update_field(
        self, field_name: str, value: Any, deal_create: DealCreate
    ) -> None:
        """Обновляет поле и устанавливает флаг изменения"""
        setattr(self._deal_update, field_name, value)
        setattr(deal_create, field_name, value)
        self._update_flags[field_name] = True

    def get_field_update_status(self, field_name: str) -> bool:
        """Возвращает статус изменения поля"""
        return self._update_flags.get(field_name, False)

    def get_deal_update(self) -> DealUpdate:
        """Возвращает объект обновления сделки"""
        return self._deal_update

    def has_changes(self) -> bool:
        """Проверяет, есть ли изменения"""
        return any(self._update_flags.values())

    def reset(self) -> None:
        """Сбрасывает трекер"""
        self._update_flags.clear()
        self._deal_update = DealUpdate()
