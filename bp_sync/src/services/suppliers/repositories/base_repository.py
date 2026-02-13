from typing import Any, Generic, TypeVar, cast
from uuid import UUID

from sqlalchemy import Result, ScalarResult, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.base import Executable

from core.exceptions.repo_exceptions import DatabaseOperationError
from core.logger import logger
from db.postgres import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """Базовый репозиторий с общими методами и логгированием."""

    model: type[T]

    def __init__(
        self, session: AsyncSession, entity_name: str = "Entity"
    ) -> None:
        self.session = session
        self.entity_name = entity_name
        self.logger = logger

    async def _execute_query(
        self, stmt: Executable, operation: str = "query", **context: Any
    ) -> Result[Any] | ScalarResult[Any]:
        """Выполнить запрос с логгированием и обработкой ошибок."""
        context_str = f" {context}" if context else ""
        self.logger.debug(f"Executing {operation}{context_str}")

        try:
            result = await self.session.execute(stmt)
            self.logger.debug(f"Successfully executed {operation}")
            return result
        except SQLAlchemyError as e:
            self.logger.error(
                f"Database {operation} failed: {str(e)}",
                exc_info=True,
                **context,
            )
            raise DatabaseOperationError(
                operation=operation,
                entity_name=self.entity_name,
                detail=str(e),
                original_error=e,
            ) from e

    async def _commit(self, operation: str = "commit", **context: Any) -> None:
        """Зафиксировать транзакцию с логгированием."""
        try:
            await self.session.commit()
            self.logger.debug(f"Successfully committed {operation}")
        except SQLAlchemyError as e:
            await self.session.rollback()
            self.logger.error(
                f"Commit failed during {operation}: {str(e)}",
                exc_info=True,
                **context,
            )
            raise DatabaseOperationError(
                operation="commit",
                entity_name=self.entity_name,
                detail=str(e),
                original_error=e,
            ) from e

    async def _flush(self, operation: str = "flush", **context: Any) -> None:
        """Сбросить изменения с логгированием."""
        try:
            await self.session.flush()
            self.logger.debug(f"Successfully flushed {operation}")
        except SQLAlchemyError as e:
            self.logger.error(
                f"Flush failed during {operation}: {str(e)}",
                exc_info=True,
                **context,
            )
            raise DatabaseOperationError(
                operation="flush",
                entity_name=self.entity_name,
                detail=str(e),
                original_error=e,
            ) from e

    async def get_by_id(self, id: UUID) -> T | None:
        """Получить запись по ID."""
        self.logger.info(f"Fetching {self.entity_name} by id, id={str(id)}")

        stmt: Executable = select(self.model).where(self.model.id == id)
        result = await self._execute_query(
            stmt, operation="get_by_id", id=str(id)
        )

        entity = result.scalar_one_or_none()

        if not entity:
            self.logger.warning(f"{self.entity_name} not found, id={str(id)}")

        return cast(T | None, entity)
