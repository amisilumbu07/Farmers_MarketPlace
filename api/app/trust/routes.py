from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..logistics.service import transporter_has_order
from ..shared.auth import current_user, require_role
from ..shared.database import get_db
from ..shared.store import Attestation, Dispute, Lot, Order, User
from .service import open_dispute, reputation, resolve_dispute

router = APIRouter(tags=["trust"])


class DisputeCreate(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class DisputeResolve(BaseModel):
    outcome: Literal["refund", "complete"]


def attestation_view(a: Attestation) -> dict:
    return {"id": a.id, "type": a.type, "actor_id": a.actor_id, "subject_type": a.subject_type, "subject_id": a.subject_id, "evidence_url": a.evidence_url, "evidence_hash": a.evidence_hash, "created_at": a.created_at}


def dispute_view(d: Dispute) -> dict:
    return {"id": d.id, "order_id": d.order_id, "opened_by": d.opened_by, "reason": d.reason, "status": d.status, "resolution": d.resolution, "created_at": d.created_at, "resolved_at": d.resolved_at}


def order_or_404(db: Session, order_id: str) -> Order:
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.get("/orders/{order_id}/history")
def order_history(order_id: str, user=Depends(current_user), db: Session = Depends(get_db)):
    order = order_or_404(db, order_id)
    allowed = user.role == "admin" or user.id in {order.buyer_id, db.get(Lot, order.lot_id).farmer_id} or transporter_has_order(db, order_id, user.id)
    if not allowed:
        raise HTTPException(status_code=403, detail="Order access denied")
    attestations = db.scalars(select(Attestation).where(Attestation.subject_type == "order", Attestation.subject_id == order_id).order_by(Attestation.created_at, Attestation.id))
    dispute = db.scalar(select(Dispute).where(Dispute.order_id == order_id))
    return {"order_id": order_id, "status": order.status, "attestations": [attestation_view(a) for a in attestations], "dispute": dispute_view(dispute) if dispute else None}


@router.get("/users/{user_id}/reputation")
def user_reputation(user_id: str, user=Depends(current_user), db: Session = Depends(get_db)):
    if not db.get(User, user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return reputation(db, user_id)


@router.post("/orders/{order_id}/dispute")
def dispute_order(order_id: str, data: DisputeCreate, user=Depends(require_role("buyer", "farmer")), db: Session = Depends(get_db)):
    return dispute_view(open_dispute(db, order_or_404(db, order_id), user.id, data.reason))


@router.get("/disputes")
def list_disputes(user=Depends(require_role("admin")), db: Session = Depends(get_db)):
    return [dispute_view(d) for d in db.scalars(select(Dispute).order_by(Dispute.created_at.desc()))]


@router.post("/disputes/{dispute_id}/resolve")
def resolve(dispute_id: str, data: DisputeResolve, user=Depends(require_role("admin")), db: Session = Depends(get_db)):
    dispute = db.get(Dispute, dispute_id)
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    return dispute_view(resolve_dispute(db, dispute, data.outcome))
