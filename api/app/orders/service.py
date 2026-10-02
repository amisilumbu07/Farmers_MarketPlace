from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..matching.engine import MatchingEngine, save_match_plan
from ..shared.store import BuyerRequest, Lot, Order, new_id

VALID_TRANSITIONS = {
    "PENDING": {"ACCEPTED", "CANCELLED"},
    "ACCEPTED": {"COMPLETED", "CANCELLED"},
    "COMPLETED": set(),
    "CANCELLED": set(),
}


def transition(order: Order, status: str) -> Order:
    if status not in VALID_TRANSITIONS.get(order.status, set()):
        raise HTTPException(status_code=409, detail=f"Cannot move {order.status} to {status}")
    order.status = status
    return order


def create_order(db: Session, buyer_id: str, lot_id: str, quantity_kg: float, request_id: str | None = None, group_id: str | None = None) -> Order:
    lot = db.scalar(select(Lot).where(Lot.id == lot_id).with_for_update())
    quantity = Decimal(str(quantity_kg))
    if not lot or not lot.active:
        raise HTTPException(status_code=404, detail="Lot not found")
    if quantity > lot.quantity_kg:
        raise HTTPException(status_code=400, detail="Requested quantity exceeds availability")
    order = Order(id=new_id("ord"), buyer_id=buyer_id, lot_id=lot_id, quantity_kg=quantity, status="PENDING", request_id=request_id, group_id=group_id)
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
    orders = [create_order(db, buyer_id, allocation.lot_id, allocation.quantity_kg, request.id, group_id) for allocation in plan.allocations]
    request.status = "ORDERED"
    return {"group_id": group_id, "request_id": request.id, "orders": orders, "plan": plan}
