from typing import Any, Dict, Optional, Tuple
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from redis.asyncio import Redis
from starlette.datastructures import FormData

from core.exceptions.supplier_exceptions import NameNotFoundError
from core.logger import logger
from models.supplier_models import SupplierProductChangeLog as SuppChangeLog
from schemas.enums import SourcesProductEnum
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
    ) -> None:
        self.import_config_repo = import_config_repo
        self.supplier_product_repo = supplier_product_repo
        self.file_import_service = file_import_service

        # Инициализация помощников
        self._init_helpers(redis_client, product_client)

        logger.debug("SupplierClient initialized")

    def _init_helpers(
        self, redis_client: Redis, product_client: ProductClient
    ) -> None:
        """Инициализирует вспомогательные сервисы."""
        self.transformer = DataTransformer()
        self.preprocessor = SupplierDataPreprocessor(
            openai_service=OpenAIService(), redis_client=redis_client
        )
        self.review_handler = ReviewHandler(product_client)

    async def get_supplier_config(
        self, source: SourcesProductEnum, config_name: Optional[str] = None
    ) -> Optional[ImportConfigDetail]:
        """
        Получает конфигурацию импорта для указанного источника.
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
        config_name: Optional[str] = None,
    ) -> ImportResult:
        """
        Импортирует товары из файла поставщика.
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
            source_enum = self._parse_source_enum(config_key)
            import_config = await self._get_import_config_or_raise(
                source_enum, config_name
            )

            return await self._execute_import(file, import_config, source_enum)

        except HTTPException:
            raise
        except Exception as e:
            self._handle_import_error(e, config_key, file.filename)

    def _parse_source_enum(self, config_key: str) -> SourcesProductEnum:
        """Преобразует строку в Enum."""
        try:
            return SourcesProductEnum[config_key]
        except KeyError as e:
            error_msg = f"Configuration {config_key} not found"
            logger.error(
                error_msg, extra={"config_key": config_key}, exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=error_msg
            ) from e

    async def _get_import_config_or_raise(
        self, source: SourcesProductEnum, config_name: Optional[str]
    ) -> ImportConfigDetail:
        """Получает конфигурацию или вызывает исключение."""
        import_config = await self.get_supplier_config(source, config_name)
        if not import_config:
            error_msg = f"Import configuration not found for {source.value}"
            logger.error(error_msg)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=error_msg
            )
        return import_config

    async def _execute_import(
        self,
        file: UploadFile,
        import_config: ImportConfigDetail,
        source: SourcesProductEnum,
    ) -> ImportResult:
        """Выполняет импорт файла."""
        content = await file.read()
        logger.debug(
            "File read successfully",
            extra={
                "filename": file.filename,
                "content_size": len(content),
            },
        )

        result = await self.file_import_service.import_file(
            content, import_config, file.filename
        )

        logger.info(
            "Products import completed",
            extra={
                "source": source.value,
                "updated_count": result.updated_count,
                "errors_count": result.errors,
            },
        )

        return result

    def _handle_import_error(
        self, error: Exception, config_key: str, filename: str
    ) -> None:
        """Обрабатывает ошибки импорта."""
        error_msg = f"Import error: {str(error)}"
        logger.error(
            error_msg,
            extra={"config_key": config_key, "filename": filename},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from error

    async def get_supplier_product_review_data(
        self, supplier_product_id: UUID
    ) -> Tuple[
        SupplierProductDetail,
        Dict[str, Dict[str, Any]],
        Dict[str, Dict[str, Any]],
    ]:
        """
        Получает данные товара поставщика для ревью с предобработкой.
        """
        logger.info(
            "Fetching supplier product for review",
            extra={"supplier_product_id": str(supplier_product_id)},
        )

        # Получаем товар
        supplier_product = await self._get_product_or_raise(
            supplier_product_id
        )

        # Получаем логи изменений
        change_logs = await self._get_change_logs(supplier_product_id)

        # Трансформируем логи
        transformed_logs = self.transformer.transform_change_logs(change_logs)

        # Предобрабатываем данные
        preprocessed_data = await self.preprocessor.process(
            supplier_product, transformed_logs
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

    async def _get_product_or_raise(
        self, product_id: UUID
    ) -> SupplierProductDetail:
        """Получает товар или вызывает исключение."""
        product = await self.supplier_product_repo.get_with_relations(
            product_id
        )
        if not product:
            error_msg = f"SupplierProduct {product_id} not found"
            logger.error(error_msg)
            raise HTTPException(status_code=404, detail=error_msg)
        return product

    async def _get_change_logs(self, product_id: UUID) -> list[SuppChangeLog]:
        """Получает логи изменений для товара."""
        change_log_repo = self.supplier_product_repo.change_log_repo
        logs = await change_log_repo.get_change_logs_by_product_id(product_id)

        logger.debug(
            "Retrieved change logs",
            extra={
                "supplier_product_id": str(product_id),
                "logs_count": len(logs),
            },
        )

        return logs

    async def get_review_data(
        self,
        supplier_product: SupplierProductDetail,
        transformed_logs: Dict[str, Dict[str, Any]],
        preprocessed_data: Dict[str, Dict[str, Any]],
        product: Any,
    ) -> Tuple[list[Dict[str, Any]], list[Dict[str, Any]]]:
        """Делегирует подготовку контекста шаблона ReviewHandler."""
        return self.review_handler.prepare_review_context(
            supplier_product, transformed_logs, preprocessed_data, product
        )

    async def process_review(
        self,
        supplier_product_id: UUID,
        form_data: FormData,
    ) -> SourcesProductEnum:
        """Обрабатывает сабмит формы."""
        logger.info(
            "Processing review submission",
            extra={"supplier_product_id": str(supplier_product_id)},
        )

        try:
            # Получаем данные
            supplier_product, _, preprocessed_data = (
                await self.get_supplier_product_review_data(
                    supplier_product_id
                )
            )

            # Парсим флаги из формы
            flags = self._parse_form_flags(form_data)

            # Подготавливаем обновление
            update_data, is_unlinked = await self._prepare_product_update(
                supplier_product, flags, form_data, preprocessed_data
            )

            # Применяем обновление
            await self._apply_product_update(
                supplier_product_id,
                supplier_product,
                update_data,
                preprocessed_data,
                is_unlinked,
            )

            return supplier_product.source

        except NameNotFoundError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to process review: {e}",
                extra={"supplier_product_id": str(supplier_product_id)},
                exc_info=True,
            )
            raise HTTPException(
                status_code=500, detail="Failed to process review"
            )

    def _parse_form_flags(self, form_data: FormData) -> Dict[str, bool]:
        """Парсит флаги из формы."""
        return {
            "should_export_to_crm": form_data.get("should_export_to_crm")
            == "on",
            "is_validated": form_data.get("is_validated") == "on",
            "needs_review": form_data.get("needs_review") == "on",
            "is_deleted_in_bitrix": form_data.get("is_deleted_in_bitrix")
            == "on",
        }

    async def _prepare_product_update(
        self,
        supplier_product: SupplierProductDetail,
        flags: Dict[str, bool],
        form_data: FormData,
        preprocessed_data: Dict[str, Dict[str, Any]],
    ) -> Tuple[SupplierProductUpdate, bool]:
        """Подготавливает данные для обновления товара."""
        update_data = SupplierProductUpdate()
        is_unlinked = False
        has_changes = False

        # Обработка открепления
        if not flags["should_export_to_crm"] and supplier_product.product_id:
            is_unlinked = True
            has_changes = True

        # Обновление флага экспорта
        if (
            flags["should_export_to_crm"]
            != supplier_product.should_export_to_crm
        ):
            update_data.should_export_to_crm = flags["should_export_to_crm"]
            has_changes = True

        # Обработка экспорта в CRM
        if flags["should_export_to_crm"]:
            product_id = await self.review_handler.handle_submission(
                supplier_product, form_data, preprocessed_data
            )
            if product_id:
                update_data.product_id = product_id
                has_changes = True

        # Обновление флагов завершения
        if not supplier_product.is_validated:
            update_data.is_validated = True
            has_changes = True

        if supplier_product.needs_review:
            update_data.needs_review = False
            has_changes = True

        # Добавление предобработанных данных
        chars, complects, descriptions = (
            self.transformer.extract_preprocessed_data(preprocessed_data)
        )

        # Обновление описаний
        for key, value in descriptions.items():
            setattr(update_data, key, value)
            has_changes = True

        logger.info(has_changes)
        return update_data, is_unlinked

    async def _apply_product_update(
        self,
        product_id: UUID,
        supplier_product: SupplierProductDetail,
        update_data: SupplierProductUpdate,
        preprocessed_data: Dict[str, Dict[str, Any]],
        is_unlinked: bool,
    ) -> None:
        """Применяет обновление к товару."""
        # Помечаем логи как обработанные
        await self._mark_logs_processed(product_id)

        # Извлекаем сложные данные
        chars, complects, _ = self.transformer.extract_preprocessed_data(
            preprocessed_data
        )

        # Проверяем, есть ли изменения
        has_changes = self._has_changes(
            update_data, chars, complects, is_unlinked
        )

        if has_changes:
            await self.supplier_product_repo.update(
                product_id=product_id,
                product_data=update_data,
                characteristics=chars,
                complects=complects,
                is_unlinked=is_unlinked,
            )
            logger.info(f"Product {product_id} updated successfully")

    async def _mark_logs_processed(self, product_id: UUID) -> None:
        """Помечает логи как обработанные."""
        change_log_repo = self.supplier_product_repo.change_log_repo
        count = await change_log_repo.mark_change_logs_as_processed(product_id)

        logger.debug(
            f"Marked {count} logs as processed for product {product_id}"
        )

    def _has_changes(
        self,
        update_data: SupplierProductUpdate,
        characteristics: Optional[list[SupplierCharacteristicUpdate]],
        complects: Optional[list[SupplierComplectUpdate]],
        is_unlinked: bool,
    ) -> bool:
        """Проверяет, есть ли изменения для сохранения."""
        return any(
            [
                update_data.preview_for_offer,
                update_data.description_for_offer,
                update_data.product_id,
                update_data.should_export_to_crm is not None,
                update_data.is_validated is not None,
                update_data.needs_review is not None,
                characteristics,
                complects,
                is_unlinked,
            ]
        )
