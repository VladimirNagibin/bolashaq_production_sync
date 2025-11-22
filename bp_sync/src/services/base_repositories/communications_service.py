from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import logger
from models.communications import (
    CommunicationChannel,
    CommunicationChannelType,
)
from schemas.base_schemas import CommunicationChannel as CommSchema
from schemas.enums import CommunicationType, EntityType


class CommunicationService:
    """Сервис для работы с коммуникационными каналами"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_communication_channel(
        self,
        entity_type: EntityType,
        entity_id: int,
        comm_schema: CommSchema,
        comm_type: CommunicationType,
    ) -> bool:
        """Создает канал связи для любой сущности"""
        try:
            # Поиск или создание типа канала
            stmt = select(CommunicationChannelType).where(
                CommunicationChannelType.type_id == comm_type.value,
                CommunicationChannelType.value_type == comm_schema.value_type,
            )
            result = await self.session.execute(stmt)
            channel_type = result.scalars().first()

            if not channel_type:
                logger.info(
                    "Creating new channel type: "
                    f"{comm_type.value}/{comm_schema.value_type} "
                )
                channel_type = CommunicationChannelType(
                    type_id=comm_type.value,
                    value_type=comm_schema.value_type,
                    description=f"Automatically created for {comm_type.value}",
                )
                self.session.add(channel_type)
                await self.session.flush()
                await self.session.refresh(channel_type)

                logger.debug(
                    f"Created channel type ID: {channel_type.id} "
                    f"({comm_type.value}/{comm_schema.value_type})"
                )

            # Создание канала связи
            channel = CommunicationChannel(
                external_id=comm_schema.external_id,
                entity_type=entity_type.value,
                entity_id=entity_id,
                channel_type_id=channel_type.id,
                value=comm_schema.value,
            )

            self.session.add(channel)
            await self.session.flush()
            logger.debug(
                "Created communication channel "
                f"{comm_type.value} - {comm_schema.value}"
            )
            return True

        except SQLAlchemyError as e:
            logger.error(
                f"Database error {str(e)} creating communication channel for "
                f"Type: {comm_type.value}, Value: {comm_schema.value}"
            )
            # Откатываем изменения в текущей транзакции
            await self.session.rollback()
            return False

        except Exception as e:
            logger.exception(
                f"Unexpected error {str(e)} creating communication channel "
                f"Type: {comm_type.value}, Value: {comm_schema.value}"
            )
            await self.session.rollback()
            return False

    async def update_communications(
        self,
        entity_type: EntityType,
        entity_id: int,
        comm_type: CommunicationType,
        new_comms: list[CommSchema] | None,
    ) -> None:
        """
        Обновляет коммуникации лида:
        - Если new_comms is None - пропускаем обновление
        - Если пустой список - удаляем все коммуникации этого типа
        - Если список с элементами - заменяем существующие
        """
        if new_comms is None:
            return

        # Удаление старых коммуникаций этого типа
        await self.delete_communications(entity_type, entity_id, comm_type)

        # Создание новых коммуникаций
        if new_comms:
            for comm_schema in new_comms:
                await self.create_communication_channel(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    comm_schema=comm_schema,
                    comm_type=comm_type,
                )

    async def delete_communications(
        self,
        entity_type: EntityType,
        entity_id: int,
        comm_type: CommunicationType | None = None,
    ) -> None:
        """Удаляет коммуникации сущности"""
        try:
            delete_stmt = delete(CommunicationChannel).where(
                CommunicationChannel.entity_type == entity_type.value,
                CommunicationChannel.entity_id == entity_id,
            )

            if comm_type:
                subquery = (
                    select(CommunicationChannelType.id)
                    .where(CommunicationChannelType.type_id == comm_type.value)
                    .scalar_subquery()
                )
                delete_stmt = delete_stmt.where(
                    CommunicationChannel.channel_type_id.in_(subquery)
                )

            await self.session.execute(delete_stmt)
            logger.debug(
                f"Deleted communications for {entity_type} ID={entity_id}, "
                f"type: {comm_type.value if comm_type else 'all'}"
            )
        except SQLAlchemyError as e:
            logger.error(
                f"Error deleting communications for {entity_type} "
                f"ID={entity_id}: {str(e)}"
            )
            raise
