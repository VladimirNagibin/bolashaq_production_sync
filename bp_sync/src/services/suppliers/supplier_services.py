from typing import Any
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from redis.asyncio import Redis
from starlette.datastructures import FormData

from core.exceptions.supplier_exceptions import NameNotFoundError
from core.logger import logger
from schemas.enums import SourcesProductEnum
from schemas.product_schemas import ProductCreate
from schemas.supplier_schemas import (
    ImportConfigDetail,
    ImportResult,
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
        self.product_section_client = product_section_client

        # Инициализация помощников
        self._category_cache = CategoryCacheService(
            redis_client=redis_client,
            supplier_product_repo=supplier_product_repo,
        )
        self._transformer = DataTransformer()
        self._preprocessor = SupplierDataPreprocessor(
            openai_service=OpenAIService(),
            redis_client=redis_client,
            category_cache=self._category_cache,
        )
        self._review_handler = ReviewHandler(
            product_client,
            product_section_client,
        )

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
            HTTPException: Если товар не найден
        """
        logger.info(
            "Fetching supplier product for review",
            extra={"supplier_product_id": str(supplier_product_id)},
        )
        # 1. Базовые данные
        supplier_product = await self.supplier_product_repo.get_with_relations(
            supplier_product_id
        )
        if not supplier_product:
            error_msg = f"SupplierProduct {supplier_product_id} not found"
            logger.error(error_msg)
            raise HTTPException(status_code=404, detail=error_msg)

        # 2. Логи изменений
        change_log_repo = self.supplier_product_repo.change_log_repo
        logs = await change_log_repo.get_change_logs_by_product_id(
            supplier_product_id
        )
        logger.debug(
            "Retrieved change logs",
            extra={
                "supplier_product_id": str(supplier_product_id),
                "logs_count": len(logs),
            },
        )

        # 3. Трансформация логов (через Transformer)
        transformed_logs = self._transformer.transform_change_logs(
            logs, supplier_product.name
        )

        # 4. Предобработка/AI (через Preprocessor с кэшированием)
        preprocessed_data = await self._preprocessor.process(
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

    async def get_review_data(
        self,
        supplier_product: SupplierProductDetail,
        transformed_logs: dict[str, dict[str, Any]],
        preprocessed_data: dict[str, dict[str, Any]],
        product: ProductCreate | None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Делегирует подготовку контекста шаблона ReviewHandler."""
        return self._review_handler.prepare_review_context(
            supplier_product, transformed_logs, preprocessed_data, product
        )

    async def process_review(
        self,
        supplier_product_id: UUID,
        form_data: FormData,
    ) -> SourcesProductEnum:
        """Обрабатывает сабмит формы."""
        # Получаем данные (включая кэшированные AI данные)
        supplier_product, _, preprocessed_data = (
            await self.get_supplier_product_review_data(supplier_product_id)
        )
        # Парсим флаги из формы
        flags = {
            "is_validated": form_data.get("is_validated") == "on",
            "should_export_to_crm": (
                form_data.get("should_export_to_crm") == "on"
            ),
            "needs_review": form_data.get("needs_review") == "on",
            "is_deleted_in_bitrix": (
                form_data.get("is_deleted_in_bitrix") == "on"
            ),
        }
        supp_update = SupplierProductUpdate()
        has_local_changes = False
        is_unlinked = False

        # Логика открепления товара
        if not flags["should_export_to_crm"] and supplier_product.product_id:
            is_unlinked = True
            has_local_changes = True
        if (
            flags["should_export_to_crm"]
            != supplier_product.should_export_to_crm
        ):
            supp_update.should_export_to_crm = flags["should_export_to_crm"]
            has_local_changes = True

        # Обработка данных товара (если выгрузка разрешена)
        if flags["should_export_to_crm"]:
            try:
                product_id, section_id = (
                    await self._review_handler.handle_submission(
                        supplier_product, form_data, preprocessed_data
                    )
                )

                if product_id:
                    supp_update.product_id = product_id
                    has_local_changes = True
                if (
                    section_id
                    and section_id != supplier_product.internal_section_id
                ):
                    supp_update.internal_section_id = section_id
                    has_local_changes = True
                    await self._update_categiry_cache(
                        supplier_product, section_id
                    )

            except NameNotFoundError as e:
                logger.warning(f"Review failed: {e}")
                raise  # Пробрасываем чтобы роутер сделал редирект с ошибкой
            except Exception as e:
                logger.error(
                    f"Error processing review submission: {e}", exc_info=True
                )
                raise HTTPException(
                    status_code=500, detail="Internal processing error"
                )

        # Обновляем локальные флаги
        if not supplier_product.is_validated:
            supp_update.is_validated = True
            has_local_changes = True
        if supplier_product.needs_review:
            supp_update.needs_review = False
            has_local_changes = True

        updated_preprocessed_data = (
            self._transformer.extract_preprocessed_data(preprocessed_data)
        )
        characteristics, complects, descriptions = updated_preprocessed_data

        if descriptions:
            for key, value in descriptions.items():
                setattr(supp_update, key, value)
            has_local_changes = True

        # Помечаем логи как обработанные
        change_log_repo = self.supplier_product_repo.change_log_repo
        await change_log_repo.mark_change_logs_as_processed(
            supplier_product_id
        )
        # Сохраняем в БД, если есть изменения
        if has_local_changes or characteristics or complects:
            await self.supplier_product_repo.update(
                product_id=supplier_product_id,
                product_data=supp_update,
                characteristics=characteristics,
                complects=complects,
                is_unlinked=is_unlinked,
            )

        return supplier_product.source

    async def _update_categiry_cache(
        self, supplier_product: SupplierProductDetail, section_id: int
    ) -> None:
        if not supplier_product.supplier_category:
            return None
        category_cache = await self._category_cache.get(
            supplier_product.source
        )
        key = (
            supplier_product.supplier_category,
            supplier_product.supplier_subcategory,
        )
        if category_cache.get(key) == section_id:
            return None
        category_cache[key] = section_id
        await self._category_cache.set(supplier_product.source, category_cache)
