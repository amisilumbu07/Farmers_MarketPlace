from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from geoalchemy2 import Geography
from sqlalchemy import JSON, Boolean, CheckConstraint, DateTime, Float, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


ORDER_STATUSES = ("PENDING", "ACCEPTED", "READY_FOR_PICKUP", "IN_TRANSIT", "DELIVERED", "COMPLETED", "CANCELLED", "DISPUTED", "REFUNDED")
ORDER_STATUS_SQL = ", ".join(repr(status) for status in ORDER_STATUSES)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}"


class User(Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("role IN ('buyer', 'farmer', 'admin', 'transporter')", name="ck_users_role"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Token(Base):
    __tablename__ = "auth_tokens"
    token: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FarmerProfile(Base):
    __tablename__ = "farmer_profiles"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str | None] = mapped_column(String(30))


class Farm(Base):
    __tablename__ = "farms"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    farmer_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    location: Mapped[object] = mapped_column(Geography("POINT", srid=4326, spatial_index=True))


class Lot(Base):
    __tablename__ = "lots"
    __table_args__ = (CheckConstraint("quantity_kg >= 0", name="ck_lots_quantity"), CheckConstraint("price_per_kg > 0", name="ck_lots_price"))
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    farmer_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    farm_id: Mapped[str] = mapped_column(ForeignKey("farms.id", ondelete="CASCADE"), index=True)
    product: Mapped[str] = mapped_column(String(100), index=True)
    quantity_kg: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    price_per_kg: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)


class BuyerRequest(Base):
    __tablename__ = "buyer_requests"
    __table_args__ = (CheckConstraint("quantity_kg > 0", name="ck_requests_quantity"), CheckConstraint("radius_km > 0", name="ck_requests_radius"), CheckConstraint("status IN ('OPEN', 'ORDERED', 'CANCELLED')", name="ck_requests_status"))
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    buyer_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    product: Mapped[str] = mapped_column(String(100), index=True)
    quantity_kg: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    max_price_per_kg: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    location: Mapped[object | None] = mapped_column(Geography("POINT", srid=4326, spatial_index=True))
    radius_km: Mapped[float] = mapped_column(Float, default=50)
    status: Mapped[str] = mapped_column(String(20), default="OPEN")
    window_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    window_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class MatchPlan(Base):
    __tablename__ = "match_plans"
    request_id: Mapped[str] = mapped_column(ForeignKey("buyer_requests.id", ondelete="CASCADE"), primary_key=True)
    requested_quantity_kg: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    allocated_quantity_kg: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    complete: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Allocation(Base):
    __tablename__ = "allocations"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(ForeignKey("match_plans.request_id", ondelete="CASCADE"), index=True)
    lot_id: Mapped[str] = mapped_column(ForeignKey("lots.id", ondelete="CASCADE"))
    farmer_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    quantity_kg: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    price_per_kg: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    distance_km: Mapped[float] = mapped_column(Float)
    score: Mapped[float] = mapped_column(Float)
    distance_score: Mapped[float] = mapped_column(Float)
    price_score: Mapped[float] = mapped_column(Float)
    fulfilment_risk: Mapped[float] = mapped_column(Float)


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (CheckConstraint("quantity_kg > 0", name="ck_orders_quantity"), CheckConstraint(f"status IN ({ORDER_STATUS_SQL})", name="ck_orders_status"))
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    buyer_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    lot_id: Mapped[str] = mapped_column(ForeignKey("lots.id", ondelete="RESTRICT"), index=True)
    quantity_kg: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    status: Mapped[str] = mapped_column(String(20), default="PENDING", index=True)
    request_id: Mapped[str | None] = mapped_column(ForeignKey("buyer_requests.id", ondelete="SET NULL"), index=True)
    group_id: Mapped[str | None] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    dest_latitude: Mapped[float | None] = mapped_column(Float)
    dest_longitude: Mapped[float | None] = mapped_column(Float)
    window_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    window_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pool_id: Mapped[str | None] = mapped_column(ForeignKey("transport_pools.id", ondelete="SET NULL"), index=True)


class Vehicle(Base):
    __tablename__ = "vehicles"
    __table_args__ = (CheckConstraint("capacity_kg > 0", name="ck_vehicles_capacity"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    transporter_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    capacity_kg: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    base_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    cost_per_km: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class TransportPool(Base):
    __tablename__ = "transport_pools"
    __table_args__ = (CheckConstraint("status IN ('PROPOSED', 'CONFIRMED')", name="ck_pools_status"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    total_kg: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    separate_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    pooled_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    status: Mapped[str] = mapped_column(String(20), default="PROPOSED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TransportQuote(Base):
    __tablename__ = "transport_quotes"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    pool_id: Mapped[str] = mapped_column(ForeignKey("transport_pools.id", ondelete="CASCADE"), index=True)
    vehicle_id: Mapped[str] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"))
    cost: Mapped[Decimal] = mapped_column(Numeric(12, 2))


class Shipment(Base):
    __tablename__ = "shipments"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    pool_id: Mapped[str] = mapped_column(ForeignKey("transport_pools.id", ondelete="CASCADE"), unique=True)
    vehicle_id: Mapped[str | None] = mapped_column(ForeignKey("vehicles.id", ondelete="SET NULL"))
    route_km: Mapped[float] = mapped_column(Float)


class ShipmentStop(Base):
    __tablename__ = "shipment_stops"
    __table_args__ = (CheckConstraint("kind IN ('pickup', 'delivery')", name="ck_stops_kind"),)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    shipment_id: Mapped[str] = mapped_column(ForeignKey("shipments.id", ondelete="CASCADE"), index=True)
    seq: Mapped[int]
    kind: Mapped[str] = mapped_column(String(10))
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)


class Attestation(Base):
    __tablename__ = "attestations"
    __table_args__ = (UniqueConstraint("subject_type", "subject_id", "type", name="uq_attestation_once"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    subject_type: Mapped[str] = mapped_column(String(20))
    subject_id: Mapped[str] = mapped_column(String(64), index=True)
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(String(40))
    evidence_url: Mapped[str | None] = mapped_column(String(500))
    evidence_hash: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ReputationEvent(Base):
    __tablename__ = "reputation_events"
    __table_args__ = (UniqueConstraint("user_id", "type", "order_id", name="uq_reputation_event_once"),)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(40))
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Dispute(Base):
    __tablename__ = "disputes"
    __table_args__ = (CheckConstraint("status IN ('OPEN', 'RESOLVED')", name="ck_disputes_status"), CheckConstraint("resolution IN ('refund', 'complete')", name="ck_disputes_resolution"))
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), unique=True)
    opened_by: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    reason: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(10), default="OPEN")
    resolution: Mapped[str | None] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ExternalTransaction(Base):
    """One call to an outside payment/ledger system. Provider-specific ids live here and nowhere else."""
    __tablename__ = "external_transactions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String(120), unique=True)
    provider: Mapped[str] = mapped_column(String(20))  # mock / fiat / solana / x402 later
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    purpose: Mapped[str] = mapped_column(String(20))  # order / attestation / settlement
    external_id: Mapped[str | None] = mapped_column(String(128))  # e.g. Solana signature
    amount: Mapped[int] = mapped_column(default=0)  # minor units
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    status: Mapped[str] = mapped_column(String(10), default="PENDING")  # PENDING / CONFIRMED / FAILED
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
