from schemas.enums import SourcesProductEnum
from schemas.supplier_schemas import (
    ImportConfigDetail,
)

from .repositories.import_config_repo import ImportConfigRepository
from .repositories.supplier_product_repo import SupplierProductRepository


class SupplierClient:
    def __init__(
        self,
        import_config_repo: ImportConfigRepository,
        supplier_product_repo: SupplierProductRepository,
    ):
        self.import_config_repo = import_config_repo
        self.supplier_product_repo = supplier_product_repo

    async def get_supplier_config(
        self, source: SourcesProductEnum, config_name: str | None = None
    ) -> ImportConfigDetail | None:
        import_config = await self.import_config_repo.get_by_source(
            source, config_name
        )
        return import_config
