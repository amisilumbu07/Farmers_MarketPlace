"""Add order delivery states and pooled transportation tables."""

from alembic import op
import sqlalchemy as sa

from api.app.shared.store import ORDER_STATUS_SQL

revision = "0002_logistics"
down_revision = "0001_marketplace"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("ck_users_role", "users")
    op.create_check_constraint("ck_users_role", "users", "role IN ('buyer', 'farmer', 'admin', 'transporter')")
    op.add_column("buyer_requests", sa.Column("window_start", sa.DateTime(timezone=True)))
    op.add_column("buyer_requests", sa.Column("window_end", sa.DateTime(timezone=True)))

    op.create_table("vehicles", sa.Column("id", sa.String(64), primary_key=True), sa.Column("transporter_id", sa.String(64), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("capacity_kg", sa.Numeric(12, 3), nullable=False), sa.Column("base_fee", sa.Numeric(12, 2), nullable=False), sa.Column("cost_per_km", sa.Numeric(12, 2), nullable=False), sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.CheckConstraint("capacity_kg > 0", name="ck_vehicles_capacity"))
    op.create_index("ix_vehicles_transporter_id", "vehicles", ["transporter_id"])
    op.create_table("transport_pools", sa.Column("id", sa.String(64), primary_key=True), sa.Column("total_kg", sa.Numeric(12, 3), nullable=False), sa.Column("separate_cost", sa.Numeric(12, 2), nullable=False), sa.Column("pooled_cost", sa.Numeric(12, 2), nullable=False), sa.Column("status", sa.String(20), nullable=False, server_default="PROPOSED"), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.CheckConstraint("status IN ('PROPOSED', 'CONFIRMED')", name="ck_pools_status"))

    op.drop_constraint("ck_orders_status", "orders")
    op.create_check_constraint("ck_orders_status", "orders", f"status IN ({ORDER_STATUS_SQL})")
    op.add_column("orders", sa.Column("dest_latitude", sa.Float()))
    op.add_column("orders", sa.Column("dest_longitude", sa.Float()))
    op.add_column("orders", sa.Column("window_start", sa.DateTime(timezone=True)))
    op.add_column("orders", sa.Column("window_end", sa.DateTime(timezone=True)))
    op.add_column("orders", sa.Column("pool_id", sa.String(64), sa.ForeignKey("transport_pools.id", ondelete="SET NULL")))
    op.create_index("ix_orders_pool_id", "orders", ["pool_id"])

    op.create_table("transport_quotes", sa.Column("id", sa.String(64), primary_key=True), sa.Column("pool_id", sa.String(64), sa.ForeignKey("transport_pools.id", ondelete="CASCADE"), nullable=False), sa.Column("vehicle_id", sa.String(64), sa.ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False), sa.Column("cost", sa.Numeric(12, 2), nullable=False))
    op.create_index("ix_transport_quotes_pool_id", "transport_quotes", ["pool_id"])
    op.create_table("shipments", sa.Column("id", sa.String(64), primary_key=True), sa.Column("pool_id", sa.String(64), sa.ForeignKey("transport_pools.id", ondelete="CASCADE"), nullable=False, unique=True), sa.Column("vehicle_id", sa.String(64), sa.ForeignKey("vehicles.id", ondelete="SET NULL")), sa.Column("route_km", sa.Float(), nullable=False))
    op.create_table("shipment_stops", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("shipment_id", sa.String(64), sa.ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False), sa.Column("seq", sa.Integer(), nullable=False), sa.Column("kind", sa.String(10), nullable=False), sa.Column("order_id", sa.String(64), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False), sa.Column("latitude", sa.Float(), nullable=False), sa.Column("longitude", sa.Float(), nullable=False), sa.CheckConstraint("kind IN ('pickup', 'delivery')", name="ck_stops_kind"))
    op.create_index("ix_shipment_stops_shipment_id", "shipment_stops", ["shipment_id"])
    op.create_index("ix_shipment_stops_order_id", "shipment_stops", ["order_id"])


def downgrade():
    for table in ("shipment_stops", "shipments", "transport_quotes"):
        op.drop_table(table)
    op.drop_index("ix_orders_pool_id", "orders")
    for column in ("pool_id", "window_end", "window_start", "dest_longitude", "dest_latitude"):
        op.drop_column("orders", column)
    op.drop_constraint("ck_orders_status", "orders")
    op.create_check_constraint("ck_orders_status", "orders", "status IN ('PENDING', 'ACCEPTED', 'COMPLETED', 'CANCELLED')")
    op.drop_table("transport_pools")
    op.drop_table("vehicles")
    op.drop_column("buyer_requests", "window_end")
    op.drop_column("buyer_requests", "window_start")
    op.drop_constraint("ck_users_role", "users")
    op.create_check_constraint("ck_users_role", "users", "role IN ('buyer', 'farmer', 'admin')")
