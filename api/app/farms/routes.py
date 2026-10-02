from fastapi import APIRouter, Depends
from geoalchemy2.elements import WKTElement
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..shared.auth import require_role
from ..shared.database import get_db
from ..shared.store import Farm, new_id

router = APIRouter(tags=["farms"])


class FarmCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


def farm_view(farm: Farm) -> dict:
    return {"id": farm.id, "farmer_id": farm.farmer_id, "name": farm.name, "latitude": farm.latitude, "longitude": farm.longitude}


@router.post("/farms")
def create_farm(data: FarmCreate, user=Depends(require_role("farmer")), db: Session = Depends(get_db)):
    farm = Farm(id=new_id("farm"), farmer_id=user.id, name=data.name, latitude=data.latitude, longitude=data.longitude, location=WKTElement(f"POINT({data.longitude} {data.latitude})", srid=4326))
    db.add(farm)
    return farm_view(farm)


@router.get("/farms")
def list_farms(user=Depends(require_role("farmer")), db: Session = Depends(get_db)):
    return [farm_view(farm) for farm in db.scalars(select(Farm).where(Farm.farmer_id == user.id))]
