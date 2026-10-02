from fastapi import APIRouter, Depends, HTTPException
from geoalchemy2.elements import WKTElement
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..matching.engine import MatchingEngine, save_match_plan
from ..shared.auth import current_user, require_role
from ..shared.database import get_db
from ..shared.store import BuyerRequest, Lot, Order, new_id
from .service import create_grouped_orders, create_order, transition

router = APIRouter(tags=["orders"])


class OrderCreate(BaseModel):
    lot_id: str
    quantity_kg: float = Field(gt=0)


class BuyerRequestCreate(BaseModel):
    product: str = Field(min_length=1, max_length=100)
    quantity_kg: float = Field(gt=0)
    max_price_per_kg: float | None = Field(default=None, gt=0)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    radius_km: float = Field(default=50, gt=0, le=500)


def order_view(order: Order) -> dict:
    return {"id": order.id, "buyer_id": order.buyer_id, "lot_id": order.lot_id, "quantity_kg": float(order.quantity_kg), "status": order.status, "request_id": order.request_id, "group_id": order.group_id}


def request_view(request: BuyerRequest) -> dict:
    return {"id": request.id, "buyer_id": request.buyer_id, "product": request.product, "quantity_kg": float(request.quantity_kg), "max_price_per_kg": float(request.max_price_per_kg) if request.max_price_per_kg is not None else None, "latitude": request.latitude, "longitude": request.longitude, "radius_km": request.radius_km, "status": request.status}


@router.post("/buyer-requests")
def create_buyer_request(data: BuyerRequestCreate, user=Depends(require_role("buyer")), db: Session = Depends(get_db)):
    location = WKTElement(f"POINT({data.longitude} {data.latitude})", srid=4326) if data.latitude is not None and data.longitude is not None else None
    request = BuyerRequest(id=new_id("req"), buyer_id=user.id, product=data.product, quantity_kg=data.quantity_kg, max_price_per_kg=data.max_price_per_kg, latitude=data.latitude, longitude=data.longitude, location=location, radius_km=data.radius_km, status="OPEN")
    db.add(request)
    return request_view(request)


@router.get("/buyer-requests")
def list_buyer_requests(user=Depends(current_user), db: Session = Depends(get_db)):
    query = select(BuyerRequest)
    if user.role == "buyer":
        query = query.where(BuyerRequest.buyer_id == user.id)
    return [request_view(request) for request in db.scalars(query)]


@router.get("/buyer-requests/{request_id}/matches")
def match_buyer_request(request_id: str, user=Depends(current_user), db: Session = Depends(get_db)):
    request = db.get(BuyerRequest, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Buyer request not found")
    if user.role == "buyer" and request.buyer_id != user.id:
        raise HTTPException(status_code=403, detail="Request access denied")
    try:
        plan = MatchingEngine().match(db, request)
        save_match_plan(db, plan)
        return plan
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/buyer-requests/{request_id}/orders")
def finalize_buyer_request(request_id: str, user=Depends(require_role("buyer")), db: Session = Depends(get_db)):
    result = create_grouped_orders(db, request_id, user.id)
    return {**result, "orders": [order_view(order) for order in result["orders"]]}


@router.post("/orders")
def create_buyer_order(data: OrderCreate, user=Depends(require_role("buyer")), db: Session = Depends(get_db)):
    return order_view(create_order(db, user.id, data.lot_id, data.quantity_kg))


@router.get("/orders")
def list_orders(user=Depends(current_user), db: Session = Depends(get_db)):
    query = select(Order)
    if user.role == "buyer":
        query = query.where(Order.buyer_id == user.id)
    elif user.role == "farmer":
        query = query.join(Lot, Lot.id == Order.lot_id).where(Lot.farmer_id == user.id)
    return [order_view(order) for order in db.scalars(query)]


def get_order_or_404(db: Session, order_id: str) -> Order:
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.get("/orders/{order_id}")
def get_order(order_id: str, user=Depends(current_user), db: Session = Depends(get_db)):
    order = get_order_or_404(db, order_id)
    lot = db.get(Lot, order.lot_id)
    if user.role != "admin" and user.id not in {order.buyer_id, lot.farmer_id}:
        raise HTTPException(status_code=403, detail="Order access denied")
    return order_view(order)


@router.post("/orders/{order_id}/accept")
def accept_order(order_id: str, user=Depends(require_role("farmer")), db: Session = Depends(get_db)):
    order = get_order_or_404(db, order_id)
    if db.get(Lot, order.lot_id).farmer_id != user.id:
        raise HTTPException(status_code=403, detail="Only the farmer can accept this order")
    return order_view(transition(order, "ACCEPTED"))


@router.post("/orders/{order_id}/complete")
def complete_order(order_id: str, user=Depends(require_role("buyer")), db: Session = Depends(get_db)):
    order = get_order_or_404(db, order_id)
    if order.buyer_id != user.id:
        raise HTTPException(status_code=403, detail="Only the buyer can complete this order")
    return order_view(transition(order, "COMPLETED"))
