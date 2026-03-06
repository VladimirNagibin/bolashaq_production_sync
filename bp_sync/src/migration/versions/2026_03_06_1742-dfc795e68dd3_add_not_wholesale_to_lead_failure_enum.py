"""Add NOT_WHOLESALE to lead failure enum

Revision ID: dfc795e68dd3
Revises: 06d73f15013f
Create Date: 2026-03-06 17:42:56.869582

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "dfc795e68dd3"
down_revision: Union[str, Sequence[str], None] = "06d73f15013f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add NOT_WHOLESALE to enum."""

    # Добавляем новое значение в существующий enum
    op.execute("ALTER TYPE lead_failure_enum ADD VALUE 'NOT_WHOLESALE'")


def downgrade() -> None:
    """Remove NOT_WHOLESALE from enum."""

    # PostgreSQL не позволяет просто удалить значение из enum
    # Нужно создавать новый enum без этого значения

    # Создаем новый тип без NOT_WHOLESALE
    op.execute(
        "CREATE TYPE lead_failure_enum_new AS ENUM "
        "('SPAM', 'WRONG_CONTACT', 'NO_ANSWER', 'INVALID_CONTACT_DATA', "
        "'TEST_LEAD', 'DUPLICATE', 'OTHER')"
    )

    # Обновляем данные: преобразуем NOT_WHOLESALE в OTHER
    op.execute(
        "UPDATE leads SET failure_reason = 'OTHER' WHERE "
        "failure_reason = 'NOT_WHOLESALE'"
    )

    # Меняем тип колонки
    op.execute(
        "ALTER TABLE leads ALTER COLUMN failure_reason TYPE "
        "lead_failure_enum_new USING "
        "failure_reason::text::lead_failure_enum_new"
    )

    # Удаляем старый тип
    op.execute("DROP TYPE lead_failure_enum")

    # Переименовываем новый тип
    op.execute("ALTER TYPE lead_failure_enum_new RENAME TO lead_failure_enum")
