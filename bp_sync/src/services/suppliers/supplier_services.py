from fastapi import HTTPException, UploadFile

from core.logger import logger
from schemas.enums import SourcesProductEnum
from schemas.supplier_schemas import (
    ImportConfigDetail,
    ImportResult,
)

from .file_import_service import FileImportService
from .repositories.import_config_repo import ImportConfigRepository
from .repositories.supplier_product_repo import SupplierProductRepository


class SupplierClient:
    def __init__(
        self,
        import_config_repo: ImportConfigRepository,
        supplier_product_repo: SupplierProductRepository,
        file_import_service: FileImportService,
    ):
        self.import_config_repo = import_config_repo
        self.supplier_product_repo = supplier_product_repo
        self.file_import_service = file_import_service

    async def get_supplier_config(
        self, source: SourcesProductEnum, config_name: str | None = None
    ) -> ImportConfigDetail | None:
        import_config = await self.import_config_repo.get_by_source(
            source, config_name
        )
        return import_config

    async def import_products(
        self,
        config: str,
        file: UploadFile,
        config_name: str | None = None,
    ) -> ImportResult:
        try:
            config_enum = SourcesProductEnum[config]
        except KeyError as e:
            logger.error(
                f"Configuration {config} not found: {str(e)}", exc_info=True
            )
            raise HTTPException(
                status_code=404, detail=f"Configuration {config} not found"
            )
        try:
            # Получаем конфигурацию из БД
            import_config = await self.get_supplier_config(
                config_enum, config_name
            )
            if not import_config:
                raise HTTPException(
                    status_code=404, detail="Configuration not found"
                )

            # Читаем файл
            content = await file.read()

            return await self.file_import_service.import_file(
                content, import_config, file.filename
            )

        except Exception as e:
            logger.error(f"Import error: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
