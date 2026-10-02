from dataclasses import asdict, dataclass
from decimal import Decimal

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from ..shared.store import Allocation as AllocationModel
from ..shared.store import BuyerRequest, Farm, Lot, MatchPlan as MatchPlanModel


@dataclass
class Allocation:
    lot_id: str
    farmer_id: str
    quantity_kg: float
    price_per_kg: float
    distance_km: float
    score: float
    distance_score: float
    price_score: float
    fulfilment_risk: float


@dataclass
class MatchPlan:
    request_id: str
    requested_quantity_kg: float
    allocated_quantity_kg: float
    complete: bool
    allocations: list[Allocation]


class MatchingEngine:
    def match(self, db: Session, request: BuyerRequest, lock_lots: bool = False) -> MatchPlan:
        if request.location is None:
            raise ValueError("Buyer request needs a location before matching")

        distance_m = func.ST_Distance(Farm.location, request.location)
        query = (
            select(Lot, distance_m.label("distance_m"))
            .join(Farm, Farm.id == Lot.farm_id)
            .where(
                Lot.active.is_(True),
                func.lower(Lot.product) == request.product.lower(),
                func.ST_DWithin(Farm.location, request.location, request.radius_km * 1000),
            )
        )
        if request.max_price_per_kg is not None:
            query = query.where(Lot.price_per_kg <= request.max_price_per_kg)
        if lock_lots:
            query = query.order_by(Lot.id).with_for_update(of=Lot)

        eligible = list(db.execute(query))
        price_ceiling = float(request.max_price_per_kg or max((lot.price_per_kg for lot, _ in eligible), default=1))
        candidates = []
        request_quantity = float(request.quantity_kg)
        for lot, raw_distance_m in eligible:
            distance = float(raw_distance_m) / 1000
            distance_score = distance / request.radius_km
            price_score = float(lot.price_per_kg) / price_ceiling
            fulfilment_risk = 1 - min(float(lot.quantity_kg) / request_quantity, 1)
            score = .5 * distance_score + .3 * price_score + .2 * fulfilment_risk
            candidates.append((score, distance, lot, distance_score, price_score, fulfilment_risk))

        candidates.sort(key=lambda candidate: (candidate[0], candidate[1], candidate[2].price_per_kg))
        remaining = request_quantity
        allocations = []
        for score, distance, lot, distance_score, price_score, fulfilment_risk in candidates:
            quantity = min(remaining, float(lot.quantity_kg))
            allocations.append(Allocation(lot.id, lot.farmer_id, quantity, float(lot.price_per_kg), round(distance, 2), round(score, 4), round(distance_score, 4), round(price_score, 4), round(fulfilment_risk, 4)))
            remaining -= quantity
            if remaining <= 0:
                break

        allocated = request_quantity - max(remaining, 0)
        return MatchPlan(request.id, request_quantity, allocated, remaining <= 0, allocations)


def save_match_plan(db: Session, plan: MatchPlan) -> None:
    db.execute(delete(AllocationModel).where(AllocationModel.request_id == plan.request_id))
    stored = db.get(MatchPlanModel, plan.request_id)
    if stored:
        stored.requested_quantity_kg = Decimal(str(plan.requested_quantity_kg))
        stored.allocated_quantity_kg = Decimal(str(plan.allocated_quantity_kg))
        stored.complete = plan.complete
    else:
        db.add(MatchPlanModel(request_id=plan.request_id, requested_quantity_kg=plan.requested_quantity_kg, allocated_quantity_kg=plan.allocated_quantity_kg, complete=plan.complete))
    db.flush()
    db.add_all(AllocationModel(request_id=plan.request_id, **asdict(allocation)) for allocation in plan.allocations)
