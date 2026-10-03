from dataclasses import dataclass
from datetime import datetime

from .routing import Point, RoutingProvider

BASE_FEE = 10.0  # default rate card used to compare separate vs pooled; vehicle quotes use their own rates
COST_PER_KM = 0.8
DEST_RADIUS_KM = 5
PICKUP_RADIUS_KM = 30
MIN_SAVINGS = 0.10


@dataclass(frozen=True)
class PoolOrder:
    order_id: str
    kg: float
    pickup: Point
    dest: Point
    window_start: datetime | None = None
    window_end: datetime | None = None


@dataclass
class PoolProposal:
    orders: list[PoolOrder]
    stops: list[tuple[str, str, Point]]  # (kind, order_id, point) in visiting order
    route_km: float
    separate_cost: float
    pooled_cost: float


def delivery_cost(km: float, base_fee: float = BASE_FEE, cost_per_km: float = COST_PER_KM) -> float:
    return base_fee + cost_per_km * km


def _window(start_a, end_a, order: PoolOrder):
    starts = [x for x in (start_a, order.window_start) if x]
    ends = [x for x in (end_a, order.window_end) if x]
    return (max(starts) if starts else None), (min(ends) if ends else None)


def _nearest_first(points: list[tuple[str, Point]], start: Point, provider: RoutingProvider):
    left, ordered = list(points), []
    while left:
        nxt = min(left, key=lambda item: provider.estimate(start, item[1]))
        left.remove(nxt)
        ordered.append(nxt)
        start = nxt[1]
    return ordered


def plan_stops(orders: list[PoolOrder], provider: RoutingProvider):
    """Pickups first (nearest-neighbour from the pickup farthest from the first destination), then deliveries."""
    far = max(orders, key=lambda o: provider.estimate(o.pickup, orders[0].dest))
    pickups = _nearest_first([(o.order_id, o.pickup) for o in orders], far.pickup, provider)
    deliveries = _nearest_first([(o.order_id, o.dest) for o in orders], pickups[-1][1], provider)
    return [("pickup", oid, p) for oid, p in pickups] + [("delivery", oid, p) for oid, p in deliveries]


def propose_pools(orders: list[PoolOrder], provider: RoutingProvider, capacity_kg: float) -> list[PoolProposal]:
    """Greedy grouping by destination area, delivery window, pickup proximity and vehicle capacity.
    ponytail: greedy single pass, O(n * clusters); move to OR-Tools CVRP when real data shows it falls short."""
    clusters: list[dict] = []
    for order in sorted(orders, key=lambda o: o.order_id):
        for cluster in clusters:
            first = cluster["orders"][0]
            window = _window(*cluster["window"], order)
            if (
                cluster["kg"] + order.kg <= capacity_kg
                and provider.estimate(first.dest, order.dest) <= DEST_RADIUS_KM
                and provider.estimate(first.pickup, order.pickup) <= PICKUP_RADIUS_KM
                and not (window[0] and window[1] and window[0] > window[1])
            ):
                cluster["orders"].append(order)
                cluster["kg"] += order.kg
                cluster["window"] = window
                break
        else:
            clusters.append({"orders": [order], "kg": order.kg, "window": (order.window_start, order.window_end)})

    proposals = []
    for cluster in clusters:
        members = cluster["orders"]
        if len(members) < 2:
            continue
        stops = plan_stops(members, provider)
        route_km = provider.route([point for _, _, point in stops])
        separate = sum(delivery_cost(provider.route([o.pickup, o.dest])) for o in members)
        pooled = delivery_cost(route_km)
        if pooled <= separate * (1 - MIN_SAVINGS):
            proposals.append(PoolProposal(members, stops, route_km, round(separate, 2), round(pooled, 2)))
    return proposals
