from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from ..shared.store import Farm, Lot, Order, Shipment, ShipmentStop, TransportPool, TransportQuote, Vehicle, new_id
from .pooling import PoolOrder, delivery_cost, propose_pools
from .routing import FallbackRoutingProvider, MockRoutingProvider, RoutingProvider

DEFAULT_CAPACITY_KG = 1000


def create_pools(db: Session, provider: RoutingProvider | None = None) -> list[TransportPool]:
    provider = provider or FallbackRoutingProvider(MockRoutingProvider())
    rows = db.execute(
        select(Order, Farm)
        .join(Lot, Lot.id == Order.lot_id)
        .join(Farm, Farm.id == Lot.farm_id)
        .where(Order.status.in_(("ACCEPTED", "READY_FOR_PICKUP")), Order.pool_id.is_(None), Order.dest_latitude.is_not(None))
        .order_by(Order.id)
        .with_for_update(of=Order)
    ).all()
    orders = {order.id: order for order, _ in rows}
    vehicles = list(db.scalars(select(Vehicle).where(Vehicle.active.is_(True))))
    capacity = max((float(v.capacity_kg) for v in vehicles), default=DEFAULT_CAPACITY_KG)
    pool_orders = [PoolOrder(o.id, float(o.quantity_kg), (f.latitude, f.longitude), (o.dest_latitude, o.dest_longitude), o.window_start, o.window_end) for o, f in rows]

    pools = []
    for proposal in propose_pools(pool_orders, provider, capacity):
        total_kg = sum(o.kg for o in proposal.orders)
        pool = TransportPool(id=new_id("pool"), total_kg=Decimal(str(total_kg)), separate_cost=Decimal(str(proposal.separate_cost)), pooled_cost=Decimal(str(proposal.pooled_cost)), status="PROPOSED")
        db.add(pool)
        db.flush()
        shipment = Shipment(id=new_id("shp"), pool_id=pool.id, route_km=proposal.route_km)
        db.add(shipment)
        db.flush()
        db.add_all(ShipmentStop(shipment_id=shipment.id, seq=i, kind=kind, order_id=oid, latitude=point[0], longitude=point[1]) for i, (kind, oid, point) in enumerate(proposal.stops))
        for order in proposal.orders:
            orders[order.order_id].pool_id = pool.id
        for vehicle in vehicles:
            if float(vehicle.capacity_kg) >= total_kg:
                cost = delivery_cost(proposal.route_km, float(vehicle.base_fee), float(vehicle.cost_per_km))
                db.add(TransportQuote(id=new_id("qte"), pool_id=pool.id, vehicle_id=vehicle.id, cost=Decimal(str(round(cost, 2)))))
        pools.append(pool)
    db.flush()
    return pools


def confirm_pool(db: Session, pool_id: str, quote_id: str, transporter_id: str) -> TransportPool:
    pool = db.scalar(select(TransportPool).where(TransportPool.id == pool_id).with_for_update())
    if not pool:
        raise HTTPException(status_code=404, detail="Pool not found")
    if pool.status != "PROPOSED":
        raise HTTPException(status_code=409, detail="Pool already confirmed")
    quote = db.get(TransportQuote, quote_id)
    if not quote or quote.pool_id != pool_id:
        raise HTTPException(status_code=404, detail="Quote not found for this pool")
    if db.get(Vehicle, quote.vehicle_id).transporter_id != transporter_id:
        raise HTTPException(status_code=403, detail="Quote belongs to another transporter")
    db.scalar(select(Shipment).where(Shipment.pool_id == pool_id)).vehicle_id = quote.vehicle_id
    pool.status = "CONFIRMED"
    return pool


def transporter_has_order(db: Session, order_id: str, transporter_id: str) -> bool:
    return db.scalar(
        select(ShipmentStop.id)
        .join(Shipment, Shipment.id == ShipmentStop.shipment_id)
        .join(Vehicle, Vehicle.id == Shipment.vehicle_id)
        .where(ShipmentStop.order_id == order_id, Vehicle.transporter_id == transporter_id)
        .limit(1)
    ) is not None


def pool_view(db: Session, pool: TransportPool) -> dict:
    shipment = db.scalar(select(Shipment).where(Shipment.pool_id == pool.id))
    stops = db.scalars(select(ShipmentStop).where(ShipmentStop.shipment_id == shipment.id).order_by(ShipmentStop.seq))
    quotes = db.scalars(select(TransportQuote).where(TransportQuote.pool_id == pool.id).order_by(TransportQuote.cost))
    separate, pooled = float(pool.separate_cost), float(pool.pooled_cost)
    return {
        "id": pool.id, "status": pool.status, "total_kg": float(pool.total_kg),
        "separate_cost": separate, "pooled_cost": pooled, "savings": round(separate - pooled, 2), "savings_pct": round(100 * (separate - pooled) / separate, 1),
        "vehicle_id": shipment.vehicle_id, "route_km": round(shipment.route_km, 2),
        "stops": [{"seq": s.seq, "kind": s.kind, "order_id": s.order_id, "latitude": s.latitude, "longitude": s.longitude} for s in stops],
        "quotes": [{"id": q.id, "vehicle_id": q.vehicle_id, "cost": float(q.cost)} for q in quotes],
    }


def order_transporter(db: Session, order_id: str) -> str | None:
    return db.scalar(
        select(Vehicle.transporter_id)
        .join(Shipment, Shipment.vehicle_id == Vehicle.id)
        .join(ShipmentStop, ShipmentStop.shipment_id == Shipment.id)
        .where(ShipmentStop.order_id == order_id)
        .limit(1)
    )


def dissolve_pool(db: Session, pool: TransportPool) -> None:
    """Drop a proposed pool and release its orders so they can be pooled again."""
    if pool.status != "PROPOSED":
        raise HTTPException(status_code=409, detail="Only a proposed pool can be dissolved")
    db.execute(update(Order).where(Order.pool_id == pool.id).values(pool_id=None))
    db.execute(delete(TransportPool).where(TransportPool.id == pool.id))
