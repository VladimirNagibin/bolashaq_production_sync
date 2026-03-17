import hashlib
import json
from typing import Any
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from redis.asyncio import Redis
from starlette.datastructures import FormData

from core.logger import logger
from schemas.enums import SourcesProductEnum
from schemas.fields import FIELDS_SUPPLIER_PRODUCT
from schemas.product_schemas import ProductCreate, ProductUpdate
from schemas.supplier_schemas import (
    ImportConfigDetail,
    ImportResult,
    SupplierCharacteristicUpdate,
    SupplierComplectUpdate,
    SupplierProductDetail,
    SupplierProductUpdate,
)
from services.products.product_services import ProductClient

from ..open_ai_services import OpenAIService
from .file_import_service import FileImportService
from .json_encoder import CustomJSONEncoder, PreprocessedDataSerializer
from .repositories.import_config_repo import ImportConfigRepository
from .repositories.supplier_product_repo import SupplierProductRepository


class SupplierClient:
    """
    Клиент для работы с поставщиками: импорт товаров, обработка данных, ревью.
    """

    # Константы для специальной обработки
    SOURCE_SPECIFIC_FIELDS = {
        SourcesProductEnum.LABSET: ["more_photo"],
    }

    def __init__(
        self,
        import_config_repo: ImportConfigRepository,
        supplier_product_repo: SupplierProductRepository,
        file_import_service: FileImportService,
        redis_client: Redis,
    ) -> None:
        """
        Инициализация клиента поставщика.

        Args:
            import_config_repo: Репозиторий конфигураций импорта
            supplier_product_repo: Репозиторий товаров поставщиков
            file_import_service: Сервис импорта файлов
        """
        self.import_config_repo = import_config_repo
        self.supplier_product_repo = supplier_product_repo
        self.file_import_service = file_import_service
        self.redis_client = redis_client
        self._openai_service = OpenAIService()

        logger.debug("SupplierClient initialized")

    async def get_supplier_config(
        self, source: SourcesProductEnum, config_name: str | None = None
    ) -> ImportConfigDetail | None:
        """
        Получает конфигурацию импорта для указанного источника.

        Args:
            source: Источник данных
            config_name: Название конфигурации (опционально)

        Returns:
            Optional[ImportConfigDetail]: Конфигурация или None
        """
        logger.debug(
            "Fetching supplier config",
            extra={"source": source.value, "config_name": config_name},
        )

        import_config = await self.import_config_repo.get_by_source(
            source, config_name
        )

        if import_config:
            logger.info(
                "Supplier config found",
                extra={"source": source.value, "config_name": config_name},
            )
        else:
            logger.warning(
                "Supplier config not found",
                extra={"source": source.value, "config_name": config_name},
            )

        return import_config

    async def import_products(
        self,
        config_key: str,
        file: UploadFile,
        config_name: str | None = None,
    ) -> ImportResult:
        """
        Импортирует товары из файла поставщика.

        Args:
            config_key: Ключ конфигурации (значение Enum)
            file: Загруженный файл
            config_name: Название конфигурации (опционально)

        Returns:
            ImportResult: Результат импорта

        Raises:
            HTTPException: При ошибках импорта
        """
        logger.info(
            "Starting products import",
            extra={
                "config_key": config_key,
                "config_name": config_name,
                "filename": file.filename,
                "file_size": file.size,
            },
        )

        try:
            # Преобразуем строку в Enum
            source_enum = SourcesProductEnum[config_key]
        except KeyError as e:
            error_msg = f"Configuration {config_key} not found"
            logger.error(
                error_msg, extra={"config_key": config_key}, exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=error_msg
            ) from e

        try:
            # Получаем конфигурацию из БД
            import_config = await self.get_supplier_config(
                source_enum, config_name
            )
            if not import_config:
                error_msg = f"Import configuration not found for {config_key}"
                logger.error(error_msg)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=error_msg
                )

            # Читаем файл
            content = await file.read()
            logger.debug(
                "File read successfully",
                extra={
                    "filename": file.filename,
                    "content_size": len(content),
                },
            )

            # Импортируем
            result = await self.file_import_service.import_file(
                content, import_config, file.filename
            )

            logger.info(
                "Products import completed",
                extra={
                    "source": source_enum.value,
                    "updated_count": result.updated_count,
                    "errors_count": result.errors,
                },
            )

            return result

        except HTTPException:
            # Пробрасываем HTTP исключения дальше
            raise
        except Exception as e:
            error_msg = f"Import error: {str(e)}"
            logger.error(
                error_msg,
                extra={"config_key": config_key, "filename": file.filename},
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg,
            ) from e

    async def get_supplier_product_review_data(
        self,
        supp_product_id: UUID,
    ) -> tuple[
        SupplierProductDetail,
        dict[str, dict[str, Any]],
        dict[str, dict[str, Any]],
    ]:
        """
        Получает данные товара поставщика для ревью с предобработкой.

        Args:
            supplier_product_id: ID товара поставщика

        Returns:
            Tuple с товаром, логами изменений и предобработанными данными

        Raises:
            HTTPException: Если товар не найден
        """
        logger.info(
            "Fetching supplier product for review",
            extra={"supplier_product_id": str(supp_product_id)},
        )

        # Получаем товар со связанными данными
        supp_product = await self.supplier_product_repo.get_with_relations(
            supp_product_id
        )
        if not supp_product:
            error_msg = f"SupplierProduct {supp_product_id} not found"
            logger.error(error_msg)
            raise HTTPException(status_code=404, detail=error_msg)

        # Получаем логи изменений
        change_log_repo = self.supplier_product_repo.change_log_repo
        change_logs = await change_log_repo.get_change_logs_by_product_id(
            supp_product_id
        )

        logger.debug(
            "Retrieved change logs",
            extra={
                "supplier_product_id": str(supp_product_id),
                "logs_count": len(change_logs),
            },
        )

        # Трансформируем логи
        transformed_logs = self._transform_change_log(change_logs)

        # Предобрабатываем данные через AI и правила
        preprocessed_data = await self._preprocess_supplier_data(
            supp_product, transformed_logs
        )
        logger.info(
            "Review data prepared",
            extra={
                "supplier_product_id": str(supp_product_id),
                "transformed_logs_count": len(transformed_logs),
                "preprocessed_fields_count": len(preprocessed_data),
            },
        )

        return supp_product, transformed_logs, preprocessed_data

    def _transform_change_log(
        self, change_logs: list[Any]
    ) -> dict[str, dict[str, Any]]:
        """
        Трансформирует список логов в словарь с последними значениями по полям

        Args:
            change_logs: Список логов изменений

        Returns:
            Dict[str, Dict[str, Any]]: Словарь вида
            {field_name: {old_value, new_value, created_at}}
        """
        transformed_logs: dict[str, dict[str, Any]] = {}

        for log in change_logs:
            field_name = log.field_name
            typed_old = self._cast_value_by_type(log.old_value, log.value_type)
            typed_new = self._cast_value_by_type(log.new_value, log.value_type)

            if field_name not in transformed_logs:
                # Первый лог для этого поля
                transformed_logs[field_name] = {
                    "old_value": typed_old,
                    "new_value": typed_new,
                    "min_created_at": log.created_at,  # храним мин время
                    "max_created_at": log.created_at,  # храним макс время
                    "old_value_at_min": typed_old,  # old_value при мин врем
                    "new_value_at_max": typed_new,  # new_value при макс врем
                }
            else:
                entry = transformed_logs[field_name]

                # Обновляем минимальное время и соответствующее old_value
                if log.created_at < entry["min_created_at"]:
                    entry["min_created_at"] = log.created_at
                    entry["old_value_at_min"] = typed_old

                # Обновляем максимальное время и соответствующее new_value
                if log.created_at > entry["max_created_at"]:
                    entry["max_created_at"] = log.created_at
                    entry["new_value_at_max"] = typed_new

        # Приводим к нужному формату
        result: dict[str, dict[str, Any]] = {}
        for field_name, entry in transformed_logs.items():
            result[field_name] = {
                "old_value": entry["old_value_at_min"],
                "new_value": entry["new_value_at_max"],
                "created_at": entry["max_created_at"],
            }

        # Добавляем заглушку для name
        if result and "name" not in result:
            result["name"] = {
                "old_value": None,
                "new_value": None,
                "created_at": None,
            }

        logger.debug(
            "Transformed change logs",
            extra={"fields_count": len(result)},
        )

        return result

    def _cast_value_by_type(
        self, value: str | None, value_type: str | None
    ) -> Any:
        """
        Приводит строковое значение к указанному типу.

        Args:
            value: Строковое значение
            value_type: Тип данных

        Returns:
            Any: Значение в нужном типе или исходная строка
        """
        if value is None:
            return None
        if not value_type:
            return value

        try:
            type_cast_map: dict[str, Any] = {
                "int": int,
                "float": float,
                "bool": lambda v: v.lower() in ("true", "1", "yes", "on"),
                "str": str,
            }

            cast_func = type_cast_map.get(value_type)
            if cast_func:
                return cast_func(value)

        except (ValueError, TypeError, AttributeError) as e:
            logger.warning(
                f"Failed to cast value to {value_type}",
                extra={"value": value, "error": str(e)},
            )

        return value

    async def _preprocess_supplier_data(
        self,
        supp_product: SupplierProductDetail,
        field_data: dict[str, dict[str, Any]],  # dict[str, Any],
        # config_name: str | None = None,
    ) -> dict[str, dict[str, Any]]:
        """
        Предобрабатывает данные товара: AI парсинг, определение категорий
        и т.д.

        Args:
            supplier_product: Товар поставщика
            field_data: Данные полей для обработки

        Returns:
            Dict[str, Dict[str, Any]]: Предобработанные данные
        """

        # Сериализуем данные в строку
        # (сортировка ключей важна для стабильности)
        data_str = json.dumps(
            field_data,
            cls=CustomJSONEncoder,
            sort_keys=True,
            ensure_ascii=False,
        )

        # Создаем хеш (чтобы ключ не был слишком длинным)
        data_hash = hashlib.md5(data_str.encode()).hexdigest()[:8]

        # Формируем итоговый ключ
        cache_key = f"preprocess_supplier_data:{supp_product.id}:{data_hash}"
        cached_json = await self.redis_client.get(cache_key)

        if cached_json:
            try:
                # result = json.loads(cached_json)
                result = PreprocessedDataSerializer.deserialize_from_cache(
                    cached_json
                )
                logger.info(f"Load data from cache with key: {cache_key}")
                return result
            except Exception as e:
                logger.error(f"Failed to load cached data: {e}")
        else:
            logger.warning(f"No cached data found for {cache_key}")
        preprocessed_data: dict[str, dict[str, Any]] = {}

        # 1. Обработка описания через AI
        if description_data := field_data.get("description"):
            ai_processed = await self._process_description_with_ai(
                description_data, supp_product
            )
            preprocessed_data.update(ai_processed)

        # 2. Определение категории
        if category_data := field_data.get("supplier_category"):
            category_processed = await self._determine_category(
                category_data=category_data,
                subcategory_data=field_data.get("supplier_subcategory"),
                supp_product=supp_product,
            )
            preprocessed_data.update(category_processed)

        # 3. Специфичная для источника обработка
        source_specific = await self._apply_source_specific_processing(
            supp_product.source, field_data, supp_product
        )
        preprocessed_data.update(source_specific)

        logger.debug(
            "Preprocessed supplier data",
            extra={
                "supplier_product_id": str(supp_product.id),
                "source": supp_product.source.value,
                "preprocessed_fields": list(preprocessed_data.keys()),
            },
        )
        await self.redis_client.set(
            cache_key,
            PreprocessedDataSerializer.serialize_for_cache(preprocessed_data),
            # json.dumps(preprocessed_data),
            ex=1800,  # Время жизни 30 минут (1800 сек)
        )
        return preprocessed_data

    async def _process_description_with_ai(
        self,
        description_data: dict[str, Any],
        supp_product: SupplierProductDetail,
    ) -> dict[str, dict[str, Any]]:
        """
        Обрабатывает описание товара через AI.

        Args:
            description_data: Данные описания
            supplier_product: Товар поставщика

        Returns:
            Dict[str, Dict[str, Any]]: Обработанные AI данные
        """
        result: dict[str, dict[str, Any]] = {}
        # Получаем новое значение описания
        new_description = description_data.get("new_value")
        if not new_description or not isinstance(new_description, str):
            logger.debug(
                "No valid description for AI processing",
                extra={"supplier_product_id": str(supp_product.id)},
            )
            return result

        try:
            # Парсим описание через AI
            ai_result = self._openai_service.parse_product_description(
                description_text=new_description,
                product_name=supp_product.name,
                article=supp_product.article,
                brand=supp_product.brend,
            )

            # Маппинг полей AI на поля товара
            field_mapping = {
                "announcement": "preview_for_offer",
                "description": "description_for_offer",
                "characteristics": "characteristics",
                "kit": "complects",
            }

            for ai_field, target_field in field_mapping.items():
                ai_value = getattr(ai_result, ai_field, None)
                if ai_value:
                    current_value = getattr(supp_product, target_field, None)
                    result[target_field] = {
                        "old_value": current_value,
                        "new_value": ai_value,
                    }

            logger.info(
                "AI description processing completed",
                extra={
                    "supplier_product_id": str(supp_product.id),
                    "fields_processed": list(result.keys()),
                },
            )

        except Exception as e:
            logger.error(
                f"AI processing failed: {e}",
                extra={"supplier_product_id": str(supp_product.id)},
                exc_info=True,
            )

        return result

    async def _determine_category(
        self,
        category_data: dict[str, Any],
        subcategory_data: dict[str, Any] | None,
        supp_product: SupplierProductDetail,
    ) -> dict[str, dict[str, Any]]:
        """
        Определяет ID категории в CRM по названию категории поставщика.

        Args:
            category_data: Данные категории
            subcategory_data: Данные подкатегории
            supplier_product: Товар поставщика

        Returns:
            Dict[str, Dict[str, Any]]: Данные категории
        """
        result: dict[str, dict[str, Any]] = {}

        try:
            # Получаем кэш категорий для источника
            category_cache = await self._get_category_cache(
                supp_product.source
            )
            if category_name := category_data.get("new_data"):
                subcategory_name = (
                    subcategory_data.get("new_data")
                    if subcategory_data
                    else None
                )
                category_key = (category_name, subcategory_name)
                if category_id := category_cache.get(category_key):
                    result["internal_section_id"] = {
                        "old_value": supp_product.internal_section_id,
                        "new_value": category_id,  # ID категории в Битрикс24
                    }

                    logger.debug(
                        "Category determined",
                        extra={
                            "supplier_product_id": str(supp_product.id),
                            "category": category_name,
                            "subcategory": subcategory_name,
                            "category_id": category_id,
                        },
                    )
                else:
                    logger.debug(
                        "Category not found in cache",
                        extra={
                            "supplier_product_id": str(supp_product.id),
                            "category": category_name,
                            "subcategory": subcategory_name,
                        },
                    )

        except Exception as e:
            logger.error(
                f"Category determination failed: {e}",
                extra={"supplier_product_id": str(supp_product.id)},
                exc_info=True,
            )

        return result

    async def _get_category_cache(
        self, source: SourcesProductEnum
    ) -> dict[tuple[str, str | None], int]:
        """
        Получает кэш соответствия категорий поставщика и CRM.

        Args:
            source: Источник данных

        Returns:
            Dict[Tuple[str, Optional[str]], int]:
            Словарь (категория, подкатегория) -> ID в CRM
        """
        # TODO: Реализовать получение кэша из БД или Redis
        # Пока возвращаем пустой словарь
        logger.debug(
            "Getting category cache",
            extra={"source": source.value, "cache_size": 0},
        )

        return {}

    async def _apply_source_specific_processing(
        self,
        source: SourcesProductEnum,
        field_data: dict[str, dict[str, Any]],
        supplier_product: SupplierProductDetail,
    ) -> dict[str, dict[str, Any]]:
        """
        Применяет специфичную для источника обработку данных.

        Args:
            source: Источник данных
            field_data: Данные полей
            supplier_product: Товар поставщика

        Returns:
            Dict[str, Dict[str, Any]]: Обработанные данные
        """
        result: dict[str, dict[str, Any]] = {}

        # Проверяем, есть ли специфичные поля для этого источника
        source_fields = self.SOURCE_SPECIFIC_FIELDS.get(source, [])

        for field_name in source_fields:
            if field_data.get(field_name):
                field_value = field_data[field_name].get("new_value")
                processed_values = self._process_source_specific_field(
                    source, field_name, field_value
                )

                if processed_values:
                    for new_name, processed_value in processed_values.items():
                        result[new_name] = {
                            "old_value": None,
                            "new_value": processed_value,
                        }

        return result

    def _process_source_specific_field(
        self,
        source: SourcesProductEnum,
        field_name: str,
        field_value: Any,
    ) -> dict[str, Any]:
        """
        Обрабатывает специфичное для источника поле.

        Args:
            source: Источник данных
            field_name: Название поля
            field_value: Значение поля

        Returns:
            Any: Обработанное значение
        """
        result: dict[str, Any] = {}
        if source == SourcesProductEnum.LABSET and field_name == "more_photo":
            if isinstance(field_value, str):
                # Разделяем строку с фото по разделителю
                more_photos = [
                    url.strip()
                    for url in field_value.split("|")
                    if url.strip()
                ]
                if more_photos:
                    result["detail_picture_process"] = more_photos[0]

                    # Оставшиеся фото -> more_photo (если есть)
                    if len(more_photos) > 1:
                        result["more_photo_process"] = more_photos[1:]
        return result

    async def get_review_data(
        self,
        supp_product: SupplierProductDetail,
        transformed_logs: dict[str, dict[str, Any]],
        preprocessed_data: dict[str, dict[str, Any]],
        product: ProductCreate | None = None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        simple_fields = FIELDS_SUPPLIER_PRODUCT.get("simple_fields", ())
        complex_fields = FIELDS_SUPPLIER_PRODUCT.get("complex_fields", ())
        # individual_fields = FIELDS_SUPPLIER_PRODUCT.get(
        #     "individual_fields", ()
        # )
        review_data: list[dict[str, Any]] = []
        review_complex_data: list[dict[str, Any]] = []
        for field_name, value_type in simple_fields:
            if field_name not in transformed_logs:
                continue
            value = transformed_logs[field_name]
            review_data.append(
                {
                    "field_name": field_name,
                    "old_value": value.get("old_value"),
                    "new_value": value.get("new_value"),
                    "current_product_value": getattr(
                        product, field_name, None
                    ),
                    "value_type": value_type,
                }
            )
        for field_name, value_type in complex_fields:
            if field_name not in transformed_logs:
                continue
            value = transformed_logs[field_name]
            current_product_value = None
            product_value = getattr(product, field_name, None)
            if product_value:
                current_product_value = product_value.value
            review_data.append(
                {
                    "field_name": field_name,
                    "old_value": value.get("old_value"),
                    "new_value": value.get("new_value"),
                    "current_product_value": current_product_value,
                    "value_type": value_type,
                }
            )

        # TODO: added data to review_complex_data

        return review_data, review_complex_data

    async def process_review(
        self,
        supp_product_id: UUID,
        product_service: ProductClient,
        form_data: FormData,
    ) -> SourcesProductEnum:
        is_validated = form_data.get("is_validated") == "on"
        should_export_to_crm = form_data.get("should_export_to_crm") == "on"
        needs_review = form_data.get("needs_review") == "on"
        is_deleted_in_bitrix = form_data.get("is_deleted_in_bitrix") == "on"
        logger.info(
            f"is_validated:{is_validated}, "
            f"should_export_to_crm:{should_export_to_crm}, "
            f"needs_review:{needs_review}, "
            f"is_deleted_in_bitrix:{is_deleted_in_bitrix}"
        )

        supp_result = await self.get_supplier_product_review_data(
            supp_product_id
        )
        supp_product, _, preprocessed_data = supp_result
        if not supp_product:
            error_msg = "Not found supplier_product with ID: {supp_product_id}"
            raise HTTPException(status_code=404, detail=error_msg)

        supp_product_update = SupplierProductUpdate()
        has_local_changes = False
        is_unlinked = False
        if supp_product.should_export_to_crm != should_export_to_crm:
            supp_product_update.should_export_to_crm = should_export_to_crm
            has_local_changes = True

        if not should_export_to_crm:
            if product_id := supp_product.product_id:
                is_unlinked = True
                has_local_changes = True
        else:

            needs_bitrix_update = False
            product = None
            if product_id := supp_product.product_id:
                product = await product_service.repo.get_by_id(product_id)

            if product:
                product_bitrix = ProductUpdate(external_id=product.external_id)
            else:
                # TODO: check filling name
                product_bitrix = ProductCreate(name="name")

            simple_fields = FIELDS_SUPPLIER_PRODUCT.get("simple_fields", ())
            complex_fields = FIELDS_SUPPLIER_PRODUCT.get("complex_fields", ())
            # individual_fields = FIELDS_SUPPLIER_PRODUCT.get(
            #     "individual_fields", ()
            # )
            for field_name, value_type in simple_fields:
                form_field_name = f"field_{field_name}"
                if form_field_name not in form_data:
                    continue
                update_in_crm = form_data.get(f"update_{field_name}") == "on"
                if not update_in_crm:
                    continue
                value = form_data.get(form_field_name, None)
                value_typed = self._cast_value_by_type(value, value_type)
                if value_typed is not None:
                    value_bitrix = getattr(product, field_name, None)
                    if (value_bitrix is None) or (
                        value_bitrix is not None
                        and value_bitrix != value_typed
                    ):
                        setattr(product_bitrix, field_name, value_typed)
                        needs_bitrix_update = True
                        logger.info(
                            f"{form_data.get(form_field_name, '')}"
                            f"{field_name}"
                            f"{value_type}:{update_in_crm}"
                        )
            for field_name, value_type in complex_fields:
                form_field_name = f"field_{field_name}"
                if form_field_name not in form_data:
                    continue
                update_in_crm = form_data.get(f"update_{field_name}") == "on"
                logger.info(
                    f"{form_data.get(form_field_name, '')}****{field_name}***"
                    f"{value_type}:{update_in_crm}"
                )

            if needs_bitrix_update:
                # TODO: update / create in bitrix
                ...

        supp_product_update.is_validated = True
        supp_product_update.needs_review = False
        change_log_repo = self.supplier_product_repo.change_log_repo
        await change_log_repo.mark_change_logs_as_processed(supp_product_id)
        result_update = await self._update_preprocessed_data(
            supp_product, supp_product_update, preprocessed_data
        )
        need_update, characteristics, complects = result_update
        has_local_changes = has_local_changes or need_update
        if has_local_changes:
            await self.supplier_product_repo.update(
                product_id=supp_product_id,
                product_data=supp_product_update,
                characteristics=characteristics,
                complects=complects,
                is_unlinked=is_unlinked,
            )
        return supp_product.source

    async def _update_preprocessed_data(
        self,
        supp_product: SupplierProductDetail,
        supp_product_update: SupplierProductUpdate,
        preprocessed_data: dict[str, dict[str, Any]],
    ) -> tuple[
        bool,
        list[SupplierCharacteristicUpdate] | None,
        list[SupplierComplectUpdate] | None,
    ]:
        need_update = False

        preview_for_offer = self.get_value_preprocessed_data(
            "preview_for_offer", preprocessed_data
        )
        if preview_for_offer:
            supp_product_update.preview_for_offer = preview_for_offer
            need_update = True
        description_for_offer = self.get_value_preprocessed_data(
            "description_for_offer", preprocessed_data
        )
        if description_for_offer:
            supp_product_update.description_for_offer = description_for_offer
            need_update = True

        characteristics: list[SupplierCharacteristicUpdate] | None = None
        complects: list[SupplierComplectUpdate] | None = None

        characters = self.get_value_preprocessed_data(
            "characteristics", preprocessed_data
        )
        if characters:
            characteristics = []
            for character in characters:
                characteristics.append(
                    SupplierCharacteristicUpdate(
                        name=character.name,
                        value=character.value,
                        unit=character.unit,
                    )
                )
        kits = self.get_value_preprocessed_data("complects", preprocessed_data)
        if kits:
            complects = []
            for kit in kits:
                specifications = None
                try:
                    if specifications := kit.specifications:
                        specifications = json.dumps(
                            specifications,
                            cls=CustomJSONEncoder,
                            sort_keys=True,
                            ensure_ascii=False,
                        )
                except Exception:
                    pass
                complects.append(
                    SupplierComplectUpdate(
                        name=kit.name,
                        code=kit.code,
                        description=kit.description,
                        specifications=specifications,
                    )
                )
        need_update = bool(need_update or characteristics or complects)
        return need_update, characteristics, complects

    def get_value_preprocessed_data(
        self, field_name: str, preprocessed_data: dict[str, dict[str, Any]]
    ) -> Any | None:
        if field_name in preprocessed_data:
            value_data = preprocessed_data.get(field_name)
            if value_data:
                return value_data.get("new_value", None)
        return None
