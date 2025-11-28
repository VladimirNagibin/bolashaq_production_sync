"""Add new statuses for deal

Revision ID: 0ddec39cb56b
Revises: f3a390000133
Create Date: 2025-11-27 17:07:53.092195

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0ddec39cb56b"
down_revision: Union[str, Sequence[str], None] = "f3a390000133"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE deal_status_enum ADD VALUE 'DEAL_LOSE'")
    op.execute("ALTER TYPE deal_status_enum ADD VALUE 'DEAL_WON'")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        "CREATE TYPE deal_status_enum_temp AS ENUM ("
        "'NEW', 'ACCEPTED', 'OFFER_NO', "
        "'OFFER_IN_AGREEMENT_SUPERVISOR', 'OFFER_APPROVED_SUPERVISOR', "
        "'OFFER_DISMISSED_SUPERVISOR', 'OFFER_SENT_CLIENT', "
        "'OFFER_APPROVED_CLIENT', 'OFFER_DISMISSED_CLIENT', "
        "'NOT_DEFINE')"
    )

    # Обновляем записи с новыми статусами на существующий
    op.execute(
        "UPDATE product_agreement_supervisor "
        "SET status_deal = 'NOT_DEFINE' "
        "WHERE status_deal IN ('DEAL_LOSE', 'DEAL_WON')"
    )
    op.alter_column(
        "product_agreement_supervisor",
        "status_deal",
        type="deal_status_enum_temp",
        postgresql_using="status_deal::text::deal_status_enum_temp",
    )

    op.execute(
        "UPDATE deals "
        "SET status_deal = 'NOT_DEFINE' "
        "WHERE status_deal IN ('DEAL_LOSE', 'DEAL_WON')"
    )
    op.alter_column(
        "deals",
        "status_deal",
        type="deal_status_enum_temp",
        postgresql_using="status_deal::text::deal_status_enum_temp",
    )

    op.execute("DROP TYPE deal_status_enum")
    op.execute("ALTER TYPE deal_status_enum_temp RENAME TO deal_status_enum")
