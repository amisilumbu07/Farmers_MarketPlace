from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..shared.auth import require_role
from ..shared.database import get_db
from ..shared.store import ExternalTransaction
from .service import retry_failed

router = APIRouter(prefix="/admin/payments", tags=["payments"], dependencies=[Depends(require_role("admin"))])


def view(t: ExternalTransaction) -> dict:
    return {"id": t.id, "order_id": t.order_id, "provider": t.provider, "purpose": t.purpose, "external_id": t.external_id, "amount": t.amount, "currency": t.currency, "status": t.status, "error": (t.metadata_json or {}).get("error"), "created_at": t.created_at}


@router.get("")
def list_payments(status: str | None = None, db: Session = Depends(get_db)):
    query = select(ExternalTransaction).order_by(ExternalTransaction.created_at.desc())
    return [view(t) for t in db.scalars(query.where(ExternalTransaction.status == status) if status else query)]


@router.post("/retry")
def retry(db: Session = Depends(get_db)):
    return [view(t) for t in retry_failed(db)]
