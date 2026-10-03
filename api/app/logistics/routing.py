from math import asin, cos, radians, sin, sqrt
from typing import Protocol

Point = tuple[float, float]  # (latitude, longitude)


class RoutingProvider(Protocol):
    def estimate(self, origin: Point, destination: Point) -> float: ...  # road km
    def route(self, stops: list[Point]) -> float: ...  # road km through stops in order


class MockRoutingProvider:
    """Haversine x road factor. ponytail: straight-line estimate, swap in OSRM/GraphHopper for real roads."""

    road_factor = 1.3

    def estimate(self, origin: Point, destination: Point) -> float:
        lat1, lon1, lat2, lon2 = map(radians, (*origin, *destination))
        a = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
        return 2 * 6371 * asin(sqrt(a)) * self.road_factor

    def route(self, stops: list[Point]) -> float:
        return sum(self.estimate(a, b) for a, b in zip(stops, stops[1:]))


class FallbackRoutingProvider:
    """Use the primary provider, fall back to the mock when it fails."""

    def __init__(self, primary: RoutingProvider, fallback: RoutingProvider | None = None):
        self.primary, self.fallback = primary, fallback or MockRoutingProvider()

    def estimate(self, origin: Point, destination: Point) -> float:
        try:
            return self.primary.estimate(origin, destination)
        except Exception:
            return self.fallback.estimate(origin, destination)

    def route(self, stops: list[Point]) -> float:
        try:
            return self.primary.route(stops)
        except Exception:
            return self.fallback.route(stops)
