from collections.abc import Awaitable
from typing import Any, Callable, Generic, Type, TypeVar

from fastapi import HTTPException, status
from sqlalchemy import Integer, delete, exists, select, update
from sqlalchemy.exc import IntegrityError, NoResultFound, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import logger
from db.postgres import Base
from models.bases import IntIdEntity, NameStrIdEntity
from schemas.base_schemas import CommonFieldMixin

from ..exceptions import ConflictException, CyclicCallException

# Дженерик для схем
SchemaTypeCreate = TypeVar("SchemaTypeCreate", bound=CommonFieldMixin)
SchemaTypeUpdate = TypeVar("SchemaTypeUpdate", bound=CommonFieldMixin)
ModelType = TypeVar("ModelType", bound=IntIdEntity | NameStrIdEntity)
ExternalIdType = TypeVar("ExternalIdType", int, str)


class BaseRepository(
    Generic[ModelType, SchemaTypeCreate, SchemaTypeUpdate, ExternalIdType]
):
    """Базовый репозиторий для CRUD операций"""

    model: Type[ModelType]
    _default_related_checks: list[tuple[str, Type[Base], str]] = []
    """
    Список проверок по умолчанию в формате:
    (атрибут_схемы, модель_бд, поле_модели)
    """
    _default_related_create: dict[str, tuple[Any, Any, bool]] = {}
    """
    Словарь проверок с созданием сущности по умолчанию в формате:
    {атрибут_схемы: (клиент, модель_бд, проверка обязательна )}
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def _exists(self, external_id: ExternalIdType) -> bool:
        """Проверяет существование сущности по external_id"""
        try:

            field_type = self.model.external_id.type

            # Явное приведение типа для Integer полей
            if isinstance(field_type, int) and isinstance(external_id, str):
                try:
                    external_id = int(external_id)  # type: ignore[assignment]
                except ValueError:
                    return False

            stmt = select(
                exists().where(self.model.external_id == external_id)
            )
            result = await self.session.execute(stmt)
            return bool(result.scalar())
        except SQLAlchemyError as e:
            logger.exception(
                "Database error checking entity existence "
                f"ID={external_id}: {str(e)}"
            )
            return False

    def _not_found_exception(
        self, external_id: ExternalIdType
    ) -> HTTPException:
        """Генерирует исключение для отсутствующей сущности"""
        entity_name = self.model.__name__
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity_name} with ID: {external_id} not found",
        )

    def _conflict_exception(
        self, external_id: ExternalIdType
    ) -> ConflictException:
        """Генерирует исключение для конфликта дубликатов"""
        entity_name = self.model.__name__
        return ConflictException(entity_name, external_id)

    async def create(
        self,
        data: SchemaTypeCreate,
        pre_commit_hook: Callable[..., Awaitable[None]] | None = None,
        post_commit_hook: Callable[..., Awaitable[None]] | None = None,
    ) -> ModelType:
        """Создает новую Сущность с проверкой на дубликаты"""
        if not data.external_id:
            logger.error("Update failed: Missing ID")
            raise ValueError("ID is required for update")
        external_id = data.external_id

        field_type = self.model.external_id.type

        # Явное приведение типа для Integer полей
        if isinstance(field_type, Integer) and isinstance(external_id, str):
            try:
                external_id = int(external_id)
                data.external_id = external_id
            except ValueError:
                raise ValueError("ID is not correct type")

        if await self._exists(external_id):
            logger.warning(
                f"Creation {self.model.__name__} conflict: "
                f"ID={external_id} already exists"
            )
            raise self._conflict_exception(external_id)
        try:
            obj = self.model(**data.model_dump_db())
            self.session.add(obj)

            if pre_commit_hook:
                await pre_commit_hook(obj, data)

            await self.session.flush()

            if post_commit_hook:
                await post_commit_hook(obj, data)

            await self.session.commit()
            await self.session.refresh(obj)
            logger.info(f"{self.model.__name__} created: ID={external_id}")
            return obj  # type: ignore[no-any-return]
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(
                f"Integrity error creating {self.model.__name__} "
                f"ID={external_id}: {str(e)}"
            )
            raise self._conflict_exception(external_id) from e
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.exception(
                f"Database error creating {self.model.__name__} "
                f"ID={external_id}: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    f"Database operation failed creating {self.model.__name__}"
                ),
            ) from e

    async def get(self, external_id: ExternalIdType) -> ModelType | None:
        try:

            field_type = self.model.external_id.type

            if isinstance(field_type, Integer) and isinstance(
                external_id, str
            ):
                try:
                    external_id = int(external_id)  # type: ignore[assignment]
                except ValueError:
                    raise ValueError("ID is not correct type")
            stmt = select(self.model).where(
                self.model.external_id == external_id
            )
            result = await self.session.execute(stmt)
            entity = result.scalar_one_or_none()
            if not entity:
                logger.debug(
                    f"{self.model.__name__} not found: ID={external_id}"
                )
            return entity  # type: ignore[no-any-return]
        except SQLAlchemyError as e:
            logger.exception(
                f"Database error fetching {self.model.__name__} "
                f"ID={external_id}: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database operation failed",
            ) from e

    async def update(
        self,
        data: SchemaTypeUpdate | SchemaTypeCreate,
        pre_commit_hook: Callable[..., Awaitable[None]] | None = None,
        post_commit_hook: Callable[..., Awaitable[None]] | None = None,
    ) -> ModelType:
        """Обновляет существующую сущность"""
        if not data.external_id:
            logger.error("Update failed: Missing ID")
            raise ValueError("ID is required for update")

        external_id = data.external_id

        field_type = self.model.external_id.type

        if isinstance(field_type, Integer) and isinstance(external_id, str):
            try:
                external_id = int(external_id)
                data.external_id = external_id
            except ValueError:
                raise ValueError("ID is not correct type")

        if not await self._exists(external_id):
            logger.warning(
                f"Update failed: {self.model.__name__} "
                f"ID={external_id} not found"
            )
            raise self._not_found_exception(external_id)

        try:
            stmt = (
                update(self.model)
                .where(self.model.external_id == external_id)
                .values(data.model_dump_db(exclude_unset=True))
                .returning(self.model)
            )

            result = await self.session.execute(stmt)
            obj = result.scalar_one()

            if pre_commit_hook:
                await pre_commit_hook(obj, data)

            if post_commit_hook:
                await post_commit_hook(obj, data)

            await self.session.commit()
            logger.info(f"{self.model.__name__} updated: ID={external_id}")
            return obj  # type: ignore[no-any-return]
        except NoResultFound:
            await self.session.rollback()
            logger.warning(
                f"Update failed: {self.model.__name__} "
                f"ID={external_id} not found"
            )
            raise self._not_found_exception(external_id)
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.exception(
                f"Database error updating {self.model.__name__} "
                f"ID={external_id}: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database operation failed",
            ) from e

    async def delete(
        self,
        external_id: ExternalIdType,
        pre_delete_hook: Callable[..., Awaitable[None]] | None = None,
    ) -> bool:
        """Удаляет сущность по external_id, возвращает статус операции"""

        field_type = self.model.external_id.type

        if isinstance(field_type, Integer) and isinstance(external_id, str):
            try:
                external_id = int(external_id)  # type: ignore[assignment]
            except ValueError:
                raise ValueError("ID is not correct type")

        if not await self._exists(external_id):
            logger.warning(
                f"Delete failed: {self.model.__name__} "
                f"ID={external_id} not found"
            )
            raise self._not_found_exception(external_id)

        try:
            if pre_delete_hook:
                await pre_delete_hook(external_id)

            stmt = delete(self.model).where(
                self.model.external_id == external_id
            )
            result = await self.session.execute(stmt)

            if result.rowcount == 0:
                raise self._not_found_exception(external_id)

            await self.session.commit()
            logger.info(f"{self.model.__name__} deleted: ID={external_id}")
            return True
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.exception(
                f"Database error deleting {self.model.__name__} "
                f"ID={external_id}: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database operation failed",
            ) from e

    async def _check_object_exists(
        self, model: Type[Base], **filters: Any
    ) -> bool:
        """Проверяет существование объекта в БД с кэшированием результатов"""
        from ..dependencies_repo import get_exists_cache

        # Создаем уникальный ключ для кэша
        cache_key = (model, tuple(sorted(filters.items())))

        # Получаем кэш из контекста запроса
        cache = get_exists_cache()

        # Если результат уже в кэше - возвращаем его
        if cache_key in cache:
            return cache[cache_key]

        # Выполняем запрос, если нет в кэше
        stmt = select(model).filter_by(**filters).limit(1)
        result = await self.session.execute(stmt)
        exists = result.scalar_one_or_none() is not None

        # Сохраняем результат в кэш
        cache[cache_key] = exists
        return exists

    async def set_deleted_in_bitrix(
        self, external_id: ExternalIdType, is_deleted: bool = True
    ) -> bool:
        """
        Устанавливает флаг is_deleted_in_bitrix для сущности по external_id
        :param external_id: ID во внешней системе
        :param is_deleted: новое значение флага удаления
        :return: True, если обновление прошло успешно
        """

        field_type = self.model.external_id.type

        if isinstance(field_type, int) and isinstance(external_id, str):
            try:
                external_id = int(external_id)  # type: ignore[assignment]
            except ValueError:
                raise ValueError("ID is not correct type")

        if not await self._exists(external_id):
            logger.warning(
                f"Update failed: {self.model.__name__} "
                f"ID={external_id} not found"
            )
            raise self._not_found_exception(external_id)

        try:
            stmt = (
                update(self.model)
                .where(self.model.external_id == external_id)
                .values(is_deleted_in_bitrix=is_deleted)
                .execution_options(synchronize_session="fetch")
            )

            result = await self.session.execute(stmt)

            if result.rowcount == 0:
                logger.warning(
                    f"{self.model.__name__} with external_id={external_id} "
                    "not found"
                )
                return False

            await self.session.commit()
            logger.info(
                f"{self.model.__name__} ID={external_id} marked as "
                f"deleted={is_deleted}"
            )
            return True
        except NoResultFound:
            await self.session.rollback()
            logger.warning(
                f"Update failed: {self.model.__name__} "
                f"ID={external_id} not found"
            )
            raise self._not_found_exception(external_id)
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.exception(
                f"Database error updating {self.model.__name__} "
                f"ID={external_id}: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database operation failed",
            ) from e

    async def _get_related_checks(self) -> list[tuple[str, Type[Base], str]]:
        """Возвращает кастомные проверки для дочерних классов"""
        return self._default_related_checks

    async def _check_related_objects(
        self,
        data: SchemaTypeCreate | SchemaTypeUpdate,
        additional_checks: list[tuple[str, Type[Base], str]] | None = None,
    ) -> None:
        """Проверяет существование связанных объектов"""
        errors: list[str] = []
        checks = await self._get_related_checks()

        if additional_checks:
            checks.extend(additional_checks)

        for attr_name, model, filter_field in checks:
            value = getattr(data, attr_name, None)
            if value is not None and value:
                if not await self._check_object_exists(
                    model, **{filter_field: value}
                ):
                    errors.append(
                        f"{model.__name__} with {filter_field}={value} "
                        "not found"
                    )

        if errors:
            logger.exception(f"Related objects not found: {errors}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Related objects not found: {errors}",
            )

    async def _get_related_create(self) -> dict[str, tuple[Any, Any, bool]]:
        """Возвращает кастомные проверки для дочерних классов"""
        return self._default_related_create

    async def _create_or_update_related(
        self,
        data: SchemaTypeCreate | SchemaTypeUpdate,
        additional_checks: dict[str, tuple[Any, Any, bool]] | None = None,
        create: bool | None = False,
    ) -> None:
        from ..dependencies_repo import (
            get_creation_cache,
            get_exists_cache,
            get_update_needed_cache,
            get_updated_cache,
        )

        errors: list[str] = []
        checks = await self._get_related_create()
        # Для отслеживания уже обработанных сущностей
        updated_cache = get_updated_cache()
        creation_cache = get_creation_cache()
        update_needed_cache = get_update_needed_cache()

        if additional_checks:
            checks.update(additional_checks)

        for field_name, (client, model, required) in checks.items():
            value = getattr(data, field_name, None)

            if not value:
                if required and create:
                    errors.append(f"Missing required field: {field_name}")
                continue

            try:
                # Ключ для отслеживания уже обработанных сущностей
                entity_key = (model, value)
                # Пропускаем, если уже обрабатывали эту сущность
                if entity_key in updated_cache:
                    continue

                # Формируем ключ кэша для проверки существования
                filters = {"external_id": value}
                sorted_filters = tuple(sorted(filters.items()))
                cache_key = (model, sorted_filters)

                if not await self._check_object_exists(
                    model, external_id=value
                ):
                    if entity_key in creation_cache.keys():
                        update_needed_cache.add(entity_key)
                        raise CyclicCallException
                    await client.import_from_bitrix(value)  # ================
                    cache = get_exists_cache()
                    if cache_key in cache:
                        del cache[cache_key]
                else:
                    if entity_key in creation_cache.keys():
                        continue
                    await client.refresh_from_bitrix(value)  # ===============
                    updated_cache.add(entity_key)
                creation_cache[entity_key] = True
            except CyclicCallException:
                raise
            except Exception as e:
                errors.append(
                    f"{model.__name__} with id={value} failed: {str(e)}"
                )
        if errors:
            logger.exception(f"Related objects processing failed: {errors}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=", ".join(errors),
            )
