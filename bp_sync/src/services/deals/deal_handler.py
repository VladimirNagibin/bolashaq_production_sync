from datetime import date
from typing import TYPE_CHECKING, Any, ClassVar

from core.logger import logger
from schemas.deal_schemas import DealCreate, DealUpdate
from schemas.enums import (
    DealStagesEnum,
    DealStatusEnum,
    StageSemanticEnum,
)

from ..exceptions import (
    DealNotFoundError,
    DealProcessingError,
    InvalidDealStateError,
)

if TYPE_CHECKING:
    from .deal_services import DealClient


class DealHandler:
    """
    Обработчик, который применяет бизнес-логику к сделке в зависимости от ее
    состояния.
    """

    STATUS_HANDLERS: ClassVar[dict[DealStatusEnum, str]] = {
        DealStatusEnum.NEW: "_handle_deal_in_new_status",
        DealStatusEnum.ACCEPTED: "_handle_deal_in_accepted_status",
    }

    def __init__(self, deal_client: "DealClient") -> None:
        self.deal_client = deal_client

    async def handle_deal(
        self,
        deal_b24: DealCreate,
        deal_db: DealCreate | None,
        changes: dict[str, dict[str, Any]] | None,
    ) -> None:
        """
        Диспетчер обработки, применяющий различную логику в зависимости
        от состояния сделки
        """
        logger.debug(f"Starting handling for deal {deal_b24.external_id}")

        # 1. Обработка провальных сделок
        if deal_b24.stage_semantic_id == StageSemanticEnum.FAIL:
            await self._handle_fail_deal(deal_b24, deal_db)
            return

        # 2. Обработка новых сделок (которых еще нет в нашей БД)
        if not deal_db:
            await self._handle_new_deal(deal_b24)
            return

        # 3. Проверка и откат некорректного изменения статуса в Bitrix24
        await self._check_deal_status(deal_b24, deal_db)

        # 4. Диспетчеризация к обработчику для текущего статуса
        handler_name = self.STATUS_HANDLERS.get(deal_b24.status_deal)

        deal_handler_error = DealProcessingError(
            f"Not found handler for status: {deal_b24.status_deal.value}",
            self.deal_client.get_external_id(deal_b24),
        )
        if not handler_name:
            raise deal_handler_error

        handler = getattr(self, handler_name)
        if not handler:
            raise deal_handler_error

        await handler(deal_b24, deal_db, changes)
        logger.debug(f"Finished handling for deal {deal_b24.external_id}")

    async def _handle_fail_deal(
        self,
        deal_b24: DealCreate,
        deal_db: DealCreate | None,
    ) -> None:
        """Обработка провальной сделки"""
        logger.info(f"Handle fail deal: {deal_b24.external_id}")
        today = date.today()
        needs_status_update = (
            deal_b24.status_deal != DealStatusEnum.DEAL_LOSE
            or (deal_db and deal_db.status_deal != DealStatusEnum.DEAL_LOSE)
        )
        if needs_status_update:
            self.deal_client.update_tracker.update_field(
                "status_deal", DealStatusEnum.DEAL_LOSE, deal_b24
            )
            logger.info(
                f"Deal {deal_b24.external_id} status set to DEAL_LOSE."
            )
            deal_moved_date = (
                deal_db.moved_date.date()
                if deal_db and deal_db.moved_date
                else None
            )
            if deal_moved_date != today:
                self.deal_client.update_tracker.update_field(
                    "moved_date", today, deal_b24
                )
                logger.info(
                    f"Deal {deal_b24.external_id} moved_date updated to "
                    f"{today}."
                )

    async def _handle_new_deal(
        self,
        deal_b24: DealCreate,
    ) -> None:
        """Обработка новой сделки"""
        logger.info(f"Handling new deal: {deal_b24.external_id}")

        if deal_b24.status_deal != DealStatusEnum.NEW:
            self.deal_client.update_tracker.update_field(
                "status_deal", DealStatusEnum.NEW, deal_b24
            )
        repo = self.deal_client.repo
        initial_stage_id = await repo.get_external_id_by_sort_order_stage(
            DealStagesEnum.NEW,
        )
        if deal_b24.stage_id != initial_stage_id:
            self.deal_client.update_tracker.update_field(
                "stage_id", initial_stage_id, deal_b24
            )
        self.deal_client.update_tracker.update_field(
            "moved_date", date.today(), deal_b24
        )
        logger.info(
            f"Deal {deal_b24.external_id} initialized with status NEW "
            f"and stage {initial_stage_id}."
        )
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
                self.deal_client.get_external_id(deal_b24),
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

            await self.deal_client.bitrix_client.update(deal_update)
            raise InvalidDealStateError(
                f"Deal {deal_b24.external_id} status was changed externally. "
                f"Rolled back to '{deal_db.status_deal.value}'."
            )

    async def handle_deal_in_new_status(
        self,
        deal_b24: DealCreate,
        deal_db: DealCreate | None,
        changes: dict[str, dict[str, Any]] | None,
    ) -> None:
        """Обработка сделки, которая находится в статусе 'Новая'."""
        logger.info(f"Handling deal in 'NEW' status: {deal_b24.external_id}")
        repo = self.deal_client.repo
        stage_number = await repo.get_sort_order_by_external_id_stage(
            deal_b24.stage_id
        )

        if stage_number and stage_number > DealStagesEnum.NEW:
            logger.debug(
                "Deal stage advanced beyond initial",
                extra={
                    "deal_id": deal_b24.external_id,
                    "stage_number": stage_number,
                },
            )
            if stage_number > DealStagesEnum.NEEDS_IDENTIFICATION:
                second_stage = await repo.get_external_id_by_sort_order_stage(
                    DealStagesEnum.NEEDS_IDENTIFICATION
                )
                self.deal_client.update_tracker.update_field(
                    "stage_id", second_stage, deal_b24
                )
                logger.info(
                    f"Deal {deal_b24.external_id} stage rolled back to stage 2"
                )
            self.deal_client.update_tracker.update_field(
                "status_deal", DealStatusEnum.ACCEPTED, deal_b24
            )
            logger.info(
                f"Deal {deal_b24.external_id} status updated to ACCEPTED."
            )

    async def _handle_deal_in_accepted_status(
        self,
        deal_b24: DealCreate,
        deal_db: DealCreate | None,
        changes: dict[str, dict[str, Any]] | None,
    ) -> None:
        """Обработка сделки, которая находится в статусе 'Новая'."""
        logger.info(
            f"Handling deal in 'ACCEPTED' status: {deal_b24.external_id}"
        )
        repo = self.deal_client.repo
        stage_number = await repo.get_sort_order_by_external_id_stage(
            deal_b24.stage_id
        )
        available_stage_number = DealStagesEnum.NEEDS_IDENTIFICATION

        if deal_b24.company_id and await self._check_products(deal_b24):
            available_stage_number = DealStagesEnum.OFFER_PREPARE
        if stage_number != available_stage_number:
            available_stage = await repo.get_external_id_by_sort_order_stage(
                available_stage_number
            )
            self.deal_client.update_tracker.update_field(
                "stage_id", available_stage, deal_b24
            )

    async def _check_products(self, deal_b24: DealCreate) -> bool:

        return True
