from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from api.app.logistics.pooling import PoolOrder, delivery_cost, propose_pools
from api.app.logistics.routing import FallbackRoutingProvider, MockRoutingProvider
from api.app.logistics.service import confirm_pool, create_pools, transporter_has_order
from api.app.orders.service import transition
from api.app.shared.store import Order, TransportQuote, Vehicle
from api.tests.test_phase1 import db  # noqa: F401  (fixture)

MOCK = MockRoutingProvider()
NOW = datetime(2026, 10, 10, tzinfo=timezone.utc)


def order(oid, kg=50, pickup=(1.29, 36.82), dest=(1.30, 36.82), start=None, end=None):
    return PoolOrder(oid, kg, pickup, dest, start, end)


def test_compatible_orders_pool_and_save_money():
    [pool] = propose_pools([order("a"), order("b", pickup=(1.31, 36.81))], MOCK, 500)
    assert {o.order_id for o in pool.orders} == {"a", "b"}
    assert pool.pooled_cost < pool.separate_cost * 0.9
    assert [kind for kind, _, _ in pool.stops] == ["pickup", "pickup", "delivery", "delivery"]


def test_capacity_limits_pooling():
    assert propose_pools([order("a", kg=300), order("b", kg=300)], MOCK, 500) == []


def test_far_destinations_and_incompatible_windows_do_not_pool():
    assert propose_pools([order("a"), order("b", dest=(1.9, 37.5))], MOCK, 500) == []
    early = order("a", start=NOW, end=NOW + timedelta(hours=2))
    late = order("b", start=NOW + timedelta(days=1), end=NOW + timedelta(days=1, hours=2))
    assert propose_pools([early, late], MOCK, 500) == []


def test_pool_skipped_when_savings_too_small():
    # pickups on opposite sides of the destination: sharing the truck saves nothing
    assert propose_pools([order("a", pickup=(1.0, 36.82)), order("b", pickup=(1.6, 36.82))], MOCK, 500) == []


def test_routing_failure_falls_back_to_mock():
    class Broken:
        def estimate(self, a, b): raise RuntimeError("OSRM down")
        def route(self, stops): raise RuntimeError("OSRM down")

    provider = FallbackRoutingProvider(Broken())
    assert provider.estimate((1.29, 36.82), (1.30, 36.82)) == MOCK.estimate((1.29, 36.82), (1.30, 36.82))
    assert delivery_cost(provider.route([(1.29, 36.82), (1.30, 36.82)])) > 10


def test_pool_confirm_and_delivery_flow(db):  # noqa: F811
    session, demo = db
    [pool] = create_pools(session)
    assert float(pool.pooled_cost) < float(pool.separate_cost)
    assert create_pools(session) == []  # orders are never pooled twice
    pooled = {"ord_demo_1", "ord_demo_pool_2"}
    assert {o.id for o in session.query(Order).filter_by(pool_id=pool.id)} == pooled

    quote = session.query(Vehicle).one()
    assert not transporter_has_order(session, "ord_demo_1", "usr_demo_transporter")  # not confirmed yet
    quote_id = session.query(TransportQuote).filter_by(pool_id=pool.id).one().id
    with pytest.raises(HTTPException) as error:
        confirm_pool(session, pool.id, quote_id, "someone_else")
    assert error.value.status_code == 403
    assert confirm_pool(session, pool.id, quote_id, quote.transporter_id).status == "CONFIRMED"
    assert transporter_has_order(session, "ord_demo_1", "usr_demo_transporter")

    shipped = session.get(Order, "ord_demo_1")
    for status in ("READY_FOR_PICKUP", "IN_TRANSIT", "DELIVERED", "COMPLETED"):
        assert transition(shipped, status).status == status
    with pytest.raises(HTTPException):
        transition(shipped, "IN_TRANSIT")
