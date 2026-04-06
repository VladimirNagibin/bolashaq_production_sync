import asyncio
import re
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import pandas as pd

from api.v1.schemas.response_schemas import TokenData
from core.exceptions.supplier_exceptions import (
    DatabaseError,
    DataMappingError,
    FileProcessingError,
)
from core.logger import logger
from models.product_models import Product as ProductDB
from models.supplier_models import SupplierProduct
from schemas.change_log_schemas import ChangeLogUpdate
from schemas.enums import (
    SourceKeyField,
    SourcesProductEnum,
    TransformationRule,
)
from schemas.product_schemas import ProductUpdate
from schemas.supplier_schemas import (
    ImportConfigDetail,
    ImportResult,
    ProcessingResult,
    SupplierProductCreate,
    SupplierProductUpdate,
    UpdateResult,
)
from services.products.product_services import ProductClient

from .helpers.data_transformer import DataTransformer
from .repositories.supplier_product_repo import SupplierProductRepository


class FileImportService:
    """Сервис для импорта файлов с настройками из БД."""

    # Константы для настройки
    BITRIX_SYNC_BATCH_SIZE = 50
    BITRIX_SYNC_PAUSE_SECONDS = 1
    BITRIX_RETRY_ATTEMPTS = 3
    BITRIX_RETRY_DELAY_SECONDS = 2

    TRUE_VALUES = {"true", "yes", "1", "да", "y", "t", "1.0"}

    def __init__(
        self,
        supplier_product_repo: SupplierProductRepository,
        product_client: ProductClient,
    ) -> None:
        self._repo = supplier_product_repo
        self._product_client = product_client
        self._transformer = DataTransformer()

    async def import_file(
        self,
        file_content: bytes,
        config: ImportConfigDetail,
        token_data: TokenData,
        filename: str | None = None,
    ) -> ImportResult:
        """
        Основной метод импорта файла.

        Args:
            file_content: Содержимое файла в байтах
            config: Конфигурация импорта из БД
            filename: Имя файла (для логирования)

        Returns:
            ImportResult с результатами импорта

        """
        result = ImportResult()
        log_context = f"FileImport [{filename or 'unknown'}]"

        logger.info(f"{log_context}: Starting import process")

        try:
            # 1. Чтение файла согласно настройкам
            dataframe = await self._load_dataframe(
                file_content,
                config,
                log_context,
            )

            if dataframe.empty:
                logger.warning(
                    f"{log_context}: File is empty or no data found."
                )
                return result

            total_count = len(dataframe)
            logger.info(f"{log_context}: Loaded {total_count} rows from file.")

            # 2. Трансформация данных и маппинг колонок
            mapped_rows = await self._map_dataframe_columns(dataframe, config)
            if not mapped_rows:
                logger.warning(f"{log_context}: No data after mapping.")
                return result

            # 3. Загрузка существующих записей для сравнения
            existing_products = await self._fetch_existing_products(
                source=config.source,
                mapped_rows=mapped_rows,
                key_field=config.source_key_field,
            )
            logger.info(
                f"{log_context}: Found {len(existing_products)} existing "
                "records in DB."
            )

            # 3.1 TODO: Если опция "Обновить все", тогда ищем отсутствующие
            # в обновлениях и деактивируем.
            # Получить все позиции по поставщику для полного сравнения

            # 4. Подготовка пакетов для создания/обновления
            processing_result = await self._process_mapped_data(
                mapped_rows=mapped_rows,
                existing_products=existing_products,
                config=config,
                log_context=log_context,
                token_data=token_data,
            )

            # 5. Синхронизация с Битрикс
            if processing_result.bitrix_updates:
                await self._sync_with_bitrix(
                    processing_result,
                    log_context,
                    config,
                )

            # 6. Сохранение изменений в БД
            await self._save_import_results(
                processing_result, log_context, config
            )

            # Обновляем счетчики в результате
            result.total_count = total_count
            result.added_count = len(processing_result.products_to_create)
            result.updated_count = len(processing_result.products_to_update)
            result.bitrix_update_count = len(processing_result.bitrix_updates)
            result.errors_count = len(processing_result.errors)
            result.errors = processing_result.errors

            logger.info(
                f"{log_context}: Import finished successfully. "
                f"Added: {result.added_count}, "
                f"Updated: {result.updated_count}, "
                f"Bitrix: {result.bitrix_update_count}"
            )

        except FileProcessingError as e:
            error_msg = f"File processing error: {str(e)}"
            logger.error(f"{log_context}: {error_msg}")
            result.errors.append(error_msg)
        except DataMappingError as e:
            error_msg = f"Data mapping error: {str(e)}"
            logger.error(f"{log_context}: {error_msg}")
            result.errors.append(error_msg)
        except DatabaseError as e:
            error_msg = f"Database error: {str(e)}"
            logger.error(f"{log_context}: {error_msg}", exc_info=True)
            result.errors.append(error_msg)
        except Exception as e:
            error_msg = f"Critical import failure: {str(e)}"
            logger.error(f"{log_context}: {error_msg}", exc_info=True)
            result.errors.append(error_msg)

        return result

    # --- Data Loading & Mapping ---

    async def _load_dataframe(
        self, content: bytes, config: ImportConfigDetail, log_context: str
    ) -> pd.DataFrame:
        """Чтение файла в DataFrame согласно формату."""
        file_format = (config.file_format or "XLSX").upper()

        try:
            import io

            read_params: dict[str, Any] = {
                "header": None,
                "dtype": str,
                "keep_default_na": False,
                "na_values": [""],
            }

            if file_format == "CSV":
                read_params.update(
                    {
                        "encoding": config.encoding or "utf-8",
                        "sep": config.delimiter or ";",
                    }
                )
                dataframe = pd.read_csv(io.BytesIO(content), **read_params)
            elif file_format == "XLSX":
                read_params["engine"] = "openpyxl"
                dataframe = pd.read_excel(io.BytesIO(content), **read_params)
            else:
                raise ValueError(
                    f"Неподдерживаемый формат файла: {file_format}"
                )

            logger.debug(
                f"{log_context}: Raw data shape: {dataframe.shape}, "
                f"first 3 rows:\n{dataframe.head(3)}"
            )

            # Применяем настройки строк
            return self._apply_row_settings(dataframe, config, log_context)

        except pd.errors.EmptyDataError:
            raise FileProcessingError("File is empty")
        except pd.errors.ParserError as e:
            raise FileProcessingError(f"Failed to parse file: {str(e)}")
        except Exception as e:
            raise FileProcessingError(f"Error reading file: {str(e)}")

    def _apply_row_settings(
        self,
        dataframe: pd.DataFrame,
        config: ImportConfigDetail,
        log_context: str,
    ) -> pd.DataFrame:
        """Применение настроек строк к DataFrame."""
        df = dataframe.copy()

        # Обработка заголовков
        if config.header_row_index is not None:
            df = self._set_headers_from_row(
                df, config.header_row_index, log_context
            )

        # Пропуск строк до начала данных
        if config.data_start_row is not None:
            df = self._slice_data_start(df, config, log_context)

        # Очистка данных
        return self._clean_dataframe(df, log_context)

    def _set_headers_from_row(
        self, df: pd.DataFrame, header_idx: int, log_context: str
    ) -> pd.DataFrame:
        """Установка заголовков из указанной строки."""
        if not 0 <= header_idx < len(df):
            logger.warning(
                f"{log_context}: Header row {header_idx} out of range "
                f"(0-{len(df)-1})"
            )
            return df

        # Получаем и очищаем заголовки
        headers = df.iloc[header_idx].astype(str)
        headers = headers.str.strip()
        headers = headers.replace(["", "nan", "None", "NaN", "NaT"], "")

        # Генерируем имена для пустых колонок
        for i, header in enumerate(headers):
            if not header or pd.isna(header):
                headers.iloc[i] = f"column_{i}"

        # Устанавливаем заголовки и удаляем строку заголовка
        df.columns = headers
        df = df.drop(index=header_idx)

        logger.info(
            f"{log_context}: Headers set from row {header_idx}: "
            f"{list(df.columns)}"
        )

        return df

    def _slice_data_start(
        self, df: pd.DataFrame, config: ImportConfigDetail, log_context: str
    ) -> pd.DataFrame:
        """Обрезка данных до указанной строки начала."""
        if config.data_start_row is None:
            return df

        start_idx = config.data_start_row

        # Корректируем индекс, если уже удалили строку заголовка
        if (
            config.header_row_index is not None
            and config.header_row_index < start_idx
        ):
            start_idx -= 1

        if 0 <= start_idx < len(df):
            df = df.iloc[start_idx:]
            logger.info(
                f"{log_context}: Data trimmed to row {config.data_start_row}, "
                f"remaining {len(df)} rows"
            )
        else:
            logger.warning(
                f"{log_context}: Data start row {start_idx} out of range"
            )

        return df

    def _clean_dataframe(
        self, df: pd.DataFrame, log_context: str
    ) -> pd.DataFrame:
        """Очистка DataFrame от пустых строк."""
        df = df.reset_index(drop=True)

        # Удаляем полностью пустые строки
        before = len(df)
        df = df.dropna(how="all")

        if len(df) < before:
            logger.info(
                f"{log_context}: Removed {before - len(df)} empty rows"
            )

        return df

    async def _map_dataframe_columns(
        self, dataframe: pd.DataFrame, config: ImportConfigDetail
    ) -> list[dict[str, Any]]:
        """Применение маппинга колонок к DataFrame."""
        try:
            # Создаем карту колонок для быстрого доступа
            column_mappings = self._build_column_mappings(dataframe, config)

            if not column_mappings:
                raise DataMappingError("No valid column mappings found")

            # Преобразуем строки в словари
            mapped_data: list[dict[str, Any]] = []
            for row_tuple in dataframe.itertuples(index=False, name=None):
                mapped_row = self._map_single_row(row_tuple, column_mappings)
                if mapped_row:  # Только непустые строки
                    mapped_data.append(mapped_row)

            return mapped_data

        except Exception as e:
            raise DataMappingError(f"Failed to map columns: {str(e)}")

    def _build_column_mappings(
        self, df: pd.DataFrame, config: ImportConfigDetail
    ) -> list[dict[str, Any]]:
        """Построение карты маппинга колонок."""
        column_name_to_index = {
            name: idx for idx, name in enumerate(df.columns)
        }
        mappings: list[dict[str, Any]] = []

        for db_mapping in config.column_mappings:
            # Определяем индекс колонки
            col_idx = None

            if db_mapping.source_column_index is not None:
                col_idx = db_mapping.source_column_index
            elif (
                db_mapping.source_column_name
                and db_mapping.source_column_name in column_name_to_index
            ):
                col_idx = column_name_to_index[db_mapping.source_column_name]

            if col_idx is not None and 0 <= col_idx < len(df.columns):
                mappings.append(
                    {
                        "target_field": db_mapping.target_field,
                        "column_index": col_idx,
                        "transformation_rule": db_mapping.transformation_rule,
                        "force_import": db_mapping.force_import,
                        "sync_with_crm": db_mapping.sync_with_crm,
                    }
                )

        return mappings

    def _map_single_row(
        self, row: tuple[Any], column_mappings: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Маппинг одной строки данных."""
        mapped_row: dict[str, Any] = {}

        for mapping in column_mappings:
            try:
                raw_value = row[mapping["column_index"]]

                # Пропускаем пустые значения
                if self._is_empty_value(raw_value):
                    continue

                # Применяем трансформацию
                transformed_value = self._apply_transformation(
                    raw_value, mapping["transformation_rule"]
                )

                if transformed_value is not None:
                    mapped_row[mapping["target_field"]] = {
                        "value": transformed_value,
                        "force_import": mapping["force_import"],
                        "sync_with_crm": mapping["sync_with_crm"],
                    }

            except (IndexError, TypeError) as e:
                logger.debug(f"Error mapping row: {e}")
                continue

        return mapped_row

    def _is_empty_value(self, value: Any) -> bool:
        """Проверка на пустое значение."""
        if value is None:
            return True
        if isinstance(value, (float, int)) and pd.isna(value):
            return True
        if isinstance(value, str) and not value.strip():
            return True
        return False

    def _apply_transformation(self, value: Any, rule: str | None) -> Any:
        """Применение правил трансформации к значению."""
        if value is None or not rule:
            return value

        try:
            # String transformations
            if rule == TransformationRule.STRIP and isinstance(value, str):
                return value.strip()
            elif rule == TransformationRule.UPPER and isinstance(value, str):
                return value.upper()
            elif rule == TransformationRule.LOWER and isinstance(value, str):
                return value.lower()

            # Numeric transformations
            elif rule == TransformationRule.TO_FLOAT:
                return self._safe_float_conversion(value)
            elif rule == TransformationRule.TO_INT:
                return self._safe_int_conversion(value)
            elif rule == TransformationRule.TO_BOOL:
                return self._safe_bool_conversion(value)

            # Regex transformation
            elif rule and rule.startswith(TransformationRule.REGEX):
                return self._apply_regex_transformation(value, rule[3:])

            # Custom transformation
            elif rule and rule.startswith(TransformationRule.CUSTOM):
                method_name = rule[4:]
                return self._apply_custom_transformation(value, method_name)

        except Exception as e:
            logger.debug(
                f"Transformation failed for value '{value}' with rule "
                f"'{rule}': {e}"
            )
            return None

        return value

    def _safe_float_conversion(self, value: Any) -> float | None:
        """Безопасное преобразование в float."""
        try:
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                cleaned = value.strip().replace(",", ".")
                return float(cleaned)
        except (ValueError, TypeError):
            pass
        return None

    def _safe_int_conversion(self, value: Any) -> int | None:
        """Безопасное преобразование в int."""
        try:
            if isinstance(value, (int, float)):
                return int(value)
            if isinstance(value, str):
                cleaned = value.strip()
                return int(float(cleaned))
        except (ValueError, TypeError):
            pass
        return None

    def _safe_bool_conversion(self, value: Any) -> bool | None:
        """Безопасное преобразование в bool."""
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            return value.lower().strip() in self.TRUE_VALUES
        return None

    def _apply_regex_transformation(
        self, value: str, pattern: str
    ) -> str | None:
        """Применение регулярного выражения."""
        try:
            match = re.search(pattern, value)
            return match.group(1) if match and match.groups() else None
        except re.error as e:
            logger.debug(f"Regex error: {e}")
            return None

    def _apply_custom_transformation(
        self, value: Any, method_name: str
    ) -> Any:
        """Применение пользовательского метода трансформации."""
        method = getattr(self, method_name, None)
        if method and callable(method):
            try:
                return method(value)
            except Exception as e:
                logger.debug(
                    f"Custom transformation '{method_name}' failed: {e}"
                )
        return value

    def _transform_price(self, value: Any) -> float | None:
        """Пример пользовательской трансформации для цены."""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            # Удаляем валюту и пробелы
            cleaned = re.sub(r"[^\d,.]", "", value).replace(",", ".")
            try:
                return float(cleaned)
            except ValueError:
                pass
        return None

    # --- Fetching & Processing ---

    async def _fetch_existing_products(
        self,
        source: SourcesProductEnum,
        mapped_rows: list[dict[str, Any]],
        key_field: SourceKeyField,
    ) -> dict[str, SupplierProductCreate]:
        """Получение существующих записей из БД."""
        key_values = self._extract_key_values(mapped_rows, key_field)

        if not key_values:
            return {}

        try:
            filters = self._build_fetch_filters(source, key_field, key_values)
            records = await self._repo.get_by_filters(**filters)

            return {
                self._extract_record_key(record, key_field): record
                for record in records
            }

        except Exception as e:
            logger.error(f"Failed to fetch existing records: {e}")
            raise DatabaseError(f"Error fetching existing products: {str(e)}")

    def _extract_key_values(
        self, mapped_rows: list[dict[str, Any]], key_field: SourceKeyField
    ) -> list[Any]:
        """Извлечение значений ключевого поля из строк."""
        key_values: list[Any] = []
        key_field_name = key_field.value

        for row in mapped_rows:
            value_wrapper = row.get(key_field_name, {})
            raw_value = value_wrapper.get("value")

            if raw_value is not None:
                # Приводим тип ключа в зависимости от поля
                if key_field == SourceKeyField.EXTERNAL_ID:
                    try:
                        key_values.append(int(raw_value))
                    except (ValueError, TypeError):
                        pass
                else:
                    key_values.append(str(raw_value))

        return key_values

    def _build_fetch_filters(
        self,
        source: SourcesProductEnum,
        key_field: SourceKeyField,
        key_values: list[Any],
    ) -> dict[str, Any]:
        """Построение фильтров для запроса к БД."""
        filters: dict[str, Any] = {"source": source}

        if key_field == SourceKeyField.EXTERNAL_ID:
            filters["external_ids"] = key_values
        else:
            filters["codes"] = [str(v) for v in key_values]

        return filters

    def _extract_record_key(
        self, record: SupplierProductCreate, key_field: SourceKeyField
    ) -> str:
        """Извлечение значения ключевого поля из записи."""
        if key_field == SourceKeyField.EXTERNAL_ID:
            return str(record.external_id) if record.external_id else ""
        return record.code or ""

    async def _process_mapped_data(
        self,
        mapped_rows: list[dict[str, Any]],
        existing_products: dict[str, SupplierProductCreate],
        config: ImportConfigDetail,
        log_context: str,
        token_data: TokenData,
    ) -> ProcessingResult:
        """Обработка всех строк данных."""
        result = ProcessingResult()
        for idx, row in enumerate(mapped_rows):
            try:
                await self._process_single_row(
                    row_data=row,
                    existing_products=existing_products,
                    config=config,
                    result=result,
                    token_data=token_data,
                )
            except Exception as e:
                error_msg = f"Error processing row {idx}: {str(e)}"
                logger.error(f"{log_context}: {error_msg}", exc_info=True)
                result.errors.append(error_msg)
        return result

    async def _process_single_row(
        self,
        row_data: dict[str, Any],
        existing_products: dict[str, SupplierProductCreate],
        config: ImportConfigDetail,
        result: ProcessingResult,
        token_data: TokenData,
    ) -> None:
        """Обработка одной строки данных."""
        # Получаем значение ключевого поля
        key_field_name = config.source_key_field.value
        key_wrapper = row_data.get(key_field_name, {})
        raw_key = key_wrapper.get("value")

        if raw_key is None:
            logger.warning("Skipping row with null key field")
            return

        row_key = str(raw_key)
        existing_record = existing_products.get(row_key)

        if not existing_record:
            # Создание нового товара
            creates = await self._prepare_product_create(
                row_data,
                config.source,
                token_data,
                config.config_name,
            )
            result.change_logs.extend(creates.change_logs)
            if creates.local_create:
                result.products_to_create.append(creates.local_create)
            if creates.error:
                result.errors.append(creates.error)
        else:
            # Обновление существующего
            updates = await self._prepare_product_update(
                existing_product=existing_record,
                new_row_data=row_data,
                source=config.source,
                token_data=token_data,
                config_name=config.config_name,
            )

            if updates.local_update:
                result.products_to_update.append(updates.local_update)
            if updates.bitrix_update:
                result.bitrix_updates.append(updates.bitrix_update)
            if updates.change_logs:
                result.change_logs.extend(updates.change_logs)
            if updates.error:
                result.errors.append(updates.error)
            if updates.bitrix_to_supplier_product_map:
                result.bitrix_to_supplier_product_map.update(
                    updates.bitrix_to_supplier_product_map
                )

    async def _prepare_product_create(
        self,
        data: dict[str, Any],
        source: SourcesProductEnum,
        token_data: TokenData,
        config_name: str | None = None,
    ) -> UpdateResult:
        """Подготовка данных для создания нового товара."""
        change_logs: list[ChangeLogUpdate] = []
        product_name = "Undefined"
        try:
            # Извлекаем значения полей
            external_id = self._extract_field_value(data, "external_id")
            code = self._extract_field_value(data, "code")
            product_data: dict[str, Any] = {
                "source": source,
                "is_validated": False,
                "should_export_to_crm": False,
                "needs_review": True,
            }

            if external_id is not None:
                product_data["external_id"] = external_id
            if code is not None:
                product_data["code"] = code

            # Добавляем остальные поля
            for field, wrapper in data.items():
                if self._is_valid_field(field, wrapper):
                    value = wrapper.get("value")
                    product_data[field] = value
                    if field == "name":
                        product_name = value
                    if wrapper.get("sync_with_crm"):
                        change_logs.append(
                            self._create_change_log(
                                supplier_product_id=None,
                                source=source,
                                config_name=config_name,
                                field_name=field,
                                old_value=None,
                                new_value=value,
                                loaded_by_user_id=token_data.user_bitrix_id,
                            )
                        )
            # Сохраняем товар
            supplier_product = SupplierProductCreate(**product_data)

            created_product = await self._repo.create(supplier_product)

            if created_product:
                # Обновляем ID в логах
                for log in change_logs:
                    log.supplier_product_id = created_product.id
                return UpdateResult(
                    local_create=supplier_product, change_logs=change_logs
                )
            return UpdateResult(
                error=("Error creating supplier product " f"{product_name}")
            )
        except Exception as e:
            return UpdateResult(
                error=(
                    "Error during creating supplier product "
                    f"{product_name}: {str(e)}"
                )
            )

    def _extract_field_value(
        self, data: dict[str, Any], field_name: str
    ) -> Any:
        """Извлечение значения поля из данных."""
        wrapper = data.get(field_name, {})
        return wrapper.get("value")

    def _is_valid_field(self, field_name: str, wrapper: Any) -> bool:
        """Проверка валидности поля."""
        return (
            hasattr(SupplierProduct, field_name)
            and wrapper
            and isinstance(wrapper, dict)
            and wrapper.get("value") is not None
        )

    def _create_change_log(
        self,
        supplier_product_id: UUID | None,
        source: SourcesProductEnum,
        config_name: str | None,
        field_name: str,
        old_value: Any,
        new_value: Any,
        loaded_by_user_id: int | None,
        loaded_value: Any | None = None,
        is_processed: bool = False,
        force_import: bool = False,
        processed_at: datetime | None = None,
        processed_by_user_id: int | None = None,
        comment: str | None = None,
        crm_value_previous: Any | None = None,
    ) -> ChangeLogUpdate:
        """Создание объекта лога изменений."""
        return ChangeLogUpdate(
            supplier_product_id=supplier_product_id,
            source=source,
            config_name=config_name,
            field_name=field_name,
            old_value=str(old_value) if old_value is not None else None,
            new_value=str(new_value) if new_value is not None else None,
            value_type=(
                type(new_value).__name__ if new_value is not None else None
            ),
            loaded_by_user_id=loaded_by_user_id,
            loaded_value=(
                str(loaded_value) if loaded_value is not None else None
            ),
            is_processed=is_processed,
            force_import=force_import,
            processed_at=processed_at,
            processed_by_user_id=processed_by_user_id,
            comment=comment,
            crm_value_previous=(
                str(crm_value_previous)
                if crm_value_previous is not None
                else None
            ),
        )

    async def _prepare_product_update(
        self,
        existing_product: SupplierProductCreate,
        new_row_data: dict[str, Any],
        source: SourcesProductEnum,
        token_data: TokenData,
        config_name: str | None = None,
    ) -> UpdateResult:
        """Подготовка моделей обновления."""
        result = UpdateResult()
        product_name = existing_product.name
        try:
            local_update_data: dict[str, Any] = {
                "external_id": existing_product.external_id,
                "code": existing_product.code,
            }

            has_local_changes = False
            needs_bitrix_update = False

            # Подготовка модели Битрикса
            bitrix_update, bitrix_product = await self._prepare_bitrix_model(
                existing_product
            )
            if (
                bitrix_update
                and bitrix_update.external_id
                and existing_product.id
            ):
                result.bitrix_to_supplier_product_map = {
                    int(bitrix_update.external_id): existing_product.id
                }

            # Определяем режим обработки
            is_simple_mode = not (
                existing_product.should_export_to_crm
                or existing_product.needs_review
            )

            for field, wrapper in new_row_data.items():
                if not self._is_valid_field(field, wrapper):
                    continue

                new_value = wrapper.get("value")
                old_value = getattr(existing_product, field, None)

                if self._is_equal_or_none(old_value, new_value):
                    continue

                # Обновляем локальные данные
                local_update_data[field] = new_value
                has_local_changes = True

                if is_simple_mode:
                    continue

                # Обработка для CRM-режима
                needs_review = self._process_crm_update(
                    field=field,
                    new_value=new_value,
                    old_value=old_value,
                    wrapper=wrapper,
                    existing_product=existing_product,
                    bitrix_update=bitrix_update,
                    source=source,
                    config_name=config_name,
                    result=result,
                    loaded_by_user_id=token_data.user_bitrix_id,
                    bitrix_product=bitrix_product,
                )

                if wrapper.get("force_import"):
                    needs_bitrix_update = True

                if needs_review:
                    local_update_data["needs_review"] = True
                    has_local_changes = True

            # Формируем результат
            if has_local_changes:
                result.local_update = SupplierProductUpdate(
                    **local_update_data
                )

            if needs_bitrix_update and bitrix_update:
                result.bitrix_update = bitrix_update
            return result
        except Exception as e:
            return UpdateResult(
                error=(
                    "Error during updating supplier product "
                    f"{product_name}: {str(e)}"
                )
            )

    async def _prepare_bitrix_model(
        self, existing_product: SupplierProductCreate
    ) -> tuple[ProductUpdate | None, ProductDB | None]:
        """Подготовка модели для Битрикса."""
        try:
            if not existing_product.product_id:
                return None, None
            bitrix_product = (
                await self._product_client.repo.get_product_with_properties(
                    existing_product.product_id
                )
            )
            if not bitrix_product:
                return None, None
            return (
                ProductUpdate(external_id=bitrix_product.external_id),
                bitrix_product,
            )
        except Exception:
            return None, None

    def _is_equal_or_none(self, old_value: Any, new_value: Any) -> bool:
        if new_value is None or old_value == new_value:
            return True
        try:
            old_value = str(old_value)
            new_value = str(new_value)
            old_value = old_value.replace("\r\n", "\n").replace("\r", "\n")
            new_value = new_value.replace("\r\n", "\n").replace("\r", "\n")
            return bool(old_value == new_value)
        except (TypeError, ValueError):
            return False

    def _process_crm_update(
        self,
        field: str,
        new_value: Any,
        old_value: Any,
        wrapper: dict[str, Any],
        existing_product: SupplierProductCreate,
        bitrix_update: ProductUpdate | None,
        source: SourcesProductEnum,
        config_name: str | None,
        result: UpdateResult,
        loaded_by_user_id: int,
        bitrix_product: ProductDB | None,
    ) -> bool:
        """Обработка обновления для CRM."""
        force_import = wrapper.get("force_import")
        sync_with_crm = wrapper.get("sync_with_crm")

        # Принудительный импорт в CRM
        if force_import and bitrix_update and hasattr(bitrix_update, field):
            setattr(bitrix_update, field, new_value)
            current_bitrix_value = self._fetch_current_bitrix_value(
                field, bitrix_product
            )
            change_log = self._create_change_log(
                supplier_product_id=existing_product.id,
                source=source,
                config_name=config_name,
                field_name=field,
                old_value=old_value,
                new_value=new_value,
                loaded_by_user_id=loaded_by_user_id,
                force_import=True,
                loaded_value=new_value,
                is_processed=True,
                processed_at=datetime.now(timezone.utc),
                processed_by_user_id=loaded_by_user_id,
                crm_value_previous=current_bitrix_value,
            )
            result.change_logs.append(change_log)
        # Синхронизация через лог изменений
        elif sync_with_crm:
            change_log = self._create_change_log(
                supplier_product_id=existing_product.id,
                source=source,
                config_name=config_name,
                field_name=field,
                old_value=old_value,
                new_value=new_value,
                loaded_by_user_id=loaded_by_user_id,
            )
            result.change_logs.append(change_log)

            # Если товар не требует проверки, помечаем
            if not existing_product.needs_review:
                return True
        return False

    # --- Sync & Save ---

    async def _save_import_results(
        self,
        processing_result: ProcessingResult,
        log_context: str,
        config: ImportConfigDetail,
    ) -> None:
        """Сохранение результатов импорта в БД."""
        try:
            if processing_result.products_to_update:
                logger.info(
                    f"{log_context}: Updating "
                    f"{len(processing_result.products_to_update)} "
                    "existing products..."
                )
                await self._repo.update_products(
                    processing_result.products_to_update,
                    config.source_key_field,
                    config.source,
                )

            if processing_result.change_logs:
                logger.info(
                    f"{log_context}: Creating "
                    f"{len(processing_result.change_logs)} "
                    "change logs..."
                )
                await self._repo.change_log_repo.bulk_create_change_logs(
                    processing_result.change_logs
                )

        except Exception as e:
            raise DatabaseError(f"Failed to save import results: {str(e)}")

    async def _execute_with_retry(
        self, bitrix_update: ProductUpdate, log_context: str
    ) -> bool:
        """Выполняет запрос к Битрикс с несколькими попытками."""
        ext_id = getattr(bitrix_update, "external_id", "unknown")
        for attempt in range(self.BITRIX_RETRY_ATTEMPTS):
            try:
                await self._product_client.bitrix_client.update(bitrix_update)
                return True
            except Exception as e:
                if attempt < self.BITRIX_RETRY_ATTEMPTS - 1:
                    logger.warning(
                        f"{log_context}: Bitrix update failed for {ext_id} "
                        f"(attempt {attempt + 1}), "
                        f"retrying in {self.BITRIX_RETRY_DELAY_SECONDS}s... "
                        f"Error: {e}"
                    )
                    await asyncio.sleep(self.BITRIX_RETRY_DELAY_SECONDS)
                else:
                    raise

        return False

    async def _sync_with_bitrix(
        self,
        processing_result: ProcessingResult,
        log_context: str,
        config: ImportConfigDetail,
    ) -> None:
        """Синхронизация с Битрикс24."""
        bitrix_updates = processing_result.bitrix_updates
        if not bitrix_updates:
            logger.info(f"{log_context}: No updates to sync")
            return

        logger.info(
            f"{log_context}: Sending {len(bitrix_updates)} "
            "updates to Bitrix24..."
        )

        total = len(bitrix_updates)
        success_count = 0
        error_count = 0

        for i, bitrix_update in enumerate(bitrix_updates, 1):
            ext_id = getattr(bitrix_update, "external_id", "unknown")
            try:
                await self._execute_with_retry(bitrix_update, log_context)
                success_count += 1
                await self._mark_as_processed_intermediate(
                    bitrix_update, processing_result, config
                )
            except Exception as e:
                await self._unmark_as_processed(
                    bitrix_update, processing_result, config
                )

                error_count += 1
                logger.error(
                    f"{log_context}: Failed to update product {ext_id}: {e}",
                    exc_info=False,
                )
                # Продолжаем со следующими обновлениями

            # Пауза каждые N запросов
            if i % self.BITRIX_SYNC_BATCH_SIZE == 0 and i < total:
                logger.debug(
                    f"{log_context}: Processed {i}/{total} updates. "
                    f"Pausing for {self.BITRIX_SYNC_PAUSE_SECONDS} second..."
                )
                await asyncio.sleep(self.BITRIX_SYNC_PAUSE_SECONDS)

        logger.info(
            f"{log_context}: Bitrix sync completed. "
            f"Success: {success_count}, Errors: {error_count}, Total: {total}"
        )

    async def _unmark_as_processed(
        self,
        bitrix_update: ProductUpdate,
        processing_result: ProcessingResult,
        config: ImportConfigDetail,
    ) -> None:
        try:
            if not bitrix_update.external_id:
                return
            supplier_product_id = (
                processing_result.bitrix_to_supplier_product_map.get(
                    int(bitrix_update.external_id)
                )
            )
            if not supplier_product_id:
                return
            for log in processing_result.change_logs:
                if log.supplier_product_id == supplier_product_id:
                    log.loaded_value = None
                    log.is_processed = False
                    log.force_import = False
                    log.processed_at = None
                    log.processed_by_user_id = None
                    log.crm_value_previous = None

            try:
                supplier_product = await self._repo.get_with_relations(
                    supplier_product_id
                )
                key_field_name = config.source_key_field.value
                key = getattr(supplier_product, key_field_name, None)
                if key:
                    for (
                        supplier_product_upd
                    ) in processing_result.products_to_update:
                        if (
                            getattr(supplier_product_upd, key_field_name, None)
                            == key
                        ):
                            supplier_product_upd.needs_review = True
            except Exception as e:
                logger.warning(
                    f"Failed to unmark product {supplier_product_id} as "
                    f"needs_review: {e}"
                )

        except Exception as e:
            logger.error(f"{e}")

    async def _mark_as_processed_intermediate(
        self,
        bitrix_update: ProductUpdate,
        processing_result: ProcessingResult,
        config: ImportConfigDetail,
    ) -> None:
        try:
            if not bitrix_update.external_id:
                return
            supplier_product_id = (
                processing_result.bitrix_to_supplier_product_map.get(
                    int(bitrix_update.external_id)
                )
            )
            if not supplier_product_id:
                return
            for log in processing_result.change_logs:
                if (
                    log.supplier_product_id == supplier_product_id
                    and log.is_processed
                ):
                    log_repo = self._repo.change_log_repo
                    # Для промежуточных не обработанных полей помечаем
                    # как обработанное.
                    # force_import=True, processed_by_user_id=None
                    # Это означает автоматическое закрытие лога при загрузке
                    # новых значений
                    # TODO: для оптимизации только получать логи для
                    # обновления и обновлять пакетом
                    updated = await log_repo.mark_change_logs_as_processed(
                        supplier_product_id, log.field_name, force_import=True
                    )
                    if updated > 0:
                        # TODO: Checking supplier product. If not logs for
                        # update after marking - set not needs_review

                        logger.info(
                            "Updated {updated} logs for product "
                            f"{str(supplier_product_id)}"
                        )
        except Exception as e:
            logger.error(f"{e}")

    def _fetch_current_bitrix_value(
        self, field_name: str, bitrix_product: ProductDB | None
    ) -> str | None:
        if not bitrix_product:
            return None

        try:
            if hasattr(bitrix_product, field_name):
                if value := getattr(bitrix_product, field_name, None):
                    if result := self._transformer.convert_simple_to_string(
                        value
                    ):
                        return result
                return None

            for prop in bitrix_product.simple_properties:
                if prop.property_code == field_name:
                    return prop.value  # type: ignore[no-any-return]

            for prop in bitrix_product.properties:
                if prop.property_code == field_name:
                    return prop.text_field  # type: ignore[no-any-return]

            return None
        except Exception:
            return None
