from typing import Sequence, Type

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import selectinload

from core.logger import logger
from db.postgres import Base
from models.bases import EntityType
from models.department_models import Department
from models.user_models import Manager as ManagerDB
from models.user_models import User as UserDB
from schemas.user_schemas import (
    ManagerCreate,
    ManagerUpdate,
    UserCreate,
    UserUpdate,
)

from ..base_repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[UserDB, UserCreate, UserUpdate, int]):

    model = UserDB
    entity_type = EntityType.USER

    async def create_entity(self, data: UserCreate) -> UserDB:
        """Создает нового пользователя с проверкой связанных объектов"""
        await self._check_related_objects(data)
        return await self.create(data=data)

    async def update_entity(self, data: UserCreate | UserUpdate) -> UserDB:
        """Обновляет существующего пользователя"""
        await self._check_related_objects(data)
        return await self.update(data=data)

    async def _get_related_checks(self) -> list[tuple[str, Type[Base], str]]:
        """Возвращает специфичные для User проверки"""
        return [
            # (атрибут схемы, модель БД, поле в модели)
            ("department_id", Department, "external_id"),
        ]

    async def get_manager(self, user_id: int) -> ManagerDB | None:
        """Получить менеджера по user_id"""
        try:
            query = (
                select(ManagerDB)
                .where(ManagerDB.user_id == user_id)
                .options(
                    selectinload(ManagerDB.user),
                )
            )
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(
                f"Database error getting manager by user_id {user_id}: {e}"
            )
            return None

    async def get_all_manager(
        self, skip: int = 0, limit: int = 100
    ) -> Sequence[ManagerDB]:
        """Получить всех менеджеров с пагинацией"""
        try:
            query = (
                select(ManagerDB)
                .offset(skip)
                .limit(limit)
                .options(
                    selectinload(ManagerDB.user),
                )
            )
            result = await self.session.execute(query)
            return result.scalars().all()  # type: ignore[no-any-return]
        except SQLAlchemyError as e:
            logger.error(f"Database error getting all managers: {e}")
            raise RuntimeError("Failed to retrieve managers") from e

    async def get_active_manager(self) -> Sequence[ManagerDB]:
        """Получить всех активных менеджеров"""
        try:
            query = (
                select(ManagerDB)
                .where(ManagerDB.is_active.is_(True))
                .options(
                    selectinload(ManagerDB.user),
                )
            )
            result = await self.session.execute(query)
            return result.scalars().all()  # type: ignore[no-any-return]
        except SQLAlchemyError as e:
            logger.error(f"Database error getting active managers: {e}")
            raise RuntimeError("Failed to retrieve active managers") from e

    async def create_manager(self, manager_data: ManagerCreate) -> ManagerDB:
        """Создать нового менеджера"""
        try:
            # Проверяем, существует ли уже менеджер с таким user_id
            existing_manager = await self.get(manager_data.user_id)
            if existing_manager:
                raise ValueError(
                    f"Менеджер с user_id {manager_data.user_id} уже существует"
                )

            manager = ManagerDB(
                user_id=manager_data.user_id,
                is_active=manager_data.is_active,
                default_company_id=manager_data.default_company_id,
                disk_id=manager_data.disk_id,
            )

            self.session.add(manager)
            await self.session.commit()
            await self.session.refresh(manager)

            # Загружаем связанные данные
            await self.session.refresh(manager, ["user", "default_company"])

            return manager
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Integrity error creating manager: {e}")
            raise ValueError(
                "Manager data violates database constraints"
            ) from e
        except ValueError as e:
            await self.session.rollback()
            logger.error(f"Validation error creating manager: {e}")
            raise
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Database error creating manager: {e}")
            raise RuntimeError(
                "Failed to create manager due to database error"
            ) from e

    async def update_manager(
        self, user_id: int, manager_data: ManagerUpdate
    ) -> ManagerDB | None:
        """Обновить данные менеджера"""
        try:
            query = (
                update(ManagerDB)
                .where(ManagerDB.user_id == user_id)
                .values(**manager_data.model_dump(exclude_unset=True))
                .returning(ManagerDB)
            )

            result = await self.session.execute(query)
            await self.session.commit()

            manager = result.scalar_one_or_none()
            if manager:
                # Загружаем связанные данные
                await self.session.refresh(
                    manager, ["user", "default_company"]
                )

            return manager
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Integrity error updating manager {user_id}: {e}")
            raise ValueError("Update violates database constraints") from e
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Database error updating manager {user_id}: {e}")
            raise RuntimeError(
                "Failed to update manager due to database error"
            ) from e

    async def delete_manager(self, user_id: int) -> bool:
        """Удалить менеджера"""
        try:
            manager = await self.get_manager(user_id)
            if not manager:
                return False

            await self.session.delete(manager)
            await self.session.commit()
            return True
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Database error deleting manager {user_id}: {e}")
            raise RuntimeError(
                "Failed to delete manager due to database error"
            ) from e

    async def set_activity_manager(
        self, user_id: int, is_active: bool
    ) -> ManagerDB | None:
        """Установить активность менеджера"""
        try:
            return await self.update_manager(
                user_id, ManagerUpdate(is_active=is_active)
            )
        except (ValueError, RuntimeError) as e:
            logger.error(f"Error setting activity for manager {user_id}: {e}")
            raise

    async def set_default_company_manager(
        self, user_id: int, company_id: int | None
    ) -> ManagerDB | None:
        """Установить компанию по умолчанию для менеджера"""
        try:
            return await self.update_manager(
                user_id, ManagerUpdate(default_company_id=company_id)
            )
        except (ValueError, RuntimeError) as e:
            logger.error(
                f"Error setting default company for manager {user_id}: {e}"
            )
            raise

    async def set_disk_id_manager(
        self, user_id: int, disk_id: int | None
    ) -> ManagerDB | None:
        """Установить disk_id для менеджера"""
        try:
            return await self.update_manager(
                user_id, ManagerUpdate(disk_id=disk_id)
            )
        except (ValueError, RuntimeError) as e:
            logger.error(f"Error setting disk ID for manager {user_id}: {e}")
            raise

    async def is_activity_manager(self, user_id: int) -> bool:
        """Установить активность менеджера"""
        try:
            manager = await self.get_manager(user_id)
            if manager:
                return manager.is_active  # type: ignore[no-any-return]
            return False
        except RuntimeError as e:
            logger.error(f"Error checking activity for manager {user_id}: {e}")
            return False
