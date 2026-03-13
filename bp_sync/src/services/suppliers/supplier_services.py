from typing import Any
from uuid import UUID

from fastapi import HTTPException, UploadFile

from core.logger import logger
from schemas.enums import SourcesProductEnum
from schemas.supplier_schemas import (
    ImportConfigDetail,
    ImportResult,
    SupplierProductDetail,
)

from ..open_ai_services import OpenAIService
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
        self._openai_service = OpenAIService()

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

    async def get_supplier_product_data_for_review(
        self, supp_product_id: UUID
    ) -> SupplierProductDetail:
        supp_product = await self.supplier_product_repo.get_with_relations(
            supp_product_id
        )
        if not supp_product:
            raise HTTPException(
                status_code=404,
                detail=f"SupplierProduct {supp_product_id} not found",
            )

        change_log_repo = self.supplier_product_repo.change_log_repo
        change_logs = await change_log_repo.get_change_logs_by_product_id(
            supp_product_id
        )
        change_logs_field = self._transform_change_log(change_logs)
        produced_logs_field = await self._preprocess_data(
            supp_product.source, change_logs_field
        )
        logger.info(produced_logs_field)
        return supp_product

    def _transform_change_log(
        self, change_logs: list[Any]
    ) -> dict[str, dict[str, Any]]:
        change_logs_field: dict[str, dict[str, Any]] = {}
        for log in change_logs:
            if log.field_name not in change_logs_field:
                change_logs_field[log.field_name] = {
                    "old_value": self._typing_value(
                        log.old_value, log.value_type
                    ),
                    "new_value": self._typing_value(
                        log.new_value,
                        log.value_type,
                    ),
                    "created_at": log.created_at,
                }
            else:
                created_existing = change_logs_field[log.field_name][
                    "created_at"
                ]
                if log.created_at > created_existing:
                    change_logs_field[log.field_name]["new_value"] = (
                        self._typing_value(log.new_value, log.value_type)
                    )
                else:
                    change_logs_field[log.field_name]["old_value"] = (
                        self._typing_value(log.old_value, log.value_type)
                    )
        return change_logs_field

    def _typing_value(self, value: str | None, value_type: str | None) -> Any:
        if value is None:
            return None
        if not value_type:
            return value
        try:
            if value_type == "int":
                return int(value)
            if value_type == "float":
                return float(value)
            if value_type == "bool":
                return value.lower() in ("true", "1")
            if value_type == "str":
                return value
        except Exception:
            return value

    async def _preprocess_data(
        self,
        source: SourcesProductEnum,
        data: dict[str, Any],
        config_name: str | None = None,
    ) -> dict[str, Any]:
        preprocess_data: dict[str, Any] = {}
        # TODO: Вычисляем раздел, обрабатываем описание и т.д.
        # if source == SourcesProductEnum.LABSET:
        #     if description := data.get("description"):
        #         detail = self._openai_service.parse_product_with_deepseek(
        #             description,
        #             name=data.get("name", ""),
        #             article=data.get("article"),
        #             brend=data.get("brend"),
        #         )
        #         if announce := detail.announcement:
        #             data["preview_for_offer"] = announce
        #         if descr := detail.description:
        #             data["description_for_offer"] = descr
        #         if characts := detail.characteristics:
        #             data["characteristics"] = characts
        #         if kit := detail.kit:
        #             data["complects"] = kit

        return preprocess_data
