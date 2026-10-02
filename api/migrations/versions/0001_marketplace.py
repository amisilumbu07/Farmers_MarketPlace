"""Create marketplace schema with PostGIS locations."""

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geography

revision = "0001_marketplace"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.create_table("users", sa.Column("id", sa.String(64), primary_key=True), sa.Column("email", sa.String(320), nullable=False), sa.Column("password", sa.String(255), nullable=False), sa.Column("role", sa.String(20), nullable=False), sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.CheckConstraint("role IN ('buyer', 'farmer', 'admin')", name="ck_users_role"))
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table("auth_tokens", sa.Column("token", sa.String(64), primary_key=True), sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_auth_tokens_user_id", "auth_tokens", ["user_id"])
    op.create_table("farmer_profiles", sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True), sa.Column("display_name", sa.String(100), nullable=False), sa.Column("phone", sa.String(30)))
    op.create_table("farms", sa.Column("id", sa.String(64), primary_key=True), sa.Column("farmer_id", sa.String(64), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("name", sa.String(120), nullable=False), sa.Column("latitude", sa.Float(), nullable=False), sa.Column("longitude", sa.Float(), nullable=False), sa.Column("location", Geography("POINT", srid=4326, spatial_index=False), nullable=False))
    op.create_index("ix_farms_farmer_id", "farms", ["farmer_id"])
    op.create_index("idx_farms_location", "farms", ["location"], postgresql_using="gist")
    op.create_table("lots", sa.Column("id", sa.String(64), primary_key=True), sa.Column("farmer_id", sa.String(64), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("farm_id", sa.String(64), sa.ForeignKey("farms.id", ondelete="CASCADE"), nullable=False), sa.Column("product", sa.String(100), nullable=False), sa.Column("quantity_kg", sa.Numeric(12, 3), nullable=False), sa.Column("price_per_kg", sa.Numeric(12, 2), nullable=False), sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.CheckConstraint("quantity_kg >= 0", name="ck_lots_quantity"), sa.CheckConstraint("price_per_kg > 0", name="ck_lots_price"))
    for column in ("farmer_id", "farm_id", "product", "active"):
        op.create_index(f"ix_lots_{column}", "lots", [column])
    op.create_table("buyer_requests", sa.Column("id", sa.String(64), primary_key=True), sa.Column("buyer_id", sa.String(64), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("product", sa.String(100), nullable=False), sa.Column("quantity_kg", sa.Numeric(12, 3), nullable=False), sa.Column("max_price_per_kg", sa.Numeric(12, 2)), sa.Column("latitude", sa.Float()), sa.Column("longitude", sa.Float()), sa.Column("location", Geography("POINT", srid=4326, spatial_index=False)), sa.Column("radius_km", sa.Float(), nullable=False, server_default="50"), sa.Column("status", sa.String(20), nullable=False, server_default="OPEN"), sa.CheckConstraint("quantity_kg > 0", name="ck_requests_quantity"), sa.CheckConstraint("radius_km > 0", name="ck_requests_radius"), sa.CheckConstraint("status IN ('OPEN', 'ORDERED', 'CANCELLED')", name="ck_requests_status"))
    for column in ("buyer_id", "product"):
        op.create_index(f"ix_buyer_requests_{column}", "buyer_requests", [column])
    op.create_index("idx_buyer_requests_location", "buyer_requests", ["location"], postgresql_using="gist")
    op.create_table("match_plans", sa.Column("request_id", sa.String(64), sa.ForeignKey("buyer_requests.id", ondelete="CASCADE"), primary_key=True), sa.Column("requested_quantity_kg", sa.Numeric(12, 3), nullable=False), sa.Column("allocated_quantity_kg", sa.Numeric(12, 3), nullable=False), sa.Column("complete", sa.Boolean(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_table("allocations", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("request_id", sa.String(64), sa.ForeignKey("match_plans.request_id", ondelete="CASCADE"), nullable=False), sa.Column("lot_id", sa.String(64), sa.ForeignKey("lots.id", ondelete="CASCADE"), nullable=False), sa.Column("farmer_id", sa.String(64), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("quantity_kg", sa.Numeric(12, 3), nullable=False), sa.Column("price_per_kg", sa.Numeric(12, 2), nullable=False), sa.Column("distance_km", sa.Float(), nullable=False), sa.Column("score", sa.Float(), nullable=False), sa.Column("distance_score", sa.Float(), nullable=False), sa.Column("price_score", sa.Float(), nullable=False), sa.Column("fulfilment_risk", sa.Float(), nullable=False))
    op.create_index("ix_allocations_request_id", "allocations", ["request_id"])
    op.create_table("orders", sa.Column("id", sa.String(64), primary_key=True), sa.Column("buyer_id", sa.String(64), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("lot_id", sa.String(64), sa.ForeignKey("lots.id", ondelete="RESTRICT"), nullable=False), sa.Column("quantity_kg", sa.Numeric(12, 3), nullable=False), sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"), sa.Column("request_id", sa.String(64), sa.ForeignKey("buyer_requests.id", ondelete="SET NULL")), sa.Column("group_id", sa.String(64)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.CheckConstraint("quantity_kg > 0", name="ck_orders_quantity"), sa.CheckConstraint("status IN ('PENDING', 'ACCEPTED', 'COMPLETED', 'CANCELLED')", name="ck_orders_status"))
    for column in ("buyer_id", "lot_id", "status", "request_id", "group_id"):
        op.create_index(f"ix_orders_{column}", "orders", [column])


def downgrade():
    for table in ("orders", "allocations", "match_plans", "buyer_requests", "lots", "farms", "farmer_profiles", "auth_tokens", "users"):
        op.drop_table(table)
