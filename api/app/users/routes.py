from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..shared.auth import require_role
from ..shared.database import get_db
from ..shared.store import FarmerProfile

router = APIRouter(tags=["users"])


class FarmerProfileCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=30)


@router.post("/farmer-profile")
def create_farmer_profile(data: FarmerProfileCreate, user=Depends(require_role("farmer")), db: Session = Depends(get_db)):
    if db.get(FarmerProfile, user.id):
        raise HTTPException(status_code=409, detail="Farmer profile already exists")
    profile = FarmerProfile(user_id=user.id, display_name=data.display_name, phone=data.phone)
    db.add(profile)
    return {"user_id": profile.user_id, "display_name": profile.display_name, "phone": profile.phone}


@router.get("/farmer-profile/{farmer_id}")
def get_farmer_profile(farmer_id: str, db: Session = Depends(get_db)):
    profile = db.get(FarmerProfile, farmer_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Farmer profile not found")
    return {"user_id": profile.user_id, "display_name": profile.display_name, "phone": profile.phone}
