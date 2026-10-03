from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..shared.auth import require_role
from ..shared.database import get_db
from ..shared.store import TransportPool, Vehicle, new_id
from fastapi import HTTPException

from .service import confirm_pool, create_pools, dissolve_pool, pool_view

router = APIRouter(tags=["logistics"])


class VehicleCreate(BaseModel):
    capacity_kg: float = Field(gt=0)
    base_fee: float = Field(ge=0)
    cost_per_km: float = Field(ge=0)


class Confirm(BaseModel):
    quote_id: str


def vehicle_view(vehicle: Vehicle) -> dict:
    return {"id": vehicle.id, "transporter_id": vehicle.transporter_id, "capacity_kg": float(vehicle.capacity_kg), "base_fee": float(vehicle.base_fee), "cost_per_km": float(vehicle.cost_per_km), "active": vehicle.active}


@router.post("/vehicles")
def create_vehicle(data: VehicleCreate, user=Depends(require_role("transporter")), db: Session = Depends(get_db)):
    vehicle = Vehicle(id=new_id("veh"), transporter_id=user.id, **data.model_dump())
    db.add(vehicle)
    return vehicle_view(vehicle)


@router.get("/vehicles")
def list_vehicles(user=Depends(require_role("transporter", "admin")), db: Session = Depends(get_db)):
    query = select(Vehicle)
    if user.role == "transporter":
        query = query.where(Vehicle.transporter_id == user.id)
    return [vehicle_view(vehicle) for vehicle in db.scalars(query)]


@router.post("/transport-pools/propose")
def propose(user=Depends(require_role("transporter", "admin")), db: Session = Depends(get_db)):
    return [pool_view(db, pool) for pool in create_pools(db)]


@router.get("/transport-pools")
def list_pools(user=Depends(require_role("transporter", "admin")), db: Session = Depends(get_db)):
    return [pool_view(db, pool) for pool in db.scalars(select(TransportPool).order_by(TransportPool.created_at.desc()))]


@router.post("/transport-pools/{pool_id}/confirm")
def confirm(pool_id: str, data: Confirm, user=Depends(require_role("transporter")), db: Session = Depends(get_db)):
    return pool_view(db, confirm_pool(db, pool_id, data.quote_id, user.id))


@router.post("/transport-pools/{pool_id}/dissolve")
def dissolve(pool_id: str, user=Depends(require_role("transporter", "admin")), db: Session = Depends(get_db)):
    pool = db.get(TransportPool, pool_id)
    if not pool:
        raise HTTPException(status_code=404, detail="Pool not found")
    dissolve_pool(db, pool)
    return {"id": pool_id, "dissolved": True}
