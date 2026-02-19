import re
from typing import Any

import pandas as pd

from core.logger import logger
from models.supplier_models import SupplierProduct
from schemas.enums import SourceKeyField, SourcesProductEnum
from schemas.product_schemas import ProductCreate, ProductUpdate
from schemas.supplier_schemas import (
    ImportConfigDetail,
    ImportResult,
    SupplierProductCreate,
    SupplierProductUpdate,
)
from services.products.product_services import ProductClient

from ..open_ai_services import OpenAIService
from .repositories.supplier_product_repo import SupplierProductRepository


class FileImportService:
    """Сервис для импорта файлов с настройками из БД."""

    def __init__(
        self,
        supplier_product_repo: SupplierProductRepository,
        product_client: ProductClient,
    ):
        self.supplier_product_repo = supplier_product_repo
        self.product_client = product_client
        self.open_al_service = OpenAIService()

    async def import_file(
        self,
        file_content: bytes,
        config: ImportConfigDetail,
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
        log_prefix = f"FileImport [{filename or 'unknown'}]"

        logger.info(f"{log_prefix}: Starting import process")

        try:
            # 1. Чтение файла согласно настройкам
            df = await self._load_dataframe(
                file_content,
                config,
                log_prefix,
            )
            if df.empty:
                logger.warning(
                    f"{log_prefix}: File is empty or no data found."
                )
                return result

            logger.info(f"{log_prefix}: Loaded {len(df)} rows from file.")

            # 2. Трансформация данных и маппинг колонок
            mapped_rows = await self._transform_and_map_rows(df, config)
            if not mapped_rows:
                logger.warning(f"{log_prefix}: No data after mapping.")
                return result

            # 3. Загрузка существующих записей для сравнения
            existing_products_map = await self._fetch_existing_products(
                source=config.source,
                mapped_rows=mapped_rows,
                key_field=config.source_key_field,
            )
            logger.info(
                f"{log_prefix}: Found {len(existing_products_map)} existing "
                "records in DB."
            )

            # 3.1 TODO: Если опция "Обновить все", тогда ищем отсутствующие
            # в обновлениях и деактивируем.

            # 4. Подготовка пакетов для создания/обновления
            products_to_create: list[SupplierProductCreate] = []
            products_to_update: list[SupplierProductUpdate] = []
            bitrix_updates: list[ProductCreate | ProductUpdate] = []

            # 5. Обработка данных
            for row in mapped_rows:
                try:
                    await self._process_single_row(
                        row_data=row,
                        existing_map=existing_products_map,
                        config=config,
                        result=result,
                        create_list=products_to_create,
                        update_list=products_to_update,
                        bitrix_list=bitrix_updates,
                    )
                except Exception as e:
                    error_msg = f"Error processing row: {str(e)}"
                    logger.error(f"{log_prefix}: {error_msg}", exc_info=True)
                    result.errors.append(error_msg)

            # 6. Сохранение изменений в БД
            if products_to_create:
                logger.info(
                    f"{log_prefix}: Creating {len(products_to_create)} "
                    "new products..."
                )
                await self.supplier_product_repo.create_products(
                    products_to_create, config.source_key_field
                )

            if products_to_update:
                logger.info(
                    f"{log_prefix}: Updating {len(products_to_update)} "
                    "existing products..."
                )
                await self.supplier_product_repo.update_products(
                    products_to_update, config.source_key_field, config.source
                )

            # 7. Синхронизация с Битрикс
            if bitrix_updates:
                logger.info(
                    f"{log_prefix}: Sending {len(bitrix_updates)} "
                    "updates to Bitrix24..."
                )
                # await self.product_client.create_or_update_product(
                #     bitrix_updates
                # )

            logger.info(
                f"{log_prefix}: Import finished successfully. "
                f"Added: {result.added_count}, "
                f"Updated: {result.updated_count}, "
                f"Bitrix: {result.bitrix_update_count}"
            )

        except ValueError as e:
            error_msg = f"Validation/Configuration error: {str(e)}"
            logger.error(f"{log_prefix}: {error_msg}")
            result.errors.append(error_msg)
        except Exception as e:
            error_msg = f"Critical import failure: {str(e)}"
            logger.error(f"{log_prefix}: {error_msg}", exc_info=True)
            result.errors.append(error_msg)
            # В зависимости от логики, можно пробрасывать исключение дальше
            # raise

        return result

    async def _load_dataframe(
        self, content: bytes, config: ImportConfigDetail, log_prefix: str
    ) -> pd.DataFrame:
        """Чтение файла в DataFrame согласно формату."""

        file_format = (config.file_format or "XLSX").upper()

        try:
            import io

            if file_format == "CSV":
                # Для CSV файлов
                df = pd.read_csv(
                    io.BytesIO(content),
                    encoding=config.encoding or "utf-8",
                    delimiter=config.delimiter or ";",
                    header=None,
                    dtype=str,
                )
            elif file_format == "XLSX":
                # Для Excel файлов
                df = pd.read_excel(
                    io.BytesIO(content),
                    header=None,
                    dtype=str,
                    engine="openpyxl",
                )
            else:
                raise ValueError(
                    f"Неподдерживаемый формат файла: {file_format}"
                )

            logger.info(
                f"{log_prefix}: Загружено {df.shape[0]} строк, "
                f"{df.shape[1]} колонок"
            )

            # Логируем первые строки для отладки
            logger.debug(f"{log_prefix}: Первые 3 строки:\n{df.head(3)}")

            # Применяем настройки строк
            df = self._apply_row_settings(df, config, log_prefix)

            return df

        except Exception as e:
            logger.error(
                f"{log_prefix}: Ошибка чтения файла: {str(e)}", exc_info=True
            )
            raise ValueError(f"Ошибка чтения файла: {str(e)}")

    def _apply_row_settings(
        self, df: pd.DataFrame, config: ImportConfigDetail, log_prefix: str
    ) -> pd.DataFrame:
        """Применение настроек строк к DataFrame."""

        # Обработка заголовков
        if config.header_row_index is not None:
            header_idx = config.header_row_index

            if 0 <= header_idx < len(df):
                # Получаем заголовки из указанной строки
                headers = df.iloc[header_idx].astype(str)

                # Очищаем заголовки
                headers = headers.str.strip()
                headers = headers.replace(
                    ["", "nan", "None", "NaN"], "column_"
                )

                # Если заголовок пустой, даем имя по индексу
                for i, h in enumerate(headers):
                    if pd.isna(h) or h == "" or h == "nan":
                        headers.iloc[i] = f"column_{i}"

                # Устанавливаем заголовки
                df.columns = headers

                # Удаляем строку заголовка из данных
                df = df.drop(index=header_idx)

                logger.info(
                    f"{log_prefix}: Заголовки установлены из строки "
                    f"{header_idx}: {list(df.columns)}"
                )
            else:
                logger.warning(
                    f"{log_prefix}: Строка заголовка {header_idx} "
                    f"вне диапазона (0-{len(df)-1})"
                )

        # Пропуск строк до начала данных
        if config.data_start_row is not None:
            start_idx = config.data_start_row

            # Корректируем индекс если уже удалили строку заголовка
            if (
                config.header_row_index is not None
                and config.header_row_index < start_idx
            ):
                start_idx -= 1

            if 0 <= start_idx < len(df):
                df = df.iloc[start_idx:]
                logger.info(
                    f"{log_prefix}: Данные обрезаны до строки "
                    f"{config.data_start_row}, осталось {len(df)} строк"
                )
            else:
                logger.warning(
                    f"{log_prefix}: Строка начала данных {start_idx} "
                    "вне диапазона"
                )

        # Сброс индекса
        df = df.reset_index(drop=True)

        # Удаляем пустые строки
        before = len(df)
        df = df.dropna(how="all")
        if len(df) < before:
            logger.info(
                f"{log_prefix}: Удалено {before - len(df)} пустых строк"
            )

        return df

    async def _transform_and_map_rows(
        self, df: pd.DataFrame, config: ImportConfigDetail
    ) -> list[dict[str, Any]]:
        """Применение маппинга колонок к DataFrame."""

        # Предварительная подготовка маппинга для быстрого доступа по индексу
        # Создаем словарь: {target_field:
        # (source_index_or_name, transformation_rule, force, sync)}
        field_mappings: list[dict[str, Any]] = []

        # Формируем карту имен колонок -> индексы для быстрого поиска
        col_name_to_index = {name: i for i, name in enumerate(df.columns)}

        for mapping in config.column_mappings:
            col_idx = None
            if (
                mapping.source_column_name
                and mapping.source_column_name in col_name_to_index
            ):
                col_idx = col_name_to_index[mapping.source_column_name]
            elif mapping.source_column_index:
                col_idx = mapping.source_column_index

            # Если колонка не найдена, пропускаем этот маппинг
            if col_idx is None:
                continue

            field_mappings.append(
                {
                    "target_field": mapping.target_field,
                    "col_idx": col_idx,
                    "rule": mapping.transformation_rule,
                    "force_import": mapping.force_import,
                    "sync_with_crm": mapping.sync_with_crm,
                }
            )

        mapped_data: list[dict[str, Any]] = []

        # Оптимизация: itertuples значительно быстрее iterrows
        # для больших объемов name=None возвращает обычные кортежи,
        # что еще быстрее
        for row_tuple in df.itertuples(index=False, name=None):
            row_dict: dict[str, Any] = {}

            for fm in field_mappings:
                try:
                    raw_value = row_tuple[fm["col_idx"]]
                except IndexError:
                    raw_value = None

                # Применение трансформации
                value = await self._apply_value_transformation(
                    raw_value, fm["rule"]
                )

                row_dict[fm["target_field"]] = {
                    "value": value,
                    "force_import": fm["force_import"],
                    "sync_with_crm": fm["sync_with_crm"],
                }

            mapped_data.append(row_dict)

        return mapped_data

    async def _apply_value_transformation(
        self, value: Any, rule: str | None
    ) -> Any:
        """Применение правил трансформации к значению."""
        if value is None:
            return None

        if not rule:
            return value

        try:
            if rule == "strip" and isinstance(value, str):
                return value.strip()
            elif rule == "upper" and isinstance(value, str):
                return value.upper()
            elif rule == "lower" and isinstance(value, str):
                return value.lower()
            elif rule == "float" and value is not None:
                return float(value)
            elif rule == "int" and value is not None:
                return int(float(value))
            elif rule == "bool" and value is not None:
                if isinstance(value, str):
                    return value.lower() in ["true", "yes", "1", "да"]
                return bool(value)
            elif rule.startswith("re:") and isinstance(value, str):
                pattern = rule[3:]
                match = re.search(pattern, value)
                return match.group(1) if match else None
            elif rule.startswith("def:") and value is not None:
                method = rule[4:]
                return getattr(self, method)(value)
        except (ValueError, TypeError, AttributeError):
            logger.debug(
                f"Transformation failed for value '{value}' with rule '{rule}'"
            )
            return None

        return value

    def _upd_price(self, value: Any) -> float:
        """Пример преобразования цены из _apply_value_transformation."""
        return float(value)

    async def _fetch_existing_products(
        self,
        source: SourcesProductEnum,
        mapped_rows: list[dict[str, Any]],
        key_field: SourceKeyField,
    ) -> dict[str, SupplierProductCreate]:
        """Получение существующих записей из БД."""

        key_values: list[Any] = []
        for row in mapped_rows:
            val = row.get(key_field.value, {}).get("value")
            if val is not None:
                # Приводим тип ключа к строке или int в зависимости от поля
                if key_field == SourceKeyField.EXTERNAL_ID:
                    try:
                        key_values.append(int(val))
                    except (ValueError, TypeError):
                        pass
                else:
                    key_values.append(str(val))

        if not key_values:
            return {}

        filters: dict[str, Any] = {"source": source}
        if key_field == SourceKeyField.EXTERNAL_ID:
            filters["external_ids"] = key_values
        else:
            filters["codes"] = key_values

        try:
            records = await self.supplier_product_repo.get_by_filters(
                **filters
            )

            return {
                self._get_record_key(rec, key_field): rec for rec in records
            }
        except Exception as e:
            logger.error(f"Failed to fetch existing records: {e}")
            return {}

    def _get_record_key(
        self, record: SupplierProductCreate, key_field: SourceKeyField
    ) -> str:
        """Получение значения ключевого поля из записи."""
        if key_field == SourceKeyField.EXTERNAL_ID:
            return str(record.external_id)
        return record.code or ""

    async def _process_single_row(
        self,
        row_data: dict[str, Any],
        existing_map: dict[str, SupplierProductCreate],
        config: ImportConfigDetail,
        result: ImportResult,
        create_list: list[SupplierProductCreate],
        update_list: list[SupplierProductUpdate],
        bitrix_list: list[ProductCreate | ProductUpdate],
    ) -> None:
        """Обработка одной строки данных."""

        key_val_obj = row_data.get(config.source_key_field.value, {})
        # Гарантируем, что ключ есть, иначе создадим дубликат или пропустим
        raw_key = key_val_obj.get("value")
        if raw_key is None:
            logger.warning("Skipping row with null key field")
            return

        row_key = str(raw_key)
        existing_record = existing_map.get(row_key)

        if not existing_record:
            # Создание нового товара
            new_product = await self._build_create_model(
                row_data, config.source
            )
            create_list.append(new_product)
            result.added_count += 1
        else:
            # Обновление существующего
            updates = await self._prepare_updates(
                existing_product=existing_record,
                new_row_data=row_data,
                source=config.source,
            )

            if updates[0]:
                update_list.append(updates[0])
                result.updated_count += 1

            if updates[1]:
                bitrix_list.append(updates[1])
                result.bitrix_update_count += 1

    async def _build_create_model(
        self,
        data: dict[str, Any],
        source: SourcesProductEnum,
    ) -> SupplierProductCreate:
        """Формирование модели для создания."""

        product_data: dict[str, Any] = {
            "external_id": int(data.get("external_id", {}).get("value", 0)),
            "name": data.get("name", {}).get("value", ""),
            "source": source,
            "is_validated": False,
            "should_export_to_crm": False,
        }

        # Добавляем остальные поля
        for field, wrapper in data.items():
            if (
                hasattr(SupplierProduct, field)
                and wrapper
                and wrapper.get("value") is not None
            ):
                product_data[field] = wrapper.get("value")

        # Предварительная обработка данных
        product_data = await self._preprocess_data(source, product_data)

        return SupplierProductCreate(**product_data)

    async def _prepare_updates(
        self,
        existing_product: SupplierProductCreate,
        new_row_data: dict[str, Any],
        source: SourcesProductEnum,
    ) -> tuple[
        SupplierProductUpdate | None, ProductCreate | ProductUpdate | None
    ]:
        """
        Подготовка моделей обновления.
        Возвращает кортеж (local_update, bitrix_update).
        """
        local_update: dict[str, Any] = {
            "external_id": existing_product.external_id,
            "code": existing_product.code,
        }
        # local_update = SupplierProductUpdate(
        #     external_id=existing_product.external_id,
        #     code=existing_product.code,
        # )

        has_local_changes = False
        bitrix_update: ProductCreate | ProductUpdate | None = None
        needs_bitrix_update = False

        # Инициализация модели Битрикса
        if existing_product.product_id:
            bitrix_update = ProductUpdate(
                internal_id=existing_product.product_id
            )
        else:
            bitrix_update = ProductCreate(name=existing_product.name)

        # Логика синхронизации
        if not existing_product.should_export_to_crm:
            # Простое обновление локальных данных
            for field, new_wrapper in new_row_data.items():
                if (
                    not hasattr(existing_product, field)
                    or not new_wrapper
                    or new_wrapper.get("value") is None
                ):
                    continue

                new_val = new_wrapper.get("value")
                old_val = getattr(existing_product, field)

                if old_val != new_val:
                    # setattr(local_update, field, new_val)
                    local_update[field] = new_val
                    has_local_changes = True
        else:
            # Сложная логика с синхронизацией с CRM
            for field, new_wrapper in new_row_data.items():
                if (
                    not hasattr(existing_product, field)
                    or not new_wrapper
                    or new_wrapper.get("value") is None
                ):
                    continue

                new_val = new_wrapper.get("value")
                old_val = getattr(existing_product, field)

                if old_val == new_val:
                    continue

                # Обновляем локальную модель в любом случае (как в оригинале)
                # setattr(local_update, field, new_val)
                local_update[field] = new_val
                has_local_changes = True

                force_import = new_wrapper.get("force_import")
                sync_with_crm = new_wrapper.get("sync_with_crm")

                if force_import and hasattr(bitrix_update, field):
                    setattr(bitrix_update, field, new_val)
                    needs_bitrix_update = True

                if sync_with_crm:
                    # TODO: Логика пометки для ручной обработки
                    pass

        # Предварительная обработка данных
        if has_local_changes:
            local_update = await self._preprocess_data(source, local_update)

        return (
            (
                SupplierProductUpdate(**local_update)
                if has_local_changes
                else None
            ),
            bitrix_update if needs_bitrix_update else None,
        )

    async def _preprocess_data(
        self,
        source: SourcesProductEnum,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        # TODO: Вычисляем раздел, обрабатываем описание и т.д.
        if source == SourcesProductEnum.LABSET:
            if description := data.get("description"):
                detail = self.open_al_service.parse_product_with_deepseek(
                    description,
                    name=data.get("name", ""),
                    article=data.get("article"),
                    brend=data.get("brend"),
                )
                if announce := detail.announcement:
                    data["preview_for_offer"] = announce
                if descr := detail.description:
                    data["description_for_offer"] = descr
                if characts := detail.characteristics:
                    data["characteristics"] = characts
                if kit := detail.kit:
                    data["complects"] = kit

        return data
