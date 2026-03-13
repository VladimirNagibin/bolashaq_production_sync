from typing import Any
from uuid import UUID

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.supplier_models import SupplierProductChangeLog as SuppChangeLog
from schemas.change_log_schemas import (
    ChangeLogBase,
    ChangeLogInDB,
)

from .base_repository import BaseRepository


class ChangeLogRepository(BaseRepository[SuppChangeLog]):
    """Репозиторий для работы с маппингами колонок."""

    model = SuppChangeLog

    def __init__(self, session: AsyncSession):
        super().__init__(session, entity_name="ChangeLog")

    async def bulk_create_change_logs(
        self,
        changes: list[ChangeLogBase],
        batch_size: int = 1000,
    ) -> list[ChangeLogInDB]:
        """
        Массовое создание логов изменений
        """
        if not changes:
            self.logger.info("No changing logs ts to create")
            return []

        created_logs: list[ChangeLogInDB] = []

        for i in range(0, len(changes), batch_size):
            batch = changes[i : i + batch_size]

            batch_dicts: list[dict[str, Any]] = []
            for change_data in batch:
                change_dict = change_data.model_dump(exclude_unset=True)
                batch_dicts.append(change_dict)

            stmt = (
                insert(SuppChangeLog)
                .values(batch_dicts)
                .returning(SuppChangeLog)
            )
            result = await self._execute_query(
                stmt,
                operation="batch_create_change_log",
                batch_num=i // batch_size + 1,
                batch_size=len(batch),
            )
            inserted_rows = result.scalars().all()

            # Преобразуем в детальные схемы
            for row in inserted_rows:
                created_logs.append(ChangeLogInDB.model_validate(row))

            # Сбрасываем после каждого батча для получения ID
            await self._flush(
                f"batch_create_change_logs_batch_{i//batch_size + 1}"
            )

            self.logger.debug(
                f"Created batch {i//batch_size + 1}: "
                f"{len(inserted_rows)} products"
            )

            # Финальный коммит
        await self._commit("batch_create_change_logs")

        self.logger.info(
            f"Successfully created {len(created_logs)} products in "
            f"{(len(changes) + batch_size - 1) // batch_size} batches"
        )
        return created_logs

    async def get_change_logs_by_product_id(
        self, supp_product_id: UUID
    ) -> list[SuppChangeLog]:
        stmt = (
            select(SuppChangeLog)
            .where(SuppChangeLog.supplier_product_id == supp_product_id)
            .where(SuppChangeLog.is_processed.is_(False))
        )
        result = await self._execute_query(
            stmt,
            operation="get_change_log_by_product_id_for_rewiew",
            supp_product_id=str(supp_product_id),
        )

        change_logs = result.scalars().all()

        self.logger.info(
            "Fetched supplier products need review",
            extra={
                "supp_product_id": str(supp_product_id),
                "count": len(change_logs),
            },
        )

        return change_logs  # type: ignore[no-any-return]
