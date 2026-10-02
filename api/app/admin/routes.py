from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..catalog.routes import lot_view
from ..orders.routes import order_view
from ..shared.auth import require_role
from ..shared.database import get_db
from ..shared.store import Lot, Order, User

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_role("admin"))])


class ActiveUpdate(BaseModel):
    active: bool


@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    return [{"id": user.id, "email": user.email, "role": user.role, "active": user.active} for user in db.scalars(select(User))]


@router.patch("/users/{user_id}")
def moderate_user(user_id: str, data: ActiveUpdate, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role == "admin" and not data.active:
        raise HTTPException(status_code=400, detail="Admin accounts cannot be disabled here")
    user.active = data.active
    return {"id": user.id, "email": user.email, "role": user.role, "active": user.active}


@router.get("/lots")
def list_lots(db: Session = Depends(get_db)):
    return [lot_view(lot) for lot in db.scalars(select(Lot))]


@router.patch("/lots/{lot_id}")
def moderate_lot(lot_id: str, data: ActiveUpdate, db: Session = Depends(get_db)):
    lot = db.get(Lot, lot_id)
    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")
    lot.active = data.active
    return lot_view(lot)


@router.get("/orders")
def list_orders(db: Session = Depends(get_db)):
    return [order_view(order) for order in db.scalars(select(Order))]
