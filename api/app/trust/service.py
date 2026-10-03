import base64
import binascii
import hashlib
from datetime import datetime, timezone

from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..logistics.service import order_transporter
from ..shared.events import publish, subscribe
from ..shared.store import Attestation, Dispute, Lot, Order, ReputationEvent, new_id

ATTESTATION_FOR = {"READY_FOR_PICKUP": "HANDOFF_CONFIRMED", "IN_TRANSIT": "PICKUP_CONFIRMED", "DELIVERED": "DELIVERY_CONFIRMED", "COMPLETED": "RECEIPT_CONFIRMED"}
# Points per reputation event. The score is a projection of the events, so changing these never loses history.
WEIGHTS = {"ORDER_COMPLETED": 2, "DELIVERY_ON_TIME": 1, "DELIVERY_LATE": -2, "QUALITY_ACCEPTED": 1, "QUALITY_REJECTED": -3, "DISPUTE_OPENED": 0, "DISPUTE_RESOLVED": 0, "ORDER_CANCELLED": -1}
BASE_SCORE = 50  # ponytail: neutral start + summed points, clamped 0-100; weight by recency/volume when real data exists
MAX_EVIDENCE_B64 = 2_800_000  # ~2 MB of file content


class EvidenceIn(BaseModel):
    evidence_url: str | None = Field(default=None, max_length=500, pattern=r"^https?://")
    evidence_b64: str | None = None  # file content; only its SHA-256 is stored, never the bytes


def hash_evidence(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def evidence_from(body: EvidenceIn | None) -> dict | None:
    if body is None or not (body.evidence_url or body.evidence_b64):
        return None
    digest = None
    if body.evidence_b64:
        if len(body.evidence_b64) > MAX_EVIDENCE_B64:
            raise HTTPException(status_code=413, detail="Evidence file too large")
        try:
            digest = hash_evidence(base64.b64decode(body.evidence_b64, validate=True))
        except binascii.Error as error:
            raise HTTPException(status_code=400, detail="evidence_b64 is not valid base64") from error
    return {"url": body.evidence_url, "hash": digest}


def record_attestation(db: Session, subject_type: str, subject_id: str, actor_id: str, type: str, evidence: dict | None = None) -> tuple[Attestation, bool]:
    """Returns (attestation, created). The same statement about the same subject is recorded once."""
    existing = db.scalar(select(Attestation).where(Attestation.subject_type == subject_type, Attestation.subject_id == subject_id, Attestation.type == type))
    if existing:
        return existing, False
    evidence = evidence or {}
    attestation = Attestation(id=new_id("att"), subject_type=subject_type, subject_id=subject_id, actor_id=actor_id, type=type, evidence_url=evidence.get("url"), evidence_hash=evidence.get("hash"), created_at=datetime.now(timezone.utc))
    db.add(attestation)
    db.flush()
    return attestation, True


def add_event(db: Session, user_id: str, type: str, order_id: str) -> None:
    WEIGHTS[type]  # a typo fails loudly instead of silently scoring zero
    if not db.scalar(select(ReputationEvent.id).where(ReputationEvent.user_id == user_id, ReputationEvent.type == type, ReputationEvent.order_id == order_id)):
        db.add(ReputationEvent(user_id=user_id, type=type, order_id=order_id))


def reputation(db: Session, user_id: str) -> dict:
    counts = dict(db.execute(select(ReputationEvent.type, func.count()).where(ReputationEvent.user_id == user_id).group_by(ReputationEvent.type)).all())
    points = sum(WEIGHTS[t] * n for t, n in counts.items())
    return {"user_id": user_id, "score": max(0, min(100, BASE_SCORE + points)), "points": points, "events": counts}


def _parties(db: Session, order: Order) -> tuple[str, set[str]]:
    farmer_id = db.get(Lot, order.lot_id).farmer_id
    return farmer_id, {order.buyer_id, farmer_id, order_transporter(db, order.id)} - {None}


@subscribe("order.status_changed")
def on_status_changed(db: Session, order: Order, actor_id: str, status: str, evidence: dict | None = None) -> None:
    if status in ATTESTATION_FOR:
        record_attestation(db, "order", order.id, actor_id, ATTESTATION_FOR[status], evidence)
    if status == "DELIVERED":
        late = order.window_end is not None and datetime.now(timezone.utc) > order.window_end
        add_event(db, actor_id, "DELIVERY_LATE" if late else "DELIVERY_ON_TIME", order.id)
    elif status == "COMPLETED":
        farmer_id, parties = _parties(db, order)
        for user_id in parties:
            add_event(db, user_id, "ORDER_COMPLETED", order.id)
        add_event(db, farmer_id, "QUALITY_ACCEPTED", order.id)
    elif status == "CANCELLED":
        add_event(db, actor_id, "ORDER_CANCELLED", order.id)


@subscribe("dispute.opened")
def on_dispute_opened(db: Session, order: Order, dispute: Dispute) -> None:
    for user_id in (order.buyer_id, db.get(Lot, order.lot_id).farmer_id):
        add_event(db, user_id, "DISPUTE_OPENED", order.id)


@subscribe("dispute.resolved")
def on_dispute_resolved(db: Session, order: Order, dispute: Dispute) -> None:
    farmer_id, parties = _parties(db, order)
    for user_id in (order.buyer_id, farmer_id):
        add_event(db, user_id, "DISPUTE_RESOLVED", order.id)
    if dispute.resolution == "refund":
        add_event(db, farmer_id, "QUALITY_REJECTED", order.id)
    else:
        for user_id in parties:
            add_event(db, user_id, "ORDER_COMPLETED", order.id)


def open_dispute(db: Session, order: Order, user_id: str, reason: str) -> Dispute:
    from ..orders.service import transition  # local import: orders.service publishes events, trust handles them

    if user_id not in {order.buyer_id, db.get(Lot, order.lot_id).farmer_id}:
        raise HTTPException(status_code=403, detail="Only the buyer or the farmer can dispute this order")
    transition(order, "DISPUTED")  # only IN_TRANSIT or DELIVERED orders can be disputed
    dispute = Dispute(id=new_id("dsp"), order_id=order.id, opened_by=user_id, reason=reason, status="OPEN")
    db.add(dispute)
    db.flush()
    publish("dispute.opened", db, order=order, dispute=dispute)
    return dispute


def resolve_dispute(db: Session, dispute: Dispute, outcome: str) -> Dispute:
    from ..orders.service import transition

    if dispute.status != "OPEN":
        raise HTTPException(status_code=409, detail="Dispute already resolved")
    order = db.get(Order, dispute.order_id)
    transition(order, "REFUNDED" if outcome == "refund" else "COMPLETED")
    dispute.status, dispute.resolution, dispute.resolved_at = "RESOLVED", outcome, datetime.now(timezone.utc)
    publish("dispute.resolved", db, order=order, dispute=dispute)
    return dispute
