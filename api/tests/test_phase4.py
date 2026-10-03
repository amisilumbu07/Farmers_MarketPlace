import base64
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from api.app.logistics.service import confirm_pool, create_pools
from api.app.orders.service import advance, cancel_order, create_order, transition
from api.app.shared.store import Attestation, Dispute, Lot, Order, ReputationEvent, TransportQuote, Vehicle
from api.app.trust.service import EvidenceIn, evidence_from, hash_evidence, open_dispute, record_attestation, reputation, resolve_dispute
from api.tests.test_phase1 import db  # noqa: F401  (fixture)

FARMER_1, FARMER_2, BUYER, TRANSPORTER = "usr_demo_farmer_1", "usr_demo_farmer_2", "usr_demo_buyer", "usr_demo_transporter"


def attestations(session, order_id):
    return [(a.type, a.actor_id) for a in session.scalars(select(Attestation).where(Attestation.subject_id == order_id).order_by(Attestation.created_at, Attestation.id))]


def events(session, user_id):
    return sorted(e.type for e in session.scalars(select(ReputationEvent).where(ReputationEvent.user_id == user_id)))


def deliver_pooled(session, order_id="ord_demo_pool_2"):
    """Pool, confirm with the demo van, then walk one order through the full chain."""
    [pool] = create_pools(session)
    quote = session.scalar(select(TransportQuote).where(TransportQuote.pool_id == pool.id))
    confirm_pool(session, pool.id, quote.id, TRANSPORTER)
    order = session.get(Order, order_id)
    advance(session, order, FARMER_2, "READY_FOR_PICKUP")
    advance(session, order, TRANSPORTER, "IN_TRANSIT")
    advance(session, order, TRANSPORTER, "DELIVERED")
    return order


def test_confirmation_chain_writes_one_attestation_per_step(db):  # noqa: F811
    session, _ = db
    order = deliver_pooled(session)
    advance(session, order, BUYER, "COMPLETED")
    assert attestations(session, order.id) == [("HANDOFF_CONFIRMED", FARMER_2), ("PICKUP_CONFIRMED", TRANSPORTER), ("DELIVERY_CONFIRMED", TRANSPORTER), ("RECEIPT_CONFIRMED", BUYER)]


def test_duplicate_attestation_is_not_recorded_twice(db):  # noqa: F811
    session, _ = db
    first, created = record_attestation(session, "order", "ord_demo_1", FARMER_1, "HANDOFF_CONFIRMED")
    again, created_again = record_attestation(session, "order", "ord_demo_1", FARMER_1, "HANDOFF_CONFIRMED")
    assert created and not created_again and first.id == again.id
    assert len(attestations(session, "ord_demo_1")) == 1


def test_evidence_is_hashed_server_side_and_validated(db):  # noqa: F811
    photo = b"delivery photo bytes"
    assert hash_evidence(b"abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"  # SHA-256 test vector
    stored = evidence_from(EvidenceIn(evidence_url="https://example.com/p.jpg", evidence_b64=base64.b64encode(photo).decode()))
    assert stored == {"url": "https://example.com/p.jpg", "hash": hash_evidence(photo)}
    assert evidence_from(None) is None
    with pytest.raises(HTTPException) as error:
        evidence_from(EvidenceIn(evidence_b64="not base64!!"))
    assert error.value.status_code == 400
    with pytest.raises(ValueError):  # only http(s) URLs are accepted
        EvidenceIn(evidence_url="file:///etc/passwd")

    session, _ = db
    order = session.get(Order, "ord_demo_pool_2")
    advance(session, order, FARMER_2, "READY_FOR_PICKUP", stored)
    attestation = session.scalar(select(Attestation).where(Attestation.subject_id == order.id))
    assert attestation.evidence_hash == hash_evidence(photo)


def test_reputation_events_and_score_projection(db):  # noqa: F811
    session, _ = db
    order = deliver_pooled(session)
    assert events(session, TRANSPORTER) == ["DELIVERY_ON_TIME", "DELIVERY_ON_TIME"]  # one seeded demo delivery + this one
    advance(session, order, BUYER, "COMPLETED")
    assert events(session, FARMER_2) == ["ORDER_COMPLETED", "QUALITY_ACCEPTED"]
    assert events(session, BUYER) == ["ORDER_COMPLETED"]
    assert reputation(session, FARMER_2)["score"] == 53  # 50 + 2 + 1
    assert reputation(session, TRANSPORTER)["points"] == 4  # seeded on-time delivery (+1), this on-time delivery (+1), completed (+2)


def test_late_delivery_is_recorded_against_the_transporter(db):  # noqa: F811
    session, _ = db
    session.get(Order, "ord_demo_pool_2").window_end = datetime.now(timezone.utc) - timedelta(hours=1)
    deliver_pooled(session)
    assert "DELIVERY_LATE" in events(session, TRANSPORTER)


def test_cancel_restores_stock_and_records_event(db):  # noqa: F811
    session, demo = db
    lot = session.get(Lot, "lot_demo_cabbage")
    before = lot.quantity_kg
    order = create_order(session, demo["user_id"], lot.id, lot.quantity_kg)
    assert lot.active is False
    cancel_order(session, order, BUYER)
    assert (order.status, lot.quantity_kg, lot.active) == ("CANCELLED", before, True)
    assert events(session, BUYER) == ["ORDER_CANCELLED"]


def test_cancelling_dissolves_a_proposed_pool_but_not_a_confirmed_one(db):  # noqa: F811
    session, _ = db
    [pool] = create_pools(session)
    cancel_order(session, session.get(Order, "ord_demo_1"), BUYER)
    assert session.get(Order, "ord_demo_pool_2").pool_id is None  # released for re-pooling
    assert create_pools(session) == []  # only one eligible order left

    session.get(Order, "ord_demo_1").status = "ACCEPTED"  # pretend the cancelled order is back
    session.get(Order, "ord_demo_1").pool_id = None
    [pool] = create_pools(session)
    quote = session.scalar(select(TransportQuote).where(TransportQuote.pool_id == pool.id))
    confirm_pool(session, pool.id, quote.id, TRANSPORTER)
    with pytest.raises(HTTPException) as error:
        cancel_order(session, session.get(Order, "ord_demo_1"), BUYER)
    assert error.value.status_code == 409


def test_dispute_refund_and_complete_outcomes(db):  # noqa: F811
    session, _ = db
    delivered = session.get(Order, "ord_demo_delivered")
    with pytest.raises(HTTPException) as error:
        open_dispute(session, delivered, "someone_else", "bad tomatoes")
    assert error.value.status_code == 403
    dispute = open_dispute(session, delivered, BUYER, "bruised onions")
    assert delivered.status == "DISPUTED" and dispute.status == "OPEN"
    with pytest.raises(HTTPException):
        open_dispute(session, delivered, BUYER, "again")  # already DISPUTED
    resolve_dispute(session, dispute, "refund")
    assert (delivered.status, dispute.resolution) == ("REFUNDED", "refund")
    assert "QUALITY_REJECTED" in events(session, FARMER_1)
    with pytest.raises(HTTPException) as error:
        resolve_dispute(session, dispute, "complete")
    assert error.value.status_code == 409

    order = deliver_pooled(session)
    dispute = open_dispute(session, order, FARMER_2, "buyer unreachable")
    resolve_dispute(session, dispute, "complete")
    assert order.status == "COMPLETED"
    assert "ORDER_COMPLETED" in events(session, BUYER)
