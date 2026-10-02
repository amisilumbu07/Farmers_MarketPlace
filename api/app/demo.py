import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Literal

from .shared.database import get_db
from .shared.demo import seed_demo_data

router = APIRouter(prefix="/demo", tags=["demo"])


@router.post("/seed")
def seed(role: Literal["buyer", "farmer", "admin"] = "buyer", db: Session = Depends(get_db)):
    if os.getenv("ENABLE_DEMO_SEED", "1") != "1":
        raise HTTPException(status_code=404, detail="Demo seeding is disabled")
    data = seed_demo_data(db)
    if role == "farmer":
        return data["farmer_session"]
    if role == "admin":
        return data["admin_session"]
    return data
