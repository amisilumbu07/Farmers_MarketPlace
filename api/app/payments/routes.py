import os

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..shared.auth import require_role
from ..shared.database import get_db
from ..shared.store import ExternalTransaction
from .service import process_queue

router = APIRouter(prefix="/admin/payments", tags=["payments"], dependencies=[Depends(require_role("admin"))])


def view(t: ExternalTransaction) -> dict:
    return {"id": t.id, "order_id": t.order_id, "provider": t.provider, "purpose": t.purpose, "external_id": t.external_id, "amount": t.amount, "currency": t.currency, "status": t.status, "error": (t.metadata_json or {}).get("error"), "created_at": t.created_at}


@router.get("")
def list_payments(status: str | None = None, db: Session = Depends(get_db)):
    query = select(ExternalTransaction).order_by(ExternalTransaction.created_at.desc())
    return [view(t) for t in db.scalars(query.where(ExternalTransaction.status == status) if status else query)]


@router.post("/retry")
def retry(db: Session = Depends(get_db)):
    return [view(t) for t in process_queue(db)]


cron = APIRouter(prefix="/payments", tags=["payments"])


@cron.get("/cron")
def run_queue(authorization: str | None = Header(None), db: Session = Depends(get_db)):
    """Called by a scheduler (Vercel Cron sends `Authorization: Bearer $CRON_SECRET`). Disabled until CRON_SECRET is set."""
    secret = os.getenv("CRON_SECRET")
    if not secret or authorization != f"Bearer {secret}":
        raise HTTPException(status_code=401, detail="Invalid cron secret")
    return {"processed": len(process_queue(db))}
