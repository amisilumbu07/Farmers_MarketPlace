from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..shared.auth import require_role
from ..shared.database import get_db
from ..shared.store import Farm, Lot, new_id

router = APIRouter(tags=["catalog"])


class LotCreate(BaseModel):
    farm_id: str
    product: str
    quantity_kg: float = Field(gt=0)
    price_per_kg: float = Field(gt=0)


class LotUpdate(BaseModel):
    quantity_kg: float | None = Field(default=None, gt=0)
    price_per_kg: float | None = Field(default=None, gt=0)
    active: bool | None = None


def lot_view(lot: Lot) -> dict:
    return {"id": lot.id, "farmer_id": lot.farmer_id, "farm_id": lot.farm_id, "product": lot.product, "quantity_kg": float(lot.quantity_kg), "price_per_kg": float(lot.price_per_kg), "active": lot.active}


@router.post("/lots")
def create_lot(data: LotCreate, user=Depends(require_role("farmer")), db: Session = Depends(get_db)):
    farm = db.get(Farm, data.farm_id)
    if not farm or farm.farmer_id != user.id:
        raise HTTPException(status_code=404, detail="Farm not found")
    lot = Lot(id=new_id("lot"), farmer_id=user.id, farm_id=farm.id, product=data.product, quantity_kg=data.quantity_kg, price_per_kg=data.price_per_kg, active=True)
    db.add(lot)
    return lot_view(lot)


@router.get("/lots")
@router.get("/products")
def list_lots(product: str | None = None, max_price: float | None = None, db: Session = Depends(get_db)):
    query = select(Lot).where(Lot.active.is_(True))
    if product:
        query = query.where(Lot.product.ilike(product))
    if max_price is not None:
        query = query.where(Lot.price_per_kg <= max_price)
    return [lot_view(lot) for lot in db.scalars(query)]


@router.get("/lots/{lot_id}")
def get_lot(lot_id: str, db: Session = Depends(get_db)):
    lot = db.get(Lot, lot_id)
    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")
    return lot_view(lot)


@router.patch("/lots/{lot_id}")
def update_lot(lot_id: str, data: LotUpdate, user=Depends(require_role("farmer")), db: Session = Depends(get_db)):
    lot = db.get(Lot, lot_id)
    if not lot or lot.farmer_id != user.id:
        raise HTTPException(status_code=404, detail="Lot not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(lot, key, value)
    return lot_view(lot)
