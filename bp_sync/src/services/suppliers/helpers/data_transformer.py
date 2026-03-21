import json
from typing import Any, Callable

from core.logger import logger
from schemas.supplier_schemas import (
    SupplierCharacteristicUpdate,
    SupplierComplectUpdate,
)

from ..json_encoder import CustomJSONEncoder


class DataTransformer:
    """Сервис для трансформации данных и приведения типов."""

    # Типы для приведения
    TYPE_BOOL_TRUE_VALUES = ("true", "1", "yes", "on", "да")

    # Маппинг для приведения типов
    _TYPE_CAST_MAP: dict[str, Callable[[Any], Any]] = {
        "int": int,
        "float": float,
        "bool": (
            lambda v: str(v).lower() in DataTransformer.TYPE_BOOL_TRUE_VALUES
        ),
        "str": str,
    }

    @staticmethod
    def cast_value(value: str | None, value_type: str | None) -> Any:
        """
        Безопасно приводит строковое значение к указанному типу.
        """
        if value is None:
            return None
        if not value_type:
            return value

        try:
            cast_func = DataTransformer._TYPE_CAST_MAP.get(value_type)
            if cast_func:
                return cast_func(value)
        except (ValueError, TypeError, AttributeError) as e:
            logger.warning(
                f"Failed to cast value '{value}' to type '{value_type}': {e}"
            )
        return value

    @staticmethod
    def transform_change_logs(
        change_logs: list[Any],
        supplier_product_name: str,
    ) -> dict[str, dict[str, Any]]:
        """
        Агрегирует логи изменений, находя самое старое и самое новое значение.

        Args:
            change_logs: Список логов изменений

        Returns:
            Словарь с полями и их значениями
        """
        if not change_logs:
            logger.debug("No change logs to transform")
            return {}
        try:
            # Группируем логи по полям
            logs_by_field = DataTransformer._group_logs_by_field(change_logs)

            # Обрабатываем каждую группу
            result = DataTransformer._process_field_groups(logs_by_field)

            # Добавляем обязательное поле name
            result = DataTransformer._ensure_required_fields(
                result, supplier_product_name
            )

            logger.debug(f"Transformed {len(result)} fields from logs")
            return result

        except Exception as e:
            logger.error(
                f"Failed to transform change logs: {e}", exc_info=True
            )
            return {}

    @staticmethod
    def _group_logs_by_field(logs: list[Any]) -> dict[str, list[Any]]:
        """Группирует логи по имени поля."""
        groups: dict[str, list[Any]] = {}
        for log in logs:
            field_name = log.field_name
            if field_name not in groups:
                groups[field_name] = []
            groups[field_name].append(log)
        return groups

    @staticmethod
    def _process_field_groups(
        groups: dict[str, list[Any]],
    ) -> dict[str, dict[str, Any]]:
        """Обрабатывает группы логов, находя экстремумы."""
        result: dict[str, dict[str, Any]] = {}

        for field_name, field_logs in groups.items():
            # Сортируем логи по времени создания
            sorted_logs = sorted(field_logs, key=lambda x: x.created_at)

            oldest_log = sorted_logs[0]
            newest_log = sorted_logs[-1]

            result[field_name] = {
                "old_value": DataTransformer.cast_value(
                    oldest_log.old_value, oldest_log.value_type
                ),
                "new_value": DataTransformer.cast_value(
                    newest_log.new_value, newest_log.value_type
                ),
                "created_at": newest_log.created_at,
                "old_created_at": oldest_log.created_at,
            }

        return result

    @staticmethod
    def _ensure_required_fields(
        data: dict[str, dict[str, Any]],
        old_value: str,
    ) -> dict[str, dict[str, Any]]:
        """Добавляет обязательные поля, если они отсутствуют."""
        if data and "name" not in data:
            data["name"] = {
                "old_value": old_value,
                "new_value": None,
                "created_at": None,
            }
        return data

    def extract_preprocessed_data(
        self,
        preprocessed_data: dict[str, dict[str, Any]],
    ) -> tuple[
        list[SupplierCharacteristicUpdate] | None,
        list[SupplierComplectUpdate] | None,
        dict[str, str],
    ]:
        """
        Извлекает предобработанные данные в нужном формате.

        Returns:
            Кортеж (характеристики, комплектация, описания)
        """
        try:
            characteristics = self._extract_characteristics(preprocessed_data)
            complects = self._extract_complects(preprocessed_data)
            descriptions = self._extract_descriptions(preprocessed_data)

            return characteristics, complects, descriptions

        except Exception as e:
            logger.error(
                f"Failed to extract preprocessed data: {e}", exc_info=True
            )
            return None, None, {}

    def _extract_characteristics(
        self, data: dict[str, dict[str, Any]]
    ) -> list[SupplierCharacteristicUpdate] | None:
        """Извлекает характеристики из предобработанных данных."""
        char_data = self._get_field_value("characteristics", data)

        if not char_data:
            return None

        characteristics: list[SupplierCharacteristicUpdate] = []
        for char in char_data:
            try:
                characteristics.append(
                    SupplierCharacteristicUpdate(
                        name=char.name,
                        value=char.value,
                        unit=char.unit,
                    )
                )
            except Exception as e:
                logger.warning(
                    f"Failed to process characteristic: {e}",
                    extra={"characteristic": str(char)},
                )

        return characteristics

    def _extract_complects(
        self, data: dict[str, dict[str, Any]]
    ) -> list[SupplierComplectUpdate] | None:
        """Извлекает комплектацию из предобработанных данных."""
        kit_data = self._get_field_value("complects", data)

        if not kit_data:
            return None

        complects: list[SupplierComplectUpdate] = []
        for kit in kit_data:
            try:
                specifics = self.transform_specifications(kit.specifications)
                complects.append(
                    SupplierComplectUpdate(
                        name=kit.name,
                        code=kit.code,
                        description=kit.description,
                        specifications=specifics,
                    )
                )
            except Exception as e:
                logger.warning(
                    f"Failed to process kit: {e}", extra={"kit": str(kit)}
                )

        return complects

    def transform_specifications(self, specifications: Any) -> str | None:
        # Преобразование словаря из KitItem.specifications в строку
        # для SupplierComplectCreate.specifications
        if not specifications:
            return None
        specifics: list[str] = []
        try:
            for key, value in specifications.items():
                try:
                    specifics.append(f"{key}: {str(value)}")
                except Exception:
                    pass
            return ", ".join(specifics)
        except Exception:
            return None

    def _serialize_specifications(self, specifications: Any) -> str | None:
        """Сериализует спецификации в JSON строку."""
        if not specifications:
            return None

        try:
            return json.dumps(
                specifications,
                cls=CustomJSONEncoder,
                sort_keys=True,
                ensure_ascii=False,
            )
        except Exception as e:
            logger.warning(f"Failed to serialize specifications: {e}")
            return None

    def _extract_descriptions(
        self, data: dict[str, dict[str, Any]]
    ) -> dict[str, str]:
        """Извлекает описания из предобработанных данных."""
        descriptions: dict[str, str] = {}

        preview = self._get_field_value("preview_for_offer", data)
        if preview:
            descriptions["preview_for_offer"] = preview

        description = self._get_field_value("description_for_offer", data)
        if description:
            descriptions["description_for_offer"] = description

        return descriptions

    def _get_field_value(
        self, key: str, data: dict[str, dict[str, Any]]
    ) -> Any:
        """Безопасно получает значение поля из данных."""
        if key in data:
            return data[key].get("new_value")
        return None
