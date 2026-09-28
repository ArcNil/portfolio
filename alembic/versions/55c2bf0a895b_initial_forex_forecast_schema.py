"""Initial forex forecast schema

Creates the forex_pair and daily_rate tables, ported from
ArcNil/forex_forecast (src/migrations/versions/55c2bf0a895b_initial_schema.py).

Revision ID: 55c2bf0a895b
Revises:
Create Date: 2026-09-25

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "55c2bf0a895b"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "forex_pair",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("from_currency", sa.String(length=5), nullable=False),
        sa.Column("to_currency", sa.String(length=5), nullable=False),
        sa.Column("current_rate", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "daily_rate",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rate", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("forex_pair_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["forex_pair_id"], ["forex_pair.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_daily_rate_forex_pair_id", "daily_rate", ["forex_pair_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_daily_rate_forex_pair_id", table_name="daily_rate")
    op.drop_table("daily_rate")
    op.drop_table("forex_pair")