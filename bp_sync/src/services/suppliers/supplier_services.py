from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from redis.asyncio import Redis
from starlette.datastructures import FormData

from api.v1.schemas.response_schemas import TokenData
from core.exceptions.supplier_exceptions import (
    ImportConfigurationError,
    NameNotFoundError,
    SupplierProductNotFoundError,
)
from core.logger import logger
from schemas.change_log_schemas import ChangeLogUpdate
from schemas.enums import SourcesProductEnum
from schemas.product_schemas import ProductCreate
from schemas.supplier_schemas import (
    ImportConfigDetail,
    ImportResult,
    SupplierCharacteristicUpdate,
    SupplierComplectUpdate,
    SupplierProductDetail,
    SupplierProductUpdate,
)
from services.products.product_services import ProductClient
from services.productsections.productsection_services import (
    ProductsectionClient,
)

from ..open_ai_services import OpenAIService
from .file_import_service import FileImportService
from .helpers.category_cache import CategoryCacheService
from .helpers.data_transformer import DataTransformer
from .helpers.preprocessor import SupplierDataPreprocessor
from .helpers.review_handler import ReviewHandler
from .repositories.import_config_repo import ImportConfigRepository
from .repositories.supplier_product_repo import SupplierProductRepository


class SupplierClient:
    """
    Клиент для работы с поставщиками.
    Оркестрирует процесс: Импорт -> Подготовка -> Ревью -> Сохранение.
    """

    def __init__(
        self,
        import_config_repo: ImportConfigRepository,
        supplier_product_repo: SupplierProductRepository,
        file_import_service: FileImportService,
        redis_client: Redis,
        product_client: ProductClient,
        product_section_client: ProductsectionClient,
    ) -> None:
        self.import_config_repo = import_config_repo
        self.supplier_product_repo = supplier_product_repo
        self.file_import_service = file_import_service
        self.product_client = product_client
        self.product_section_client = product_section_client

        # Инициализация помощников
        self._category_cache = CategoryCacheService(
            redis_client=redis_client,
            supplier_product_repo=supplier_product_repo,
        )
        self._transformer = DataTransformer()
        self._preprocessor = SupplierDataPreprocessor(
            openai_service=OpenAIService(redis_client=redis_client),
            redis_client=redis_client,
            category_cache=self._category_cache,
        )
        self._review_handler = ReviewHandler(
            product_client,
            product_section_client,
        )

        logger.debug("SupplierClient initialized")

    # === Методы конфигурации ===

    async def get_supplier_config(
        self, source: SourcesProductEnum, config_name: str | None = None
    ) -> ImportConfigDetail:
        """
        Получает конфигурацию импорта для указанного источника.

        Args:
            source: Источник данных
            config_name: Название конфигурации (опционально)

        Returns:
            ImportConfigDetail: Конфигурация

        Raises:
            ImportConfigurationError: Если конфигурация не найдена
        """
        logger.debug(
            "Fetching supplier config",
            extra={"source": source.value, "config_name": config_name},
        )

        import_config = await self.import_config_repo.get_by_source(
            source, config_name
        )

        if not import_config:
            logger.warning(
                "Supplier config not found",
                extra={"source": source.value, "config_name": config_name},
            )
            raise ImportConfigurationError(source.value, config_name)

        logger.info(
            "Supplier config found",
            extra={"source": source.value, "config_name": config_name},
        )
        return import_config

    # === Методы импорта ===

    async def import_products(
        self,
        config_key: str,
        file: UploadFile,
        token_data: TokenData,
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
                "file_name": file.filename,
                "file_size": file.size,
            },
        )
        # Валидация ключа конфигурации
        try:
            source_enum = SourcesProductEnum(config_key)
        except (KeyError, ValueError) as e:
            error_msg = f"Invalid configuration key: {config_key}"
            logger.error(error_msg, extra={"config_key": config_key})
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=error_msg
            ) from e

        # Получение конфигурации
        try:
            import_config = await self.get_supplier_config(
                source_enum, config_name
            )
        except ImportConfigurationError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
            ) from e

        # Чтение и импорт файла
        try:
            content = await file.read()
            logger.debug(
                "File read successfully",
                extra={
                    "file_name": file.filename,
                    "content_size": len(content),
                },
            )

            result = await self.file_import_service.import_file(
                content, import_config, token_data, file.filename
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

        except IOError as e:
            error_msg = f"Failed to read file: {file.filename}"
            logger.error(error_msg, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg
            ) from e

    # === Методы получения данных для ревью ===

    async def get_supplier_product_review_data(
        self, supplier_product_id: UUID
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
            SupplierProductNotFoundError: Если товар не найден
        """
        logger.info(
            "Fetching supplier product for review",
            extra={"supplier_product_id": str(supplier_product_id)},
        )
        # 1. Базовые данные
        try:
            supplier_product = (
                await self.supplier_product_repo.get_with_relations(
                    supplier_product_id
                )
            )
        except Exception:
            supplier_product = None
        if not supplier_product:
            error_msg = f"SupplierProduct {supplier_product_id} not found"
            logger.error(error_msg)
            raise SupplierProductNotFoundError(supplier_product_id)

        # 2. Логи изменений
        change_log_repo = self.supplier_product_repo.change_log_repo
        change_logs = await change_log_repo.get_change_logs_by_product_id(
            supplier_product_id
        )
        logger.debug(
            "Retrieved change logs",
            extra={
                "supplier_product_id": str(supplier_product_id),
                "logs_count": len(change_logs),
            },
        )

        # 3. Трансформация логов (через Transformer)
        transformed_logs = self._transformer.transform_change_logs(
            change_logs, supplier_product.name
        )

        # 4. Предобработка/AI (через Preprocessor с кэшированием)
        preprocessed_data = await self._preprocessor.process(
            supplier_product,
            transformed_logs,
            await self.product_section_client.get_catalog_hierarchy_text(),
        )
        logger.info(
            "Review data prepared",
            extra={
                "supplier_product_id": str(supplier_product_id),
                "transformed_logs_count": len(transformed_logs),
                "preprocessed_fields_count": len(preprocessed_data),
            },
        )
        return supplier_product, transformed_logs, preprocessed_data

    async def get_review_context(
        self,
        supplier_product: SupplierProductDetail,
        transformed_logs: dict[str, dict[str, Any]],
        preprocessed_data: dict[str, dict[str, Any]],
        product: ProductCreate | None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Подготавливает контекст для отображения формы ревью."""
        return await self._review_handler.prepare_review_context(
            supplier_product, transformed_logs, preprocessed_data, product
        )

    async def get_ai_context(
        self,
        preprocessed_data: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Подготавливает данные из обработки AI для отображения формы ревью.
        """
        return await self._review_handler.prepare_ai_context(preprocessed_data)

    # === Методы обработки ревью (Запись) ===

    async def process_review(
        self,
        supplier_product_id: UUID,
        form_data: FormData,
        token_data: TokenData,
    ) -> SourcesProductEnum:
        """
        Обрабатывает отправку формы ревью.
        Оркестрирует обновление флагов, данных товара и кэша.
        """
        # 1. Получение актуальных данных
        try:
            supplier_product, _, preprocessed_data = (
                await self.get_supplier_product_review_data(
                    supplier_product_id
                )
            )
        except SupplierProductNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
            ) from e

        # 2. Парсинг данных формы
        flags = self._parse_form_flags(form_data)

        # 3. Подготовка данных для обновления
        update_data = SupplierProductUpdate()
        has_changes = False
        is_unlinked = False
        crm_field_updates: dict[str, Any] = {}
        old_crm_values: dict[str, Any] = {}

        # Логика открепления/изменения статуса выгрузки
        if not flags["should_export_to_crm"] and supplier_product.product_id:
            is_unlinked = True
            has_changes = True

        # Обновление флага выгрузки, если он изменился
        if (
            flags["should_export_to_crm"]
            != supplier_product.should_export_to_crm
        ):
            update_data.should_export_to_crm = flags["should_export_to_crm"]
            has_changes = True

        # 4. Обработка данных товара (если отмечена выгрузка в CRM)
        if flags["should_export_to_crm"]:
            try:
                (product_id, section_id, crm_field_updates, old_crm_values) = (
                    await self._review_handler.handle_submission(
                        supplier_product, form_data, preprocessed_data
                    )
                )

                if product_id:
                    update_data.product_id = product_id
                    has_changes = True
                if (
                    section_id
                    and section_id != supplier_product.internal_section_id
                ):
                    update_data.internal_section_id = section_id
                    has_changes = True
                    await self._update_category_cache(
                        supplier_product, section_id
                    )

            except HTTPException:
                raise
            except NameNotFoundError as e:
                logger.warning(
                    f"Review handling failed (NameNotFoundError): {e}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
                ) from e

        # 5. Подготовка данных для сохранения
        characteristics, complects, descriptions = (
            self._transformer.extract_preprocessed_data(preprocessed_data)
        )

        # 6. Обновление локальных полей из предобработанных данных
        if self._apply_preprocessed_updates(
            update_data, preprocessed_data, supplier_product, descriptions
        ):
            has_changes = True

        # 7. Обновление флагов статуса
        if not supplier_product.is_validated:
            update_data.is_validated = True
            has_changes = True
        if supplier_product.needs_review:
            update_data.needs_review = False
            has_changes = True

        # 8. Фиксация изменений в БД
        await self._save_changes(
            supplier_product_id=supplier_product_id,
            update_data=update_data,
            preprocessed_data=preprocessed_data,
            has_changes=has_changes,
            is_unlinked=is_unlinked,
            characteristics=characteristics,
            complects=complects,
            token_data=token_data,
            new_bitrix_dict=crm_field_updates,
            old_bitrix_dict=old_crm_values,
            source=supplier_product.source,
        )

        return supplier_product.source

    # === Приватные вспомогательные методы ===

    def _parse_form_flags(self, form_data: FormData) -> dict[str, bool]:
        """Извлекает булевы флаги из данных формы."""
        return {
            "is_validated": form_data.get("is_validated") == "on",
            "should_export_to_crm": (
                form_data.get("should_export_to_crm") == "on"
            ),
            "needs_review": form_data.get("needs_review") == "on",
            "is_deleted_in_bitrix": (
                form_data.get("is_deleted_in_bitrix") == "on"
            ),
        }

    def _apply_preprocessed_updates(
        self,
        update_data: SupplierProductUpdate,
        preprocessed_data: dict[str, dict[str, Any]],
        current_product: SupplierProductDetail,
        descriptions: dict[str, str],
    ) -> bool:
        """
        Применяет изменения из предобработанных данных к модели обновления.
        Возвращает True, если были изменения.
        """
        has_changes = False

        if descriptions:
            for key, value in descriptions.items():
                setattr(update_data, key, value)
            has_changes = True

        # Обработка детальной картинки
        detail_pic_data = preprocessed_data.get("detail_picture_process", {})
        if new_detail_pic := detail_pic_data.get("new_value"):
            if current_product.detail_picture != new_detail_pic:
                update_data.detail_picture = new_detail_pic
                has_changes = True

        # Обработка дополнительных изображений
        more_photo_data = preprocessed_data.get("more_photo_process", {})
        if new_more_photos := more_photo_data.get("new_value"):
            more_photos_str = ";".join(new_more_photos)
            if current_product.more_photo_process != more_photos_str:
                update_data.more_photo_process = more_photos_str
                has_changes = True

        return has_changes

    async def _save_changes(
        self,
        supplier_product_id: UUID,
        update_data: SupplierProductUpdate,
        preprocessed_data: dict[str, dict[str, Any]],
        has_changes: bool,
        is_unlinked: bool,
        characteristics: list[SupplierCharacteristicUpdate] | None,
        complects: list[SupplierComplectUpdate] | None,
        token_data: TokenData,
        new_bitrix_dict: dict[str, Any],
        old_bitrix_dict: dict[str, Any],
        source: SourcesProductEnum,
    ) -> None:
        """Сохраняет изменения в базу данных и помечает логи обработанными."""
        try:
            if has_changes or characteristics or complects:
                await self.supplier_product_repo.update(
                    product_id=supplier_product_id,
                    product_data=update_data,
                    characteristics=characteristics,
                    complects=complects,
                    is_unlinked=is_unlinked,
                )
                logger.info(
                    "Supplier product updated",
                    extra={
                        "supplier_product_id": str(supplier_product_id),
                        "is_unlinked": is_unlinked,
                    },
                )

            # Помечаем логи как обработанные
            change_log_repo = self.supplier_product_repo.change_log_repo
            change_bitrix_logs: list[ChangeLogUpdate] = []

            for field_name, loaded_value in new_bitrix_dict.items():
                if field_name == "external_id":
                    continue
                old_value = old_bitrix_dict.get(field_name)
                updated = await change_log_repo.mark_change_logs_as_processed(
                    supplier_product_id,
                    user_id=token_data.user_bitrix_id,
                    loaded_value=self._transformer.convert_to_string(
                        loaded_value
                    ),
                    crm_value_previous=self._transformer.convert_to_string(
                        old_value
                    ),
                    field_name=field_name,
                )
                if updated == 0:
                    change_bitrix_logs.append(
                        ChangeLogUpdate(
                            supplier_product_id=supplier_product_id,
                            source=source,
                            config_name=None,
                            field_name=field_name,
                            old_value=None,
                            new_value=None,
                            value_type=None,
                            loaded_by_user_id=token_data.user_bitrix_id,
                            loaded_value=self._transformer.convert_to_string(
                                loaded_value
                            ),
                            crm_value_previous=(
                                self._transformer.convert_to_string(old_value)
                            ),
                            is_processed=True,
                            force_import=False,
                            processed_at=datetime.now(timezone.utc),
                            processed_by_user_id=token_data.user_bitrix_id,
                            comment=None,
                        )
                    )
            if change_bitrix_logs:
                await change_log_repo.bulk_create_change_logs(
                    change_bitrix_logs
                )
            # Помечаем не найденные логи
            await change_log_repo.mark_change_logs_as_processed(
                supplier_product_id,
                user_id=token_data.user_bitrix_id,
            )
        except Exception as e:
            logger.error(
                "Failed to save supplier product "
                f"(id: {supplier_product_id}): {type(e).__name__}: {e}"
            )

    async def _update_category_cache(
        self, supplier_product: SupplierProductDetail, section_id: int
    ) -> None:
        """Обновляет кэш категорий в Redis, если привязка изменилась."""
        try:
            if not supplier_product.supplier_category:
                return
            category_cache = await self._category_cache.get(
                supplier_product.source
            )
            cache_key = (
                supplier_product.supplier_category,
                supplier_product.supplier_subcategory,
            )
            if category_cache.get(cache_key) == section_id:
                return
            category_cache[cache_key] = section_id
            await self._category_cache.set(
                supplier_product.source, category_cache
            )
            logger.debug(
                "Category cache updated",
                extra={
                    "source": supplier_product.source.value,
                    "key": cache_key,
                    "section_id": section_id,
                },
            )
        except Exception as e:
            logger.error(
                f"Error category cache updated: {e}",
                extra={
                    "source": supplier_product.source.value,
                    "section_id": section_id,
                },
            )
