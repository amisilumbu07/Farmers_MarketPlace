from decimal import Decimal

from geoalchemy2.elements import WKTElement
from sqlalchemy import delete
from sqlalchemy.orm import Session

from ..auth.routes import hash_password
from .store import Allocation, BuyerRequest, FarmerProfile, Farm, Lot, MatchPlan, Order, Token, User

DEMO_PASSWORD = "demo1234"


def reset_demo_data(db: Session) -> None:
    for model in (Allocation, MatchPlan, Order, BuyerRequest, Lot, Farm, FarmerProfile, Token, User):
        db.execute(delete(model))


def seed_demo_data(db: Session) -> dict:
    reset_demo_data(db)
    farmer_1 = User(id="usr_demo_farmer_1", email="farmer.one@example.com", password=hash_password(DEMO_PASSWORD), role="farmer")
    farmer_2 = User(id="usr_demo_farmer_2", email="farmer.two@example.com", password=hash_password(DEMO_PASSWORD), role="farmer")
    buyer = User(id="usr_demo_buyer", email="buyer@example.com", password=hash_password(DEMO_PASSWORD), role="buyer")
    admin = User(id="usr_demo_admin", email="admin@example.com", password=hash_password(DEMO_PASSWORD), role="admin")
    db.add_all((farmer_1, farmer_2, buyer, admin))
    db.flush()

    db.add_all((FarmerProfile(user_id=farmer_1.id, display_name="Green Valley Farm", phone="+1 555 0101"), FarmerProfile(user_id=farmer_2.id, display_name="Sunrise Fields", phone="+1 555 0102")))
    farm_1 = Farm(id="farm_demo_valley", farmer_id=farmer_1.id, name="Green Valley Farm", latitude=1.2921, longitude=36.8219, location=WKTElement("POINT(36.8219 1.2921)", srid=4326))
    farm_2 = Farm(id="farm_demo_sunrise", farmer_id=farmer_2.id, name="Sunrise Fields", latitude=1.3102, longitude=36.8127, location=WKTElement("POINT(36.8127 1.3102)", srid=4326))
    db.add_all((farm_1, farm_2))
    db.flush()

    lots = (
        Lot(id="lot_demo_tomatoes", farmer_id=farmer_1.id, farm_id=farm_1.id, product="Tomatoes", quantity_kg=Decimal("80"), price_per_kg=Decimal("0.70")),
        Lot(id="lot_demo_tomatoes_sunrise", farmer_id=farmer_2.id, farm_id=farm_2.id, product="Tomatoes", quantity_kg=Decimal("60"), price_per_kg=Decimal("0.75")),
        Lot(id="lot_demo_onions", farmer_id=farmer_1.id, farm_id=farm_1.id, product="Onions", quantity_kg=Decimal("150"), price_per_kg=Decimal("0.45")),
        Lot(id="lot_demo_cabbage", farmer_id=farmer_2.id, farm_id=farm_2.id, product="Cabbage", quantity_kg=Decimal("60"), price_per_kg=Decimal("0.55")),
    )
    db.add_all(lots)
    db.flush()

    order = Order(id="ord_demo_1", buyer_id=buyer.id, lot_id=lots[0].id, quantity_kg=Decimal("20"), status="ACCEPTED")
    pending_order = Order(id="ord_demo_pending", buyer_id=buyer.id, lot_id=lots[1].id, quantity_kg=Decimal("10"), status="PENDING")
    lots[0].quantity_kg -= Decimal("20")
    lots[1].quantity_kg -= Decimal("10")
    request = BuyerRequest(id="req_demo_tomatoes", buyer_id=buyer.id, product="Tomatoes", quantity_kg=Decimal("100"), max_price_per_kg=Decimal("0.80"), latitude=1.3000, longitude=36.8200, location=WKTElement("POINT(36.82 1.3)", srid=4326), radius_km=50)
    db.add_all((order, pending_order, request))

    buyer_token = "token_demo_buyer"
    farmer_token = "token_demo_farmer"
    admin_token = "token_demo_admin"
    db.add_all((Token(token=buyer_token, user_id=buyer.id), Token(token=farmer_token, user_id=farmer_2.id), Token(token=admin_token, user_id=admin.id)))
    return {
        "token": buyer_token,
        "user_id": buyer.id,
        "role": buyer.role,
        "order_id": order.id,
        "request_id": request.id,
        "lot_ids": [lot.id for lot in lots],
        "credentials": {"email": buyer.email, "password": DEMO_PASSWORD},
        "farmer_session": {"token": farmer_token, "user_id": farmer_2.id, "role": farmer_2.role, "farm_id": farm_2.id, "farm": {"id": farm_2.id, "farmer_id": farm_2.farmer_id, "name": farm_2.name, "latitude": farm_2.latitude, "longitude": farm_2.longitude}},
        "admin_session": {"token": admin_token, "user_id": admin.id, "role": admin.role},
    }
