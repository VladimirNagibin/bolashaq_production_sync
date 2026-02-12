from schemas.enums import SourcesProductEnum
from schemas.supplier_schemas import (
    ImportConfigDetail,
)

from .supplier_repository import SupplierRepository


class SupplierClient:
    def __init__(
        self,
        supplier_repo: SupplierRepository,
    ):
        self.supplier_repo = supplier_repo

    async def get_supplier_config(
        self, source: SourcesProductEnum, config_name: str | None = None
    ) -> ImportConfigDetail | None:
        import_config = await self.supplier_repo.get_supplier_config(
            source, config_name
        )
        if not import_config:
            return None
        import_config_ = import_config.to_pydantic()
        if not import_config_.id:
            return None
        mapping = await self.supplier_repo.get_mapping_column(
            import_config_.id
        )
        if not mapping:
            return None
        return ImportConfigDetail(
            **import_config_.model_dump(),
            column_mappings=[m.to_pydantic() for m in mapping],
        )
