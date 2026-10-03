"""Add attestations, reputation events and disputes."""

from alembic import op
import sqlalchemy as sa

revision = "0003_trust"
down_revision = "0002_logistics"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("attestations", sa.Column("id", sa.String(64), primary_key=True), sa.Column("subject_type", sa.String(20), nullable=False), sa.Column("subject_id", sa.String(64), nullable=False), sa.Column("actor_id", sa.String(64), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("type", sa.String(40), nullable=False), sa.Column("evidence_url", sa.String(500)), sa.Column("evidence_hash", sa.String(64)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.UniqueConstraint("subject_type", "subject_id", "type", name="uq_attestation_once"))
    op.create_index("ix_attestations_subject_id", "attestations", ["subject_id"])
    op.create_table("reputation_events", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("type", sa.String(40), nullable=False), sa.Column("order_id", sa.String(64), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.UniqueConstraint("user_id", "type", "order_id", name="uq_reputation_event_once"))
    op.create_index("ix_reputation_events_user_id", "reputation_events", ["user_id"])
    op.create_table("disputes", sa.Column("id", sa.String(64), primary_key=True), sa.Column("order_id", sa.String(64), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, unique=True), sa.Column("opened_by", sa.String(64), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("reason", sa.String(500), nullable=False), sa.Column("status", sa.String(10), nullable=False, server_default="OPEN"), sa.Column("resolution", sa.String(10)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("resolved_at", sa.DateTime(timezone=True)), sa.CheckConstraint("status IN ('OPEN', 'RESOLVED')", name="ck_disputes_status"), sa.CheckConstraint("resolution IN ('refund', 'complete')", name="ck_disputes_resolution"))


def downgrade():
    for table in ("disputes", "reputation_events", "attestations"):
        op.drop_table(table)
