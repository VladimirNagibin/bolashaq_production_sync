import asyncio
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Optional, Sequence, Type

from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, load_only, selectinload

from core.logger import logger
from db.postgres import Base
from models.company_models import Company as CompanyDB
from models.contact_models import Contact as ContactDB
from models.deal_models import AdditionalInfo as AddInfoDB
from models.deal_models import Deal as DealDB
from models.deal_stage_models import DealStage
from models.lead_models import Lead as LeadDB
from models.timeline_comment_models import TimelineComment
from models.user_models import User as UserDB
from schemas.deal_schemas import (
    AddInfoCreate,
    AddInfoUpdate,
    DealCreate,
    DealUpdate,
)
from schemas.enums import DealStatusEnum, EntityType

from ..base_repositories.base_repository import BaseRepository
from ..exceptions import ConflictException

if TYPE_CHECKING:
    from ..companies.company_services import CompanyClient
    from ..contacts.contact_services import ContactClient
    from ..leads.lead_services import LeadClient
    from ..timeline_comments.timeline_comment_services import (
        TimelineCommentClient,
    )
    from ..users.user_services import UserClient


class DealRepository(BaseRepository[DealDB, DealCreate, DealUpdate, int]):
    """Репозиторий для работы со сделками"""

    model = DealDB
    entity_type = EntityType.DEAL

    def __init__(
        self,
        session: AsyncSession,
    ):
        super().__init__(session)
        self._user_client: Optional["UserClient"] = None
        self._user_client_initialized = False
        self._company_client: Optional["CompanyClient"] = None
        self._company_client_initialized = False
        self._contact_client: Optional["ContactClient"] = None
        self._contact_client_initialized = False
        self._lead_client: Optional["LeadClient"] = None
        self._llead_client_initialized = False
        self._timeline_comment_client: Optional["TimelineCommentClient"] = None
        self._timeline_comment_client_initialized = False

    def set_user_client(self, user_client: "UserClient") -> None:
        """Устанавливает UserClient после создания репозитория"""
        self._user_client = user_client
        self._user_client_initialized = True
        logger.debug("UserClient set for ContactRepository")

    @property
    def user_client(self) -> Optional["UserClient"]:
        """Ленивое свойство для доступа к UserClient"""
        if not self._user_client_initialized and self._user_client is None:
            logger.warning(
                "UserClient not initialized in ContactRepository. "
                "Call set_user_client() first or use methods "
                "that don't require UserClient."
            )
        return self._user_client

    def set_company_client(self, company_client: "CompanyClient") -> None:
        """Устанавливает CompanyClient после создания репозитория"""
        self._company_client = company_client
        self._company_client_initialized = True
        logger.debug("CompanyClient set for ContactRepository")

    @property
    def company_client(self) -> Optional["CompanyClient"]:
        """Ленивое свойство для доступа к CompanyClient"""
        if (
            not self._company_client_initialized
            and self._company_client is None
        ):
            logger.warning(
                "CompanyClient not initialized in DealRepository. "
                "Call set_company_client() first or use methods "
                "that don't require CompanyClient."
            )
        return self._company_client

    def set_contact_client(self, contact_client: "ContactClient") -> None:
        """Устанавливает ContactClient после создания репозитория"""
        self._contact_client = contact_client
        self._contact_client_initialized = True
        logger.debug("ContactClient set for ContactRepository")

    @property
    def contact_client(self) -> Optional["ContactClient"]:
        """Ленивое свойство для доступа к ContactClient"""
        if (
            not self._contact_client_initialized
            and self._contact_client is None
        ):
            logger.warning(
                "ContactClient not initialized in ContactRepository. "
                "Call set_contact_client() first or use methods "
                "that don't require ContactClient."
            )
        return self._contact_client

    def set_lead_client(self, lead_client: "LeadClient") -> None:
        """Устанавливает LeadClient после создания репозитория"""
        self._lead_client = lead_client
        self._lead_client_initialized = True
        logger.debug("LeadClient set for ContactRepository")

    @property
    def lead_client(self) -> Optional["LeadClient"]:
        """Ленивое свойство для доступа к LeadClient"""
        if not self._lead_client_initialized and self._lead_client is None:
            logger.warning(
                "LeadClient not initialized in ContactRepository. "
                "Call set_lead_client() first or use methods "
                "that don't require LeadClient."
            )
        return self._lead_client

    def set_timeline_comment_client(
        self, timeline_comment_client: "TimelineCommentClient"
    ) -> None:
        """Устанавливает TimelineCommentClient после создания репозитория"""
        self._timeline_comment_client = timeline_comment_client
        self._timeline_comment_client_initialized = True
        logger.debug("TimelineCommentClient set for ContactRepository")

    @property
    def timeline_comment_client(self) -> Optional["TimelineCommentClient"]:
        """Ленивое свойство для доступа к TimelineCommentClient"""
        if (
            not self._timeline_comment_client_initialized
            and self._timeline_comment_client is None
        ):
            logger.warning(
                "TimelineCommentClient not initialized in DealRepository. "
                "Call set_timeline_comment_client() first or use methods "
                "that don't require TimelineCommentClient."
            )
        return self._timeline_comment_client

    async def create_entity(self, data: DealCreate) -> DealDB:
        """Создает новую сделку с проверкой связанных объектов"""
        await self._check_related_objects(data)
        await self._create_or_update_related(data, create=True)
        deal = await self.create(data=data)
        asyncio.create_task(self.sync_timeline_comments(deal.external_id))
        return deal

    async def update_entity(self, data: DealUpdate | DealCreate) -> DealDB:
        """Обновляет существующую сделку"""
        await self._check_related_objects(data)
        await self._create_or_update_related(data)
        deal = await self.update(data=data)
        asyncio.create_task(self.sync_timeline_comments(deal.external_id))
        return deal

    async def _get_related_checks(self) -> list[tuple[str, Type[Base], str]]:
        """Возвращает специфичные для Deal проверки"""
        return [
            # (атрибут схемы, модель БД, поле в модели)
            ("stage_id", DealStage, "external_id"),
        ]

    async def _get_related_create(self) -> dict[str, tuple[Any, Any, bool]]:
        """Возвращает кастомные проверки для дочерних классов"""
        return {
            "lead_id": (self.lead_client, LeadDB, False),
            "company_id": (self.company_client, CompanyDB, False),
            "contact_id": (self.contact_client, ContactDB, False),
            "assigned_by_id": (self.user_client, UserDB, True),
            "created_by_id": (self.user_client, UserDB, True),
            "modify_by_id": (self.user_client, UserDB, False),
            "moved_by_id": (self.user_client, UserDB, False),
            "last_activity_by": (self.user_client, UserDB, False),
        }

    async def fetch_deals(
        self, start_date: datetime, end_date: datetime
    ) -> Any:
        """Асинхронно получает сделки со связанными данными"""
        # Рассчитываем конец периода как начало следующего дня
        end_date_plus_one = end_date + timedelta(days=1)
        try:
            result = await self.session.execute(
                select(DealDB)
                .where(
                    DealDB.date_create >= start_date,
                    DealDB.date_create <= end_date_plus_one,
                    DealDB.is_deleted_in_bitrix.is_(False),
                    DealDB.category_id == 0,
                )
                .options(
                    # Загрузка отношений для Deal
                    selectinload(DealDB.assigned_user),
                    selectinload(DealDB.assigned_user).selectinload(
                        UserDB.department
                    ),
                    selectinload(DealDB.created_user),
                    selectinload(DealDB.stage),
                    selectinload(DealDB.timeline_comments),
                    selectinload(DealDB.timeline_comments).selectinload(
                        TimelineComment.author
                    ),
                    selectinload(DealDB.company),
                    # Загрузка отношений для Lead
                    selectinload(DealDB.lead).selectinload(
                        LeadDB.assigned_user
                    ),
                    selectinload(DealDB.lead).selectinload(
                        LeadDB.created_user
                    ),
                )
            )
            return result.scalars().all()
        except Exception as e:
            # Логируем ошибку и пробрасываем дальше
            logger.error(f"Error fetching deals: {str(e)}")
            raise

    async def get_add_info_by_deal_id(self, deal_id: int) -> AddInfoDB | None:
        """Получить дополнительную информацию по ID сделки"""
        try:
            query = (
                select(AddInfoDB)
                .where(AddInfoDB.deal_id == deal_id)
                .options(selectinload(AddInfoDB.deal))
            )
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при получении дополнительной информации для сделки "
                f"{deal_id}: {e}"
            )
            raise RuntimeError(
                "Не удалось получить дополнительную информацию для сделки "
                f"{deal_id}"
            ) from e

    async def get_all_add_info(
        self, skip: int = 0, limit: int = 100
    ) -> Sequence[AddInfoDB]:
        """Получить всю дополнительную информацию с пагинацией"""
        try:
            query = (
                select(AddInfoDB)
                .offset(skip)
                .limit(limit)
                .options(selectinload(AddInfoDB.deal))
            )
            result = await self.session.execute(query)
            return result.scalars().all()  # type: ignore[no-any-return]
        except SQLAlchemyError as e:
            logger.error(
                f"Ошибка при получении списка дополнительной информации: {e}"
            )
            raise RuntimeError(
                "Не удалось получить список дополнительной информации"
            ) from e

    async def create_add_info(self, add_info_data: AddInfoCreate) -> AddInfoDB:
        """Создать новую дополнительную информацию"""
        try:
            # Проверяем, существует ли уже информация для этой сделки
            existing_info = await self.get_add_info_by_deal_id(
                add_info_data.deal_id
            )
            if existing_info:
                raise ConflictException(
                    entity="AdditionalInfo",
                    external_id=add_info_data.deal_id,
                )

            additional_info = AddInfoDB(
                deal_id=add_info_data.deal_id, comment=add_info_data.comment
            )

            self.session.add(additional_info)
            await self.session.commit()
            await self.session.refresh(additional_info)

            # Загружаем связанные данные
            await self.session.refresh(additional_info, ["deal"])

            return additional_info
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(
                "Ошибка целостности при создании дополнительной информации "
                f"для сделки {add_info_data.deal_id}: {e}"
            )
            raise ValueError(
                "Нарушение целостности данных при создании дополнительной "
                "информации"
            ) from e
        except (ValueError, RuntimeError, ConflictException) as e:
            await self.session.rollback()
            logger.error(
                "Ошибка при создании дополнительной информации для сделки "
                f"{add_info_data.deal_id}: {e}"
            )
            raise
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(
                "Ошибка базы данных при создании дополнительной информации "
                f"для сделки {add_info_data.deal_id}: {e}"
            )
            raise RuntimeError(
                "Не удалось создать дополнительную информацию из-за ошибки "
                "базы данных"
            ) from e

    async def set_add_info_by_deal_id(
        self, deal_id: int, comment: str
    ) -> bool:
        """Установить дополнительную информацию"""
        try:
            await self.create_add_info(
                AddInfoCreate(deal_id=deal_id, comment=comment)
            )
            return True
        except ConflictException:
            await self.update_add_info(deal_id, AddInfoUpdate(comment=comment))
            return True
        except Exception:
            return False

    async def update_add_info(
        self, deal_id: int, add_info_data: AddInfoUpdate
    ) -> AddInfoDB | None:
        """Обновить дополнительную информацию для сделки"""
        try:
            # Получаем текущие данные
            additional_info = await self.get_add_info_by_deal_id(deal_id)
            if not additional_info:
                return None

            # Обновляем только переданные поля
            update_data = add_info_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(additional_info, field, value)

            await self.session.commit()
            await self.session.refresh(additional_info)

            # Загружаем связанные данные
            await self.session.refresh(additional_info, ["deal"])

            return additional_info
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(
                "Ошибка целостности при обновлении дополнительной информации "
                f"для сделки {deal_id}: {e}"
            )
            raise ValueError(
                "Нарушение целостности данных при обновлении дополнительной "
                "информации"
            ) from e
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(
                "Ошибка базы данных при обновлении дополнительной информации "
                f"для сделки {deal_id}: {e}"
            )
            raise RuntimeError(
                "Не удалось обновить дополнительную информацию из-за ошибки "
                "базы данных"
            ) from e

    async def delete_add_info(self, deal_id: int) -> bool:
        """Удалить дополнительную информацию для сделки"""
        try:
            additional_info = await self.get_add_info_by_deal_id(deal_id)
            if not additional_info:
                return False

            await self.session.delete(additional_info)
            await self.session.commit()
            return True
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(
                "Ошибка базы данных при удалении дополнительной информации "
                f"для сделки {deal_id}: {e}"
            )
            raise RuntimeError(
                "Не удалось удалить дополнительную информацию из-за ошибки "
                "базы данных"
            ) from e

    async def upsert_add_info(
        self, add_info_data: AddInfoCreate
    ) -> AddInfoDB | None:
        """Создать или обновить дополнительную информацию"""
        try:
            # Проверяем, существует ли уже информация для этой сделки
            existing_info = await self.get_add_info_by_deal_id(
                add_info_data.deal_id
            )

            if existing_info:
                # Обновляем существующую запись
                return await self.update_add_info(
                    add_info_data.deal_id,
                    AddInfoUpdate(comment=add_info_data.comment),
                )
            else:
                # Создаем новую запись
                return await self.create_add_info(add_info_data)
        except (ValueError, RuntimeError) as e:
            logger.error(
                "Ошибка при создании/обновлении дополнительной информации для "
                f"сделки {add_info_data.deal_id}: {e}"
            )
            raise

    async def get_external_id_by_sort_order_stage(
        self, sort_order: int
    ) -> str | None:
        """Получить external_id стадии сделки по порядковому номеру"""
        try:
            stmt = select(DealStage.external_id).where(
                DealStage.sort_order == sort_order
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()  # type: ignore[no-any-return]
        except Exception as e:
            # Логирование ошибки
            logger.error(
                "Ошибка при получении external_id по sort_order "
                f"{sort_order}: {e}"
            )
            return None

    async def get_sort_order_by_external_id_stage(
        self, external_id: str
    ) -> int | None:
        """Получить порядковый номер стадии сделки по external_id"""
        try:
            stmt = select(DealStage.sort_order).where(
                DealStage.external_id == external_id
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()  # type: ignore[no-any-return]
        except Exception as e:
            # Логирование ошибки
            logger.error(
                "Ошибка при получении sort_order по external_id "
                f"{external_id}: {e}"
            )
            return None

    async def get_deals_for_checking_processing_status(
        self, current_time: datetime
    ) -> list[DealDB]:
        """Получает сделки для проверки статуса обработки"""
        try:
            first_stages = await self.get_first_four_stages()
            if not first_stages:
                logger.warning("No first stages found")
                return []

            # Получаем сделки для обновления
            stmt = select(DealDB).where(
                and_(
                    DealDB.stage_id.in_(first_stages),
                    DealDB.is_deleted_in_bitrix.is_(False),
                    DealDB.moved_date.is_not(None),
                    DealDB.moved_date <= current_time,
                    DealDB.category_id == 0,
                )
            )

            result = await self.session.execute(stmt)
            return result.scalars().all()  # type: ignore[no-any-return]
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при получении сделок: {e}")
            return []

    async def get_first_four_stages(self) -> list[str]:
        """Получает ID первых четырех стадий сделок"""
        try:
            stage_ids: list[str] = []
            for i in range(1, 5):
                external_id = await self.get_external_id_by_sort_order_stage(i)
                if external_id:
                    stage_ids.append(external_id)

            logger.debug(f"Found first four stages: {stage_ids}")
            return stage_ids

        except Exception as e:
            logger.error(f"Error getting first four stages: {e}")
            return []

    async def get_deals_batch(
        self,
        batch_size: int = 1000,
        last_id: int = 0,
        filters: dict[str, Any] | None = None,
    ) -> Sequence[DealDB]:
        """Оптимизированная выборка только необходимых полей"""

        # Базовый запрос с минимальной загрузкой
        stmt = (
            select(DealDB)
            .where(DealDB.external_id > last_id)
            .order_by(DealDB.external_id)
            .limit(batch_size)
            .options(
                load_only(
                    DealDB.external_id,
                    DealDB.category_id,
                    # DealDB.opportunity,
                    # DealDB.stage_id,
                    # DealDB.closedate
                )
            )
        )

        if filters:
            if filters.get("stage_id"):
                stmt = stmt.where(DealDB.stage_id == filters["stage_id"])
            if filters.get("closed") is not None:
                stmt = stmt.where(DealDB.closed == filters["closed"])
            if filters.get("date_from"):
                stmt = stmt.where(DealDB.closedate >= filters["date_from"])

        result = await self.session.execute(stmt)
        return result.scalars().all()  # type: ignore[no-any-return]

    async def get_overdue_deals(self) -> list[DealDB]:
        """
        Получает сделки с неопределённым статусом обработки
        (только на первых 4 стадиях).
        """
        try:
            first_stages = await self.get_first_four_stages()
            if not first_stages:
                logger.warning("No first stages found")
                return []

            # Получаем сделки для обновления
            stmt = (
                select(DealDB)
                .options(
                    joinedload(DealDB.assigned_user).joinedload(
                        UserDB.manager
                    ),
                    joinedload(DealDB.stage),
                )
                .where(
                    and_(
                        DealDB.stage_id.in_(first_stages),
                        DealDB.is_deleted_in_bitrix.is_(False),
                        DealDB.status_deal == (DealStatusEnum.NOT_DEFINE),
                        DealDB.category_id == 0,
                    )
                )
                .order_by(
                    DealDB.assigned_by_id.asc(),
                    DealDB.stage_id.asc(),
                    DealDB.moved_date.asc(),
                    DealDB.opportunity.desc(),
                )
            )
            result = await self.session.execute(stmt)
            return result.scalars().all()  # type: ignore[no-any-return]
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при получении сделок: {e}")
            return []

    async def sync_timeline_comments(self, deal_external_id: int) -> None:
        """Синхронизирует комментарии для сделки"""
        if not self.timeline_comment_client:
            logger.warning(
                "TimelineCommentClient not available for comment sync"
            )
            return

        try:
            # Получаем актуальные комментарии из Bitrix
            timeline_b24_client = self.timeline_comment_client.bitrix_client
            bitrix_comments = await timeline_b24_client.get_comments_by_entity(
                entity_type=EntityType.DEAL,
                entity_id=deal_external_id,
            )

            # Получаем существующие комментарии из БД
            timeline_repo = self.timeline_comment_client.repo
            exist_comments = await timeline_repo.get_existing_comments_entity(
                entity_type=EntityType.DEAL,
                entity_id=deal_external_id,
            )
            existing_comment_ids = {
                comment.external_id for comment in exist_comments
            }

            # Обновляем или создаем комментарии из Bitrix
            for comment_data in bitrix_comments.result:
                try:
                    comment_data_create = comment_data.to_create(
                        deal_external_id, EntityType.DEAL
                    )
                    await timeline_repo.create_or_update(comment_data_create)
                    if comment_data_create.external_id:
                        existing_comment_ids.discard(
                            comment_data_create.external_id
                        )
                except Exception:
                    ...

            # Помечаем как удаленные комментарии, которых нет в Bitrix
            await self._mark_deleted_comments(existing_comment_ids)

            logger.info(
                f"Synced timeline comments for deal {deal_external_id}"
            )

        except Exception as e:
            logger.error(
                "Failed to sync timeline comments for deal "
                f"{deal_external_id}: {str(e)}"
            )
            # Не прерываем основной поток из-за ошибки синхронизации

    async def _mark_deleted_comments(
        self, deleted_comment_ids: set[int]
    ) -> None:
        """Помечает комментарии как удаленные в Bitrix"""
        if not self.timeline_comment_client:
            logger.warning(
                "TimelineCommentClient not available for comment sync"
            )
            return

        timeline_repo_client = self.timeline_comment_client.repo
        for comment_id in deleted_comment_ids:
            try:
                await timeline_repo_client.set_deleted_in_bitrix(comment_id)
                logger.debug(
                    f"Marked timeline comment {comment_id} as deleted"
                )
            except Exception as e:
                logger.error(
                    f"Failed to mark comment {comment_id} as deleted: {str(e)}"
                )
