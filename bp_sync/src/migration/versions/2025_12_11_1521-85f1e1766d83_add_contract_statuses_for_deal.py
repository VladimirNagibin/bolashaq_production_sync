"""Add contract statuses for deal

Revision ID: 85f1e1766d83
Revises: 70c480de4d42
Create Date: 2025-12-11 15:21:48.851535

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "85f1e1766d83"
down_revision: Union[str, Sequence[str], None] = "70c480de4d42"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE deal_status_enum ADD VALUE 'CONTRACT_NO'")
    op.execute(
        "ALTER TYPE deal_status_enum ADD VALUE "
        "'DRAFT_CONTRACT_IN_AGREEMENT_SUPERVISOR'"
    )
    op.execute(
        "ALTER TYPE deal_status_enum ADD VALUE "
        "'DRAFT_CONTRACT_APPROVED_SUPERVISOR'"
    )
    op.execute(
        "ALTER TYPE deal_status_enum ADD VALUE "
        "'DRAFT_CONTRACT_DISMISSED_SUPERVISOR'"
    )
    op.execute(
        "ALTER TYPE deal_status_enum ADD VALUE 'DRAFT_CONTRACT_SENT_CLIENT'"
    )
    op.execute(
        "ALTER TYPE deal_status_enum ADD VALUE "
        "'DRAFT_CONTRACT_APPROVED_CLIENT'"
    )
    op.execute(
        "ALTER TYPE deal_status_enum ADD VALUE "
        "'DRAFT_CONTRACT_DISMISSED_CLIENT'"
    )
    op.execute(
        "ALTER TYPE deal_status_enum ADD VALUE 'CONTRACT_IN_SIGN_SUPERVISOR'"
    )
    op.execute(
        "ALTER TYPE deal_status_enum ADD VALUE 'CONTRACT_SIGN_SUPERVISOR'"
    )
    op.execute(
        "ALTER TYPE deal_status_enum ADD VALUE 'CONTRACT_UNSIGN_SUPERVISOR'"
    )
    op.execute(
        "ALTER TYPE deal_status_enum ADD VALUE 'CONTRACT_SENT_IN_SIGN_CLIENT'"
    )
    op.execute("ALTER TYPE deal_status_enum ADD VALUE 'CONTRACT_SIGN_CLIENT'")
    op.execute(
        "ALTER TYPE deal_status_enum ADD VALUE 'CONTRACT_UNSIGN_CLIENT'"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        "CREATE TYPE deal_status_enum_temp AS ENUM ("
        "'NEW', 'ACCEPTED', 'OFFER_NO', "
        "'OFFER_IN_AGREEMENT_SUPERVISOR', 'OFFER_APPROVED_SUPERVISOR', "
        "'OFFER_DISMISSED_SUPERVISOR', 'OFFER_SENT_CLIENT', "
        "'OFFER_APPROVED_CLIENT', 'OFFER_DISMISSED_CLIENT', "
        "'NOT_DEFINE', 'DEAL_LOSE', 'DEAL_WON')"
    )

    # Обновляем записи с новыми статусами на существующий
    op.execute(
        "UPDATE product_agreement_supervisor "
        "SET status_deal = 'NOT_DEFINE' "
        "WHERE status_deal IN ('CONTRACT_NO', "
        "'DRAFT_CONTRACT_IN_AGREEMENT_SUPERVISOR', "
        "'DRAFT_CONTRACT_APPROVED_SUPERVISOR', "
        "'DRAFT_CONTRACT_DISMISSED_SUPERVISOR', "
        "'DRAFT_CONTRACT_SENT_CLIENT', "
        "'DRAFT_CONTRACT_APPROVED_CLIENT', "
        "'DRACT_CONTRACT_DISMISSED_CLIENT', "
        "'CONTRACT_IN_SIGN_SUPERVISOR', "
        "'CONTRACT_SIGN_SUPERVISOR', "
        "'CONTRACT_UNSIGN_SUPERVISOR', "
        "'CONTRACT_SENT_IN_SIGN_CLIENT', "
        "'CONTRACT_SIGN_CLIENT', "
        "'CONTRACT_UNSIGN_CLIENT')"
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
        "WHERE status_deal IN ('CONTRACT_NO', "
        "'DRAFT_CONTRACT_IN_AGREEMENT_SUPERVISOR', "
        "'DRAFT_CONTRACT_APPROVED_SUPERVISOR', "
        "'DRAFT_CONTRACT_DISMISSED_SUPERVISOR', "
        "'DRAFT_CONTRACT_SENT_CLIENT', "
        "'DRAFT_CONTRACT_APPROVED_CLIENT', "
        "'DRACT_CONTRACT_DISMISSED_CLIENT', "
        "'CONTRACT_IN_SIGN_SUPERVISOR', "
        "'CONTRACT_SIGN_SUPERVISOR', "
        "'CONTRACT_UNSIGN_SUPERVISOR', "
        "'CONTRACT_SENT_IN_SIGN_CLIENT', "
        "'CONTRACT_SIGN_CLIENT', "
        "'CONTRACT_UNSIGN_CLIENT')"
    )
    op.alter_column(
        "deals",
        "status_deal",
        type="deal_status_enum_temp",
        postgresql_using="status_deal::text::deal_status_enum_temp",
    )

    op.execute("DROP TYPE deal_status_enum")
    op.execute("ALTER TYPE deal_status_enum_temp RENAME TO deal_status_enum")
