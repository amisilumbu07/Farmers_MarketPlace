from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..logistics.service import dissolve_pool
from ..matching.engine import MatchingEngine, save_match_plan
from ..shared.events import publish
from ..shared.store import BuyerRequest, Lot, Order, TransportPool, new_id

VALID_TRANSITIONS = {
    "PENDING": {"ACCEPTED", "CANCELLED"},
    "ACCEPTED": {"READY_FOR_PICKUP", "CANCELLED"},
    "READY_FOR_PICKUP": {"IN_TRANSIT", "CANCELLED"},
    "IN_TRANSIT": {"DELIVERED", "DISPUTED"},
    "DELIVERED": {"COMPLETED", "DISPUTED"},
    "DISPUTED": {"COMPLETED", "REFUNDED"},
    "COMPLETED": set(),
    "CANCELLED": set(),
    "REFUNDED": set(),
}


def transition(order: Order, status: str) -> Order:
    if status not in VALID_TRANSITIONS.get(order.status, set()):
        raise HTTPException(status_code=409, detail=f"Cannot move {order.status} to {status}")
    order.status = status
    return order


def advance(db: Session, order: Order, actor_id: str, status: str, evidence: dict | None = None) -> Order:
    """Validated transition plus the 'order.status_changed' event (attestations and reputation listen to it)."""
    transition(order, status)
    publish("order.status_changed", db, order=order, actor_id=actor_id, status=status, evidence=evidence)
    return order


def cancel_order(db: Session, order: Order, actor_id: str) -> Order:
    if order.pool_id:
        pool = db.get(TransportPool, order.pool_id)
        if pool.status != "PROPOSED":
            raise HTTPException(status_code=409, detail="Order is on a confirmed shipment and cannot be cancelled")
        dissolve_pool(db, pool)  # release the other orders so they can be pooled again
    lot = db.scalar(select(Lot).where(Lot.id == order.lot_id).with_for_update())
    advance(db, order, actor_id, "CANCELLED")
    if lot.quantity_kg == 0:
        lot.active = True
    lot.quantity_kg += order.quantity_kg
    return order


def create_order(db: Session, buyer_id: str, lot_id: str, quantity_kg: float, request: BuyerRequest | None = None, group_id: str | None = None) -> Order:
    lot = db.scalar(select(Lot).where(Lot.id == lot_id).with_for_update())
    quantity = Decimal(str(quantity_kg))
    if not lot or not lot.active:
        raise HTTPException(status_code=404, detail="Lot not found")
    if quantity > lot.quantity_kg:
        raise HTTPException(status_code=400, detail="Requested quantity exceeds availability")
    order = Order(id=new_id("ord"), buyer_id=buyer_id, lot_id=lot_id, quantity_kg=quantity, status="PENDING", group_id=group_id)
    if request:
        order.request_id, order.dest_latitude, order.dest_longitude = request.id, request.latitude, request.longitude
        order.window_start, order.window_end = request.window_start, request.window_end
    db.add(order)
    lot.quantity_kg -= quantity
    if lot.quantity_kg == 0:
        lot.active = False
    return order


def create_grouped_orders(db: Session, request_id: str, buyer_id: str) -> dict:
    request = db.scalar(select(BuyerRequest).where(BuyerRequest.id == request_id).with_for_update())
    if not request or request.buyer_id != buyer_id:
        raise HTTPException(status_code=404, detail="Buyer request not found")
    if request.status != "OPEN":
        raise HTTPException(status_code=409, detail="Buyer request already ordered")

    plan = MatchingEngine().match(db, request, lock_lots=True)
    save_match_plan(db, plan)
    if not plan.complete:
        raise HTTPException(status_code=409, detail="Not enough eligible supply to fill this request")

    group_id = new_id("grp")
    orders = [create_order(db, buyer_id, allocation.lot_id, allocation.quantity_kg, request, group_id) for allocation in plan.allocations]
    request.status = "ORDERED"
    return {"group_id": group_id, "request_id": request.id, "orders": orders, "plan": plan}
