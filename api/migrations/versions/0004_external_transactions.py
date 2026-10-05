"""Add external_transactions (payment / ledger calls, provider-agnostic)."""

from alembic import op
import sqlalchemy as sa

revision = "0004_external_transactions"
down_revision = "0003_trust"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("external_transactions", sa.Column("id", sa.String(64), primary_key=True), sa.Column("idempotency_key", sa.String(120), nullable=False, unique=True), sa.Column("provider", sa.String(20), nullable=False), sa.Column("order_id", sa.String(64), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False), sa.Column("purpose", sa.String(20), nullable=False), sa.Column("external_id", sa.String(128)), sa.Column("amount", sa.Integer(), nullable=False, server_default="0"), sa.Column("currency", sa.String(8), nullable=False, server_default="USD"), sa.Column("status", sa.String(10), nullable=False, server_default="PENDING"), sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_external_transactions_order_id", "external_transactions", ["order_id"])


def downgrade():
    op.drop_table("external_transactions")
