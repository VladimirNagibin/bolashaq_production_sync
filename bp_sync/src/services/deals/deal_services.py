# import asyncio
# import time
from datetime import date  # , datetime, timezone
from typing import Any, Self, cast

from core.logger import logger
from core.settings import settings
from models.deal_models import Deal as DealDB
from schemas.base_schemas import CommonFieldMixin
from schemas.company_schemas import CompanyCreate
from schemas.contact_schemas import ContactCreate
from schemas.deal_schemas import DealCreate, DealUpdate
from schemas.enums import (  # EntityTypeAbbr,
    DealStagesEnum,
    DealStatusEnum,
    StageSemanticEnum,
)
from schemas.lead_schemas import LeadCreate
from services.companies.company_services import CompanyClient
from services.contacts.contact_services import ContactClient
from services.leads.lead_services import LeadClient
from services.timeline_comments.timeline_comment_services import (
    TimelineCommentClient,
)
from services.users.user_services import UserClient

from ..base_services.base_service import BaseEntityClient
from ..decorators import log_execution_time
from ..exceptions import (
    DealNotFoundError,
    DealNotInMainFunnelError,
    DealProcessingError,
    DealSyncError,
    InvalidDealStateError,
)

# from ..products.product_bitrix_services import ProductBitrixClient
from .deal_bitrix_services import DealBitrixClient
from .deal_data_provider import DealDataProvider

# from services.bitrix_services.webhook_service import WebhookService
# from services.products.product_bitrix_services import ProductUpdateResult
from .deal_lock_service import LockService

# from .deal_extend_processing import DealProcessingClient
# from .deal_lock_service import LockService
# from .deal_processing_status_service import DealProcessingStatusService
# from .deal_report_helpers import (
#    create_dataframe,
#     create_excel_file,
#    process_deal_row_report,
# )
from .deal_repository import DealRepository

# from .deal_source_classifier import WEBSITE_CREATOR, identify_source
# from .deal_source_handler import DealSourceHandler
# from .deal_stage_handler import DealStageHandler
from .deal_update_tracker import DealUpdateTracker

# from fastapi import HTTPException, Request, status
# from fastapi.responses import JSONResponse


# from .deal_with_invoice_handler import DealWithInvioceHandler
# from .enums import (
#    EXCLUDE_FIELDS_FOR_COMPARE,
#    CreationSourceEnum,
#    DealSourceEnum,
#    DealTypeEnum,
#    NotificationScopeEnum,
# )
# from .site_order_handler import SiteOrderHandler

# STAGES_LOSE = ("LOSE", "APOLOGY")

SOURCE_SITE_ORDER = "21"
STAGE_INVOICE_FAIL = "DT31_1:D"
CONDITION_MOVING_STAGE = {
    1: (
        "Для перехода на стадию ВЫЯВЛЕНИЕ ПОТРЕБНОСТИ должны быть заполнены "
        "контактные данные (компания или контакт)"
    ),
    2: (
        "Для перехода на стадию ЗАИНТЕРЕСОВАН должны быть заполнены "
        "товары, основная деятельность и город"
    ),
    3: (
        "Для перехода на стадию СОГЛАСОВАНИЕ УСЛОВИЙ должны быть заполнены "
        "компания покупателя и фирма отгрузки"
    ),
    4: (
        "Для перехода на стадию ВЫСТАВЛЕНИЕ СЧЁТА должно быть наличие "
        "договора с компанией по фирме отгрузки. "
        "Исключения: Отгрузка по Системам - договор не требуется. "
        "Предоплата по ИП Воробьёву - используется счет-оферта без заключения "
        "договора."
    ),
}
MAX_AGE = 300


class DealClient(BaseEntityClient[DealDB, DealRepository, DealBitrixClient]):
    """Клиент для работы со сделками"""

    def __init__(
        self,
        deal_bitrix_client: DealBitrixClient,
        deal_repo: DealRepository,
        lock_service: LockService,
        user_client: UserClient | None = None,
        contact_client: ContactClient | None = None,
        company_client: CompanyClient | None = None,
        lead_client: LeadClient | None = None,
        timeline_comment_client: TimelineCommentClient | None = None,
        # product_bitrix_client: ProductBitrixClient,
    ):
        super().__init__()
        self._bitrix_client = deal_bitrix_client
        self._repo = deal_repo
        # self.product_bitrix_client = product_bitrix_client
        self.lock_service = lock_service

        # self.stage_handler = DealStageHandler(self)
        self.data_provider = DealDataProvider(self)
        self.update_tracker = DealUpdateTracker()
        # self.site_order_handler = SiteOrderHandler(self)
        # self.deal_with_invoice_handler = DealWithInvioceHandler(self)
        # self.deal_source_handler = DealSourceHandler(self)
        # self.deal_ext_service = DealProcessingClient()
        # self.deal_processing_status_service = DealProcessingStatusService(
        #     self
        # )

        self.retry_config: dict[str, Any] = self._build_retry_config()

        self._init_dependencies(
            user_client,
            company_client,
            contact_client,
            lead_client,
            timeline_comment_client,
        )

    def _build_retry_config(self) -> dict[str, Any]:
        """Создает конфигурацию для механизма повторных попыток."""
        return {
            "max_retries": getattr(settings, "lock_max_retries", 3),
            "base_delay": getattr(settings, "lock_base_delay", 1.0),
            "max_delay": getattr(settings, "lock_max_delay", 30.0),
            "jitter": getattr(settings, "lock_jitter", True),
            "lock_timeout": getattr(settings, "default_lock_timeout", 300),
        }

    def _init_dependencies(
        self: Self,
        user_client: UserClient | None,
        company_client: CompanyClient | None,
        contact_client: ContactClient | None,
        lead_client: LeadClient | None,
        timeline_comment_client: TimelineCommentClient | None,
    ) -> None:
        """Инициализация зависимых сервисов"""
        if user_client is not None:
            self._repo.set_user_client(user_client)
        if company_client is not None:
            self._repo.set_company_client(company_client)
        if contact_client is not None:
            self._repo.set_contact_client(contact_client)
        if lead_client is not None:
            self._repo.set_lead_client(lead_client)
        if timeline_comment_client is not None:
            self._repo.set_timeline_comment_client(timeline_comment_client)

    @property
    def entity_name(self) -> str:
        return "deal"

    @property
    def bitrix_client(self) -> DealBitrixClient:
        return self._bitrix_client

    @property
    def repo(self) -> DealRepository:
        return self._repo

    @property
    def webhook_config(self) -> dict[str, Any]:
        return {
            "allowed_events": set(
                settings.web_hook_config.get("allowed_events", [])
            ),
            "expected_tokens": settings.web_hook_config.get(
                "expected_tokens", {}
            ),
            "max_age": MAX_AGE,
        }

    async def _get_related_entity(
        self, entity_type: str, entity_id: int
    ) -> CommonFieldMixin | None:
        """
        Универсальный метод для получения связанных сущностей
        (лид, компания, контакт).
        """
        logger.debug(f"Getting {entity_type} with ID: {entity_id}")
        try:
            client_service = getattr(self.repo, f"{entity_type}_client", None)
            if not client_service:
                logger.warning(f"Client for {entity_type} is not configured.")
                return None
            return await client_service.bitrix_client.get(entity_id)
        except Exception as e:
            logger.error(f"Failed to get {entity_type} {entity_id}: {str(e)}")
            return None

    async def get_lead(self, lead_id: int) -> LeadCreate | None:
        """Получение лида по ID"""
        lead = await self._get_related_entity("lead", lead_id)
        assert lead is None or isinstance(lead, LeadCreate)
        return lead

    async def get_company(self, company_id: int) -> CompanyCreate | None:
        """Получение компании по ID"""
        company = await self._get_related_entity("company", company_id)
        assert company is None or isinstance(company, CompanyCreate)
        return company

    async def get_contact(self, contact_id: int) -> ContactCreate | None:
        """Получение контакта по ID"""
        contact = await self._get_related_entity("contact", contact_id)
        assert contact is None or isinstance(contact, ContactCreate)
        return contact

    async def get_comments(self, deal_id: int) -> list[str]:
        """Получает комментарии сделки"""
        logger.debug(f"Getting comments for deal ID: {deal_id}")
        try:
            timeline_service = self.repo.timeline_comment_client
            if not timeline_service:
                return []
            timeline_client = timeline_service.bitrix_client
            comments_result = await timeline_client.get_comments_by_entity(
                "deal", deal_id
            )
            comments: list[str] = [
                comm.comment_entity
                for comm in comments_result.result
                if comm.comment_entity
            ]
            return comments
        except Exception as e:
            logger.error(f"Failed to get comments deal {deal_id}: {str(e)}")
            return []

    @log_execution_time("deal_processing")
    async def handle_deal(self, external_id: int) -> bool | None:
        """
        Основной метод для обработки сделки.
        Выполняет получение данных, применение бизнес-логики и синхронизацию.
        """
        logger.info(f"Starting processing for deal {external_id}")
        try:
            self.update_tracker.reset()
            self.data_provider.clear_cache()
            self.update_tracker.init_deal(external_id)

            deal_b24, deal_db, changes = await self.get_changes_b24_db(
                external_id
            )
            logger.debug(
                "Detected changes",
                extra={"deal_id": external_id, "changes": changes},
            )
            if not deal_b24:
                raise DealNotFoundError(
                    "Not found in Bitrix24", deal_id=external_id
                )

            if deal_b24.category_id != 0:
                raise DealNotInMainFunnelError(
                    (
                        "Not in the main funnel "
                        f"(category_id={deal_b24.category_id})"
                    ),
                    external_id,
                )

            await self._handle_deal(deal_b24, deal_db, changes)

            if self.update_tracker.has_changes() or changes or not deal_db:
                await self._synchronize_deal_data(deal_b24, deal_db, changes)
                logger.info(
                    f"Deal {external_id} successfully processed and "
                    "synchronized."
                )
            else:
                logger.info(
                    f"Deal {external_id} processed successfully "
                    "with no changes."
                )

            return True
        except DealNotInMainFunnelError:
            # Это не ошибка, а штатная ситуация. Просто логируем и выходим.
            logger.info(f"Skipping deal {external_id}: not in main funnel.")
            return True
        except DealProcessingError as e:
            # Логируем наши известные ошибки обработки
            logger.error(f"Failed to process deal {external_id}: {str(e)}")
            raise
        except Exception as e:
            # Логируем непредвиденные ошибки с полным трейсбеком
            logger.exception(
                "An unexpected error occurred while processing "
                f"deal {external_id}"
            )
            # Пробрасываем дальше как общую ошибку обработки
            raise DealProcessingError(
                "Unexpected error for deal", external_id
            ) from e
        finally:
            self.data_provider.clear_cache()
            self.update_tracker.reset()
            logger.info(f"Finished processing deal {external_id}")

    async def _handle_deal(
        self,
        deal_b24: DealCreate,
        deal_db: DealCreate | None,
        changes: dict[str, dict[str, Any]] | None,
    ) -> None:
        """
        Диспетчер обработки, применяющий различную логику в зависимости
        от состояния сделки
        """
        logger.debug(f"Handling deal {deal_b24.external_id}")

        if deal_b24.stage_semantic_id == StageSemanticEnum.FAIL:
            await self._handle_fail_deal(deal_b24, deal_db)
            return

        if not deal_db:
            await self._handle_new_deal(deal_b24)
            return

        # Если в Б24 поменяли статус - откатываем из БД
        await self._check_deal_status(deal_b24, deal_db)

        if deal_b24.status_deal == DealStatusEnum.NEW:
            await self._handle_new_status_deal(deal_b24, deal_db, changes)
            return

    async def _handle_fail_deal(
        self,
        deal_b24: DealCreate,
        deal_db: DealCreate | None,
    ) -> None:
        """Обработка провальной сделки"""
        logger.info(f"Handle fail deal: {deal_b24.external_id}")
        today = date.today()

        if (deal_b24.status_deal != DealStatusEnum.DEAL_LOSE) or (
            deal_db and deal_db.status_deal != DealStatusEnum.DEAL_LOSE
        ):
            self.update_tracker.update_field(
                "status_deal", DealStatusEnum.DEAL_LOSE, deal_b24
            )
            deal_moved_date = (
                deal_db.moved_date.date()
                if deal_db and deal_db.moved_date
                else None
            )
            if deal_moved_date != today:
                self.update_tracker.update_field("moved_date", today, deal_b24)

    async def _handle_new_deal(
        self,
        deal_b24: DealCreate,
    ) -> None:
        """Обработка новой сделки"""
        logger.info(f"Handling new deal: {deal_b24.external_id}")

        if deal_b24.status_deal != DealStatusEnum.NEW:
            self.update_tracker.update_field(
                "status_deal", DealStatusEnum.NEW, deal_b24
            )
        initial_stage_id = await self.repo.get_external_id_by_sort_order_stage(
            DealStagesEnum.INITIAL_SORT_ORDER,
        )
        if deal_b24.stage_id != initial_stage_id:
            self.update_tracker.update_field(
                "stage_id", initial_stage_id, deal_b24
            )
        self.update_tracker.update_field("moved_date", date.today(), deal_b24)
        # TODO: Реализовать логику проверки источника
        # TODO: Реализовать логику проверки ответственного

    async def _check_deal_status(
        self,
        deal_b24: DealCreate,
        deal_db: DealCreate | None,
    ) -> None:
        """
        Проверяет, не был ли изменен статус сделки в Bitrix24.
        Если был, откатывает его на значение из БД.
        """
        logger.debug(f"Check status for deal: {deal_b24.external_id}")

        if not deal_db:
            raise DealNotFoundError(
                "Deal not found in database",
                cast(int | None, deal_b24.external_id),
            )

        if deal_b24.status_deal != deal_db.status_deal:
            logger.warning(
                f"Status mismatch for deal {deal_b24.external_id}. "
                f"B24: {deal_b24.status_deal}, DB: {deal_db.status_deal}. "
                f"Rolling back to DB status."
            )
            deal_data: dict[str, Any] = {
                "external_id": deal_b24.external_id,
                "status_deal": deal_db.status_deal,
            }
            deal_update = DealUpdate(**deal_data)

            await self.bitrix_client.update(deal_update)
            raise InvalidDealStateError(
                f"Deal {deal_b24.external_id} status was changed externally. "
                f"Rolled back to '{deal_db.status_deal.value}'."
            )

    async def _handle_new_status_deal(
        self,
        deal_b24: DealCreate,
        deal_db: DealCreate | None,
        changes: dict[str, dict[str, Any]] | None,
    ) -> None:
        """Обработка сделки, которая находится в статусе 'Новая'."""
        logger.info(f"Handling deal in 'NEW' status: {deal_b24.external_id}")

        stage_number = await self.repo.get_sort_order_by_external_id_stage(
            deal_b24.stage_id
        )

        if stage_number and stage_number > DealStagesEnum.INITIAL_SORT_ORDER:
            logger.debug(
                "Deal stage advanced beyond initial",
                extra={
                    "deal_id": deal_b24.external_id,
                    "stage_number": stage_number,
                },
            )
            if stage_number > DealStagesEnum.SECOND_SORT_ORDER:
                stage_need = self.repo.get_external_id_by_sort_order_stage(
                    DealStagesEnum.SECOND_SORT_ORDER
                )
                self.update_tracker.update_field(
                    "stage_id", stage_need, deal_b24
                )
                logger.debug(
                    "Rolled back deal stage to 2",
                    extra={"deal_id": deal_b24.external_id},
                )
            self.update_tracker.update_field(
                "status_deal", DealStatusEnum.ACCEPTED, deal_b24
            )
            logger.debug(
                "Updated deal status to ACCEPTED",
                extra={"deal_id": deal_b24.external_id},
            )

    # async def _check_update_products(
    #     self, deal_b24: DealCreate, external_id: int
    # ) -> None:
    #     product_client = self.product_bitrix_client
    #     products_update: ProductUpdateResult = (
    #         await product_client.check_update_products_entity(
    #             external_id, EntityTypeAbbr.DEAL
    #         )
    #     )
    #     # Если товары заменялись, тогда сообщение ответственному
    #     # (кроме заказов с сайта).
    #     if products_update.has_changes:
    #         removed_products = products_update.removed_products
    #         replaced_products = products_update.replaced_products
    #         link = self.bitrix_client.get_formatted_link(
    #             deal_b24.external_id, deal_b24.title
    #         )
    #         if removed_products:
    #             removed_info = (
    #                 f"Сделка {link}: удалены товары "
    #                 f"{len(removed_products)}шт."
    #                 f"\n{[p.product_name for p in removed_products]}"
    #             )
    #             await self.bitrix_client.send_message_b24(
    #                 deal_b24.assigned_by_id, removed_info
    #             )
    #         if replaced_products:
    #             products_replaced = [
    #                 f"{change['old_product'].product_name} -> "
    #                 f"{change['new_product'].product_name}"
    #                 for change in replaced_products
    #             ]
    #             products_replaced_ = "\n".join(products_replaced)
    #             replaced_info = (
    #                 f"Сделка {link}: заменены товары "
    #                 f"{len(replaced_products)}"
    #                 f"шт.\n{products_replaced_}"
    #             )
    #             await self.bitrix_client.send_message_b24(
    #                 deal_b24.assigned_by_id, replaced_info
    #             )

    #     products = products_update.products
    #     if products:
    #         self.data_provider.set_cached_products(products)
    #         logger.debug(
    #             f"Cached {products.count_products} products for deal "
    #             f"{external_id}"
    #         )

    # async def _send_message_unavailable_stage(
    #     self, current_stage: int, available_stage: int, deal_b24: DealCreate
    # ) -> None:
    #     messages: list[str] = []
    #     for i in range(available_stage, current_stage):
    #         messages.append(CONDITION_MOVING_STAGE[i])
    #     link = (
    #         f"[url={self.bitrix_client.get_link(deal_b24.external_id)}]"
    #         f"{deal_b24.title}[/url]"
    #     )
    #     await self.bitrix_client.send_message_b24(
    #         deal_b24.assigned_by_id,
    #         f"Сделка {link}: {'; '.join(messages)}",
    #         # deal_b24.assigned_by_id, "; ".join(messages)
    #     )

    def get_external_id(self, deal_b24: DealCreate) -> int | None:
        if not deal_b24.external_id:
            return None
        try:
            return int(deal_b24.external_id)
        except (ValueError, TypeError):
            logger.error(f"Invalid external_id format: {deal_b24.external_id}")
            return None

    async def _synchronize_deal_data(
        self,
        deal_b24: DealCreate,
        deal_db: DealCreate | None,
        changes: dict[str, dict[str, Any]] | None,
    ) -> None:
        """Синхронизирует данные сделки между Bitrix24 и базой данных"""
        logger.info(f"Synchronizing deal data for {deal_b24.external_id}")
        deal_update = self.update_tracker.get_deal_update()
        try:
            # 1. Синхронизация с базой данных
            if deal_db:
                # Добавляем изменения из Б24, которых нет в update_tracker
                if changes:
                    for key, change in changes.items():
                        if getattr(deal_update, key) is None:
                            setattr(deal_update, key, change["internal"])
                await self.repo.update_entity(deal_update)
                logger.debug(
                    f"Updated deal {deal_b24.external_id} in database."
                )
            else:
                await self.repo.create_entity(deal_b24)
                logger.debug(
                    f"Created new deal {deal_b24.external_id} in database."
                )

            # 2. Синхронизация с Bitrix24
            # Обновляем только те поля, которые были изменены обработчиком
            if self.update_tracker.has_changes():
                await self.bitrix_client.update(deal_update)
                logger.debug(
                    f"Updated deal {deal_b24.external_id} in Bitrix24."
                )

        except Exception as e:
            logger.exception(
                f"Failed to synchronize deal {deal_b24.external_id}"
            )
            raise DealSyncError(
                f"Synchronization failed for deal {deal_b24.external_id}"
            ) from e

    # async def check_source(
    #     self,
    #     deal_b24: DealCreate,
    #     deal_db: DealCreate | None,
    # ) -> bool:
    #     """Проверка и определение источника сделки"""
    #     try:
    #         needs_update = False
    #         creation_source_id = deal_b24.creation_source_id
    #         source_id = deal_b24.source_id
    #         type_id = deal_b24.type_id
    #         context: dict[str, Any] = {}
    #         if deal_db and deal_db.is_setting_source:
    #             creation_corr = CreationSourceEnum.from_value(
    #                 deal_db.creation_source_id
    #             )
    #             type_corr = DealTypeEnum.from_value(deal_db.type_id)
    #             source_corr = DealSourceEnum.from_value(deal_db.source_id)
    #         else:
    #             result = await identify_source(
    #                 deal_b24,
    #                 self.get_lead,
    #                 self.get_company,
    #                 self.get_comments,
    #                 context=context,
    #             )
    #             if "company" in context:
    #                 self.data_provider.set_cached_company(context["company"])
    #             creation_corr, type_corr, source_corr = result
    #             logger.info(
    #                 f"{deal_b24.title} - comparison of source changes:"
    #                 f"{CreationSourceEnum.get_display_name(creation_corr)}"
    #                 f":{creation_source_id}, "
    #                 f"{DealTypeEnum.get_display_name(type_corr)}:{type_id}, "
    #                 f"{DealSourceEnum.get_display_name(source_corr)}:"
    #                 f"{source_id}"
    #             )

    #         needs_update |= await self._update_field_if_needed(
    #             deal_b24,
    #             "creation_source_id",
    #             creation_source_id,
    #             creation_corr.value,
    #         )

    #         needs_update |= await self._update_field_if_needed(
    #             deal_b24,
    #             "source_id",
    #             source_id,
    #             source_corr.value,
    #         )

    #         needs_update |= await self._update_field_if_needed(
    #             deal_b24,
    #             "type_id",
    #             type_id,
    #             type_corr.value,
    #         )
    #         needs_update |= await self._handle_assignment(
    #             deal_b24, creation_corr, type_corr, deal_db
    #         )
    #         logger.debug(
    #             f"Source check for deal {deal_b24.external_id} completed, "
    #             f"updates needed: {needs_update}"
    #         )
    #         return needs_update
    #     except Exception as e:
    #         logger.error(
    #             f"Error identifying source for deal {deal_b24.external_id}: "
    #             f"{str(e)}"
    #         )
    #         raise

    # async def _update_field_if_needed(
    #     self,
    #     deal_b24: DealCreate,
    #     field_name: str,
    #     current_value: Any,
    #     correct_value: Any,
    # ) -> bool:
    #     """
    #     Обновляет поле сделки, если текущее значение отличается
    #     от корректного
    #     """
    #     if current_value != correct_value:
    #         self.update_tracker.update_field(
    #             field_name, correct_value, deal_b24
    #         )
    #         logger.info(
    #             f"Updated {field_name} from {current_value} to "
    #             f"{correct_value}"
    #         )
    #         return True
    #     return False

    # async def _handle_assignment(
    #     self,
    #     deal_b24: DealCreate,
    #     # creation_source: CreationSourceEnum,
    #     # type_corr: DealTypeEnum,
    #     deal_db: DealCreate | None,
    # ) -> bool:
    #     """
    #     Обрабатывает назначение ответственного в зависимости от источника
    #     сделки
    #     """
    #     needs_update = False

    #     if (
    #         creation_source == CreationSourceEnum.AUTO
    #         and type_corr == DealTypeEnum.ONLINE_SALES
    #         and not deal_db
    #     ):
    #         if deal_b24.assigned_by_id != WEBSITE_CREATOR:
    #             self.update_tracker.update_field(
    #                 "assigned_by_id", WEBSITE_CREATOR, deal_b24
    #             )
    #             logger.info(
    #                 "Assigned to website creator for auto-created deal"
    #             )
    #     else:
    #         if not await self._check_active_manager(deal_b24.assigned_by_id):
    #             self.update_tracker.update_field(
    #                 "assigned_by_id", WEBSITE_CREATOR, deal_b24
    #             )
    #             logger.info(
    #                 "Reassigned to website creator due to inactive manager"
    #             )

    #     return needs_update

    # async def _check_active_manager(self, manager_id: int) -> bool:
    #     """Проверка активных менеджеров"""
    #     logger.debug(f"Checking if manager {manager_id} is active")
    #     try:
    #         user_service = await self.repo.get_user_client()
    #         return await user_service.repo.is_activity_manager(manager_id)
    #     except Exception as e:
    #         logger.error(f"Failed to check manager {manager_id}: {str(e)}")
    #         return False

    # async def update_comments(
    #     self, comment: str, deal_b24: DealCreate
    # ) -> bool:
    #     """Обновляет комментарии сделки"""
    #     logger.debug(f"Updating comments for deal {deal_b24.external_id}")
    #     try:
    #         comments_deal = deal_b24.comments
    #         comments_new = None
    #         if not comments_deal:
    #             comments_new = comment
    #         else:
    #             if comment in comments_deal:
    #                 return False
    #             comments_new = (
    #                 f"<div>{comments_deal}</div><div>{comment}<br></div>"
    #             )
    #             self.update_tracker.update_field(
    #                 "comments", comments_new, deal_b24
    #             )
    #         return True

    #     except Exception as e:
    #         logger.error(
    #             "Failed to update comments for deal "
    #             f"{deal_b24.external_id}: {str(e)}"
    #         )
    #         return False

    # async def set_deal_source(
    #     self,
    #     user_id: str,
    #     key: str,
    #     deal_id: str,
    #     creation_source: str | None,
    #     source: str | None,
    #     type_deal: str | None,
    # ) -> bool:
    #     try:
    #         return await self.deal_source_handler.set_deal_source(
    #             user_id, key, deal_id, creation_source, source, type_deal
    #         )
    #     except HTTPException:
    #         # Re-raise HTTP exceptions to be handled by FastAPI
    #         raise
    #     except Exception as e:
    #         logger.error(
    #             f"Error in process_deal_source: {str(e)}", exc_info=True
    #         )
    #         return False

    # async def deal_processing(
    #     self,
    #     request: Request,
    # ) -> JSONResponse:
    #     """
    #     Основной метод обработки вебхука сделки
    #     """
    #     # ADMIN_ID = 171
    #     try:
    #         webhook_payload = await self.webhook_service.process_webhook(
    #             request
    #         )

    #         deal_id = webhook_payload.deal_id
    #         if not deal_id:
    #             return self._success_response(
    #                 "Webhook received but no deal ID found",
    #                 webhook_payload.event,
    #             )

    #         if settings.WEB_HOOK_TEST and deal_id != settings.DEAL_ID_TEST:
    #             return self._success_response(
    #                 "Test mode: Webhook received but deal not test",
    #                 webhook_payload.event,
    #             )

    #         if webhook_payload.event == "ONCRMDEALDELETE":
    #             try:
    #                 await self.repo.set_deleted_in_bitrix(deal_id)
    #             except Exception:
    #                 ...
    #         # await self.bitrix_client.send_message_b24(
    #         #    ADMIN_ID,
    #         #    f"START NEW PROCESS DEAL ID: {deal_id}
    #         #    f{webhook_payload.ts}",
    #         # )
    #         try:
    #             async with self.lock_service.acquire_deal_lock_with_retry(
    #                 deal_id,
    #                 timeout=self.retry_config["lock_timeout"],
    #                 max_retries=self.retry_config["max_retries"],
    #                 base_delay=self.retry_config["base_delay"],
    #                 max_delay=self.retry_config["max_delay"],
    #                 jitter=self.retry_config["jitter"],
    #             ):

    #                 success = await self.handle_deal(deal_id)

    #                 if success:
    #                     try:
    #                         ext_service = self.deal_ext_service
    #                         await ext_service.send_deal_processing_request(
    #                             deal_id, int(webhook_payload.ts)
    #                         )
    #                     except HTTPException as e:
    #                         logger.error(
    #                             f"Failed to send deal processing request "
    #                             f"for deal {deal_id}-{webhook_payload.ts}: "
    #                             f"{str(e)}"
    #                         )
    #                     return self._success_response(
    #                         f"Deal {deal_id} processed successfully",
    #                         webhook_payload.event,
    #                     )
    #                 else:
    #                     raise DealProcessingError(
    #                         f"Failed to process deal {deal_id}"
    #                     )

    #         except MaxRetriesExceededError:
    #             # Все попытки исчерпаны
    #             remain_time = await self.lock_service.
    #                 get_remaining_lock_time(
    #                 deal_id
    #             )
    #             error_msg = (
    #                 f"Deal {deal_id} is still locked after "
    #                 f"{self.retry_config['max_retries']} retries"
    #             )
    #             if remain_time:
    #                 error_msg += f", lock expires in {remain_time:.1f}s"

    #             logger.warning(error_msg)
    #             return self._concurrent_processing_response(
    #                 deal_id, webhook_payload.event
    #             )

    #         except LockAcquisitionError as e:
    #             logger.warning(
    #                 f"Lock acquisition failed for deal {deal_id}: {e}"
    #             )
    #             return self._concurrent_processing_response(
    #                 deal_id, webhook_payload.event
    #             )

    #     except WebhookSecurityError as e:
    #         logger.warning(f"Webhook security error: {e}")
    #         return self._error_response(
    #             status.HTTP_401_UNAUTHORIZED,
    #             "Security validation failed",
    #             "Security error",
    #         )
    #     except WebhookValidationError as e:
    #         logger.warning(f"Webhook validation error: {e}")
    #         return self._error_response(
    #             status.HTTP_400_BAD_REQUEST,
    #             "Webhook validation failed",
    #             "Validation error",
    #         )
    #     except DealProcessingError as e:
    #         logger.error(f"Deal processing error: {e}")
    #         return self._error_response(
    #             status.HTTP_500_INTERNAL_SERVER_ERROR,
    #             "Deal processing failed",
    #             "Processing error",
    #         )
    #     except Exception as e:
    #         logger.error(f"Unexpected error in deal processing: {e}")
    #         return self._error_response(
    #             status.HTTP_500_INTERNAL_SERVER_ERROR,
    #             "Internal server error",
    #             "Unexpected error",
    #         )

    # def _concurrent_processing_response(
    #     self, deal_id: int, event: str
    # ) -> JSONResponse:
    #     """Ответ при параллельной обработке после исчерпания попыток"""
    #     return JSONResponse(
    #         status_code=status.HTTP_409_CONFLICT,
    #         content={
    #             "status": "skipped",
    #             "message": (
    #                 f"Deal {deal_id} is still being processed by another "
    #                 "worker"
    #             ),
    #             "event": event,
    #             "timestamp": time.time(),
    #             "suggestion": "Please try again later",
    #         },
    #     )

    # async def update_processing_statuses(
    #     self, relative_time: datetime | None = None
    # ) -> dict[str, int]:
    #     """Обновляет статусы обработки сделок"""
    #     try:
    #         status_service = self.deal_processing_status_service
    #         return await status_service.update_processing_statuses(
    #             relative_time
    #         )
    #     except Exception as e:
    #         logger.error(f"Error updating processing statuses: {e}")
    #         raise HTTPException(
    #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #             detail=f"Failed to update processing statuses: {str(e)}",
    #         )

    # async def update_single_processing_status(
    #     self, deal_id: int, relative_time: datetime | None = None
    # ) -> bool:
    #     """Обновляет статус обработки для одной сделки"""
    #     try:
    #         status_service = self.deal_processing_status_service
    #         return await status_service.update_single_deal_status(
    #             deal_id, relative_time
    #         )
    #     except Exception as e:
    #         logger.error(f"Error updating single processing status: {e}")
    #         raise HTTPException(
    #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #             detail=(
    #                 f"Failed to update single processing status: {str(e)}"
    #             ),
    #         )

    # async def checking_deals(self) -> None:
    #     """
    #     Функция обработки проверки всех сделок на удаление и воронку
    #     """
    #     last_id = 0
    #     batch_number = 0

    #     logger.info("Начата проверка всех сделок.")
    #     try:
    #         while True:
    #             try:
    #                 deals = await self.repo.get_deals_batch(last_id=last_id)
    #             except Exception as e:
    #                 logger.error(
    #                     "Ошибка при получении пачки сделок (last_id=%s): %s",
    #                     last_id,
    #                     e,
    #                     exc_info=True,
    #                 )
    #                 raise

    #             if not deals:
    #                 logger.info("Все сделки обработаны.")
    #                 break

    #             logger.info(
    #                 "Обрабатывается пачка #%d, количество сделок: %d",
    #                 batch_number,
    #                 len(deals),
    #             )

    #             for deal in deals:
    #                 await self._process_deal_data(deal)

    #             last_id = deals[-1].external_id
    #             batch_number += 1

    #             await asyncio.sleep(0.1)
    #         logger.info("Проверка сделок завершена успешно.")

    #     except Exception as e:
    #         logger.critical(
    #             "Критическая ошибка в процессе проверки сделок: %s",
    #             e,
    #             exc_info=True,
    #         )
    #         raise

    # async def _process_deal_data(self, deal: DealDB) -> None:
    #     """Обрабатывает данные одной сделки из БД."""
    #     external_id = deal.external_id
    #     logger.debug("Обработка сделки с external_id=%s", external_id)

    #     try:
    #         deal_b24 = await self.bitrix_client.get(external_id)
    #         await asyncio.sleep(1)  # соблюдение рейт-лимитов API

    #         if deal_b24.category_id != 0:
    #             logger.info(
    #                 "Обновление категории для сделки %s: новая категория %s",
    #                 external_id,
    #                 deal_b24.category_id,
    #             )
    #             await self._update_category_deal(
    #                 external_id, deal_b24.category_id
    #             )
    #         else:
    #             logger.debug(
    #                 "Сделка %s имеет категорию 0 — пропуск.", external_id
    #             )

    #     except BitrixApiError as e:
    #         if e.is_not_found_error():
    #             logger.info(
    #                 "Сделка %s не найдена в Б24 — помечена как удалённая.",
    #                 external_id,
    #             )
    #             await self.repo.set_deleted_in_bitrix(external_id)
    #         else:
    #             logger.error(
    #                 "Ошибка API Битрикс24 при обработке сделки %s: %s",
    #                 external_id,
    #                 e,
    #                 exc_info=True,
    #             )
    #             raise
    #     except Exception as e:
    #         logger.error(
    #             "Неожиданная ошибка при обработке сделки %s: %s",
    #             external_id,
    #             e,
    #             exc_info=True,
    #         )
    #         raise

    # async def _update_category_deal(
    #     self, external_id: int, category_id: int
    # ) -> None:
    #     """Обновляет категорию сделки в локальной БД."""
    #     try:
    #         data: dict[str, Any] = {
    #             "external_id": external_id,
    #             "category_id": category_id,
    #         }
    #         deal_update = DealUpdate(**data)
    #         await self.repo.update(deal_update)
    #         logger.debug(
    #             "Категория для сделки %s успешно обновлена в БД.",
    #             external_id
    #         )
    #     except Exception as e:
    #         logger.error(
    #             "Ошибка при обновлении категории сделки %s в БД: %s",
    #             external_id,
    #             e,
    #             exc_info=True,
    #         )
    #         raise

    # async def send_notifications_overdue_deals(
    #     self,
    #     # notification_scope: int = NotificationScopeEnum.SUPERVISOR,
    #     chat_supervisor: int = settings.CHAT_SUPERVISOR,
    #     type_chat_supervisor: bool = settings.TYPE_CHAT_SUPERVISOR,
    # ) -> None:
    #     deal_processing_status_service = self.deal_processing_status_service
    #     await deal_processing_status_service.
    #         send_notifications_overdue_deals(
    #         notification_scope,
    #         chat_supervisor,
    #         type_chat_supervisor,
    #     )
