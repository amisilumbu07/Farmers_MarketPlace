import pytest
from fastapi import HTTPException
from sqlalchemy import func, select

from api.app.matching.engine import MatchingEngine
from api.app.orders.service import create_grouped_orders, create_order, transition
from api.app.shared.database import SessionLocal
from api.app.shared.demo import seed_demo_data
from api.app.shared.store import BuyerRequest, Lot, Order, User


@pytest.fixture
def db():
    with SessionLocal() as session:
        demo = seed_demo_data(session)
        session.flush()
        yield session, demo
        session.rollback()


def test_marketplace_flow(db):
    session, demo = db
    lot = session.get(Lot, "lot_demo_tomatoes_sunrise")
    order = create_order(session, demo["user_id"], lot.id, 50)
    assert transition(order, "ACCEPTED").status == "ACCEPTED"
    assert transition(order, "COMPLETED").status == "COMPLETED"
    assert lot.active is False


def test_demo_seed_is_persisted(db):
    session, demo = db
    session.commit()
    with SessionLocal() as other_session:
        assert other_session.scalar(select(func.count()).select_from(User)) == 4
        assert other_session.get(Order, demo["order_id"]).status == "ACCEPTED"
        assert other_session.get(BuyerRequest, demo["request_id"]).status == "OPEN"


def test_matching_uses_radius_and_aggregates(db):
    session, demo = db
    request = session.get(BuyerRequest, demo["request_id"])
    plan = MatchingEngine().match(session, request)
    assert plan.complete is True
    assert plan.allocated_quantity_kg == 100
    assert len(plan.allocations) == 2
    assert all(0 <= allocation.score <= 1 for allocation in plan.allocations)
    request.radius_km = .1
    assert MatchingEngine().match(session, request).allocations == []


def test_complete_match_creates_grouped_orders_once(db):
    session, demo = db
    result = create_grouped_orders(session, demo["request_id"], demo["user_id"])
    assert len(result["orders"]) == 2
    assert sum(order.quantity_kg for order in result["orders"]) == 100
    assert len({order.group_id for order in result["orders"]}) == 1
    assert session.get(BuyerRequest, demo["request_id"]).status == "ORDERED"
    with pytest.raises(HTTPException) as error:
        create_grouped_orders(session, demo["request_id"], demo["user_id"])
    assert error.value.status_code == 409
