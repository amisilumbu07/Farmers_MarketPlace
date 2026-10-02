from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from geoalchemy2 import Geography
from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}"


class User(Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("role IN ('buyer', 'farmer', 'admin')", name="ck_users_role"),)
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
    __table_args__ = (CheckConstraint("quantity_kg > 0", name="ck_orders_quantity"), CheckConstraint("status IN ('PENDING', 'ACCEPTED', 'COMPLETED', 'CANCELLED')", name="ck_orders_status"))
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    buyer_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    lot_id: Mapped[str] = mapped_column(ForeignKey("lots.id", ondelete="RESTRICT"), index=True)
    quantity_kg: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    status: Mapped[str] = mapped_column(String(20), default="PENDING", index=True)
    request_id: Mapped[str | None] = mapped_column(ForeignKey("buyer_requests.id", ondelete="SET NULL"), index=True)
    group_id: Mapped[str | None] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
