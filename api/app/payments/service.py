"""Listens to order events and mirrors them to the configured provider. Chain trouble never blocks the marketplace:
a failed call is stored as FAILED and replayed by process_queue()."""
import hashlib
import os

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..shared.events import subscribe
from ..shared.store import Attestation, ExternalTransaction, Lot, Order, new_id
from ..trust import service as _trust  # noqa: F401  (registers its handlers first, so the attestation row exists when we run)
from ..trust.service import ATTESTATION_FOR
from .base import MockPaymentProvider, PaymentProvider

_provider: PaymentProvider | None = None


def get_provider() -> PaymentProvider:
    global _provider
    if _provider is None:
        if os.getenv("PAYMENT_PROVIDER", "mock") == "solana":
            from .solana_adapter import SolanaPaymentProvider  # imported lazily: solders is only needed on this path

            _provider = SolanaPaymentProvider.from_env(os.environ)
        else:
            _provider = MockPaymentProvider()
    return _provider


def attestation_hash(a: Attestation) -> bytes:
    return hashlib.sha256(f"{a.subject_id}|{a.type}|{a.actor_id}|{a.evidence_hash or ''}".encode()).digest()


def execute(row: ExternalTransaction) -> ExternalTransaction:
    provider, meta = get_provider(), row.metadata_json
    try:
        if row.purpose == "order":
            row.external_id = provider.create_payment(row.order_id, row.amount)
        elif row.purpose == "attestation":
            row.external_id = provider.attest(row.order_id, bytes.fromhex(meta["hash"]), meta.get("seq"))
        else:
            row.external_id = (provider.capture if meta["outcome"] == "capture" else provider.refund)(row.order_id)
        row.status, row.metadata_json = "CONFIRMED", {**meta, "error": None}
    except Exception as error:  # noqa: BLE001  (any provider failure is recorded, never raised into the order flow)
        row.status, row.metadata_json = "FAILED", {**meta, "error": str(error)[:300]}
    return row


def enqueue(db: Session, order_id: str, purpose: str, key: str, amount: int = 0, **meta) -> ExternalTransaction:
    """Idempotent: the same key is executed once (until it fails, then process_queue picks it up)."""
    key = f"{order_id}:{key}"
    row = db.scalar(select(ExternalTransaction).where(ExternalTransaction.idempotency_key == key))
    if row:
        return row
    row = ExternalTransaction(id=new_id("ext"), idempotency_key=key, provider=get_provider().name, order_id=order_id, purpose=purpose, amount=amount, metadata_json=meta)
    db.add(row)
    # the mock provider is instant, so it runs inline; a real chain stays PENDING until process_queue() (cron) sends it
    return execute(row) if get_provider().name == "mock" else row


def _committed(db: Session, order_id: str) -> bool:
    return db.scalar(select(ExternalTransaction.id).where(ExternalTransaction.idempotency_key == f"{order_id}:commit")) is not None


def settle(db: Session, order_id: str, outcome: str) -> None:
    if _committed(db, order_id):  # orders that never reached the chain have nothing to settle
        enqueue(db, order_id, "settlement", "settle", outcome=outcome)


PURPOSE_RANK = {"order": 0, "attestation": 1, "settlement": 2}


def process_queue(db: Session) -> list[ExternalTransaction]:
    """Sends every PENDING or FAILED row. Rows of one request share a timestamp, so ties break commit, attest (by seq), settle.
    Safe to run twice at once: rows are locked, and the chain adapter ignores a step that already landed."""
    rows = db.scalars(select(ExternalTransaction).where(ExternalTransaction.status.in_(("PENDING", "FAILED"))).with_for_update(skip_locked=True)).all()
    rows.sort(key=lambda r: (r.created_at, PURPOSE_RANK[r.purpose], r.metadata_json.get("seq") or 0))
    return [execute(row) for row in rows]  # ponytail: one batch per cron tick; a failed commit makes later rows of that order fail and replay in order next tick


@subscribe("order.status_changed")
def on_status_changed(db: Session, order: Order, actor_id: str, status: str, evidence: dict | None = None) -> None:
    if status == "ACCEPTED":
        lot = db.get(Lot, order.lot_id)
        enqueue(db, order.id, "order", "commit", amount=int(order.quantity_kg * lot.price_per_kg * 100))
    elif status in ATTESTATION_FOR:
        a = db.scalar(select(Attestation).where(Attestation.subject_type == "order", Attestation.subject_id == order.id, Attestation.type == ATTESTATION_FOR[status]))
        if a and _committed(db, order.id):
            seq = db.scalar(select(func.count()).select_from(ExternalTransaction).where(ExternalTransaction.order_id == order.id, ExternalTransaction.purpose == "attestation"))
            enqueue(db, order.id, "attestation", f"attest:{a.type}", hash=attestation_hash(a).hex(), seq=seq)  # ponytail: position = rows queued so far; only this service writes the chain
    if status == "COMPLETED":
        settle(db, order.id, "capture")
    elif status == "CANCELLED":
        settle(db, order.id, "refund")


@subscribe("dispute.resolved")
def on_dispute_resolved(db: Session, order: Order, dispute) -> None:
    settle(db, order.id, "refund" if dispute.resolution == "refund" else "capture")
