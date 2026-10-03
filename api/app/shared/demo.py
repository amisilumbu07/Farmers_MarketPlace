from decimal import Decimal

from geoalchemy2.elements import WKTElement
from sqlalchemy import delete
from sqlalchemy.orm import Session

from ..auth.routes import hash_password
from .store import Allocation, Attestation, Dispute, ReputationEvent, BuyerRequest, FarmerProfile, Farm, Lot, MatchPlan, Order, Shipment, ShipmentStop, Token, TransportPool, TransportQuote, User, Vehicle

DEMO_PASSWORD = "demo1234"


def reset_demo_data(db: Session) -> None:
    for model in (Dispute, ReputationEvent, Attestation, ShipmentStop, Shipment, TransportQuote, Allocation, MatchPlan, Order, TransportPool, Vehicle, BuyerRequest, Lot, Farm, FarmerProfile, Token, User):
        db.execute(delete(model))


def seed_demo_data(db: Session) -> dict:
    reset_demo_data(db)
    farmer_1 = User(id="usr_demo_farmer_1", email="farmer.one@example.com", password=hash_password(DEMO_PASSWORD), role="farmer")
    farmer_2 = User(id="usr_demo_farmer_2", email="farmer.two@example.com", password=hash_password(DEMO_PASSWORD), role="farmer")
    buyer = User(id="usr_demo_buyer", email="buyer@example.com", password=hash_password(DEMO_PASSWORD), role="buyer")
    admin = User(id="usr_demo_admin", email="admin@example.com", password=hash_password(DEMO_PASSWORD), role="admin")
    transporter = User(id="usr_demo_transporter", email="transporter@example.com", password=hash_password(DEMO_PASSWORD), role="transporter")
    db.add_all((farmer_1, farmer_2, buyer, admin, transporter))
    db.flush()

    db.add_all((FarmerProfile(user_id=farmer_1.id, display_name="Green Valley Farm", phone="+1 555 0101"), FarmerProfile(user_id=farmer_2.id, display_name="Sunrise Fields", phone="+1 555 0102")))
    farm_1 = Farm(id="farm_demo_valley", farmer_id=farmer_1.id, name="Green Valley Farm", latitude=1.2921, longitude=36.8219, location=WKTElement("POINT(36.8219 1.2921)", srid=4326))
    farm_2 = Farm(id="farm_demo_sunrise", farmer_id=farmer_2.id, name="Sunrise Fields", latitude=1.3102, longitude=36.8127, location=WKTElement("POINT(36.8127 1.3102)", srid=4326))
    db.add_all((farm_1, farm_2))
    db.flush()

    lots = (
        Lot(id="lot_demo_tomatoes", farmer_id=farmer_1.id, farm_id=farm_1.id, product="Tomatoes", quantity_kg=Decimal("80"), price_per_kg=Decimal("0.70")),
        Lot(id="lot_demo_tomatoes_sunrise", farmer_id=farmer_2.id, farm_id=farm_2.id, product="Tomatoes", quantity_kg=Decimal("70"), price_per_kg=Decimal("0.75")),
        Lot(id="lot_demo_onions", farmer_id=farmer_1.id, farm_id=farm_1.id, product="Onions", quantity_kg=Decimal("150"), price_per_kg=Decimal("0.45")),
        Lot(id="lot_demo_cabbage", farmer_id=farmer_2.id, farm_id=farm_2.id, product="Cabbage", quantity_kg=Decimal("60"), price_per_kg=Decimal("0.55")),
    )
    db.add_all(lots)
    db.flush()

    order = Order(id="ord_demo_1", buyer_id=buyer.id, lot_id=lots[0].id, quantity_kg=Decimal("20"), status="ACCEPTED", dest_latitude=1.3000, dest_longitude=36.8200)
    pool_order = Order(id="ord_demo_pool_2", buyer_id=buyer.id, lot_id=lots[1].id, quantity_kg=Decimal("10"), status="ACCEPTED", dest_latitude=1.3010, dest_longitude=36.8210)
    db.add(Vehicle(id="veh_demo_van", transporter_id=transporter.id, capacity_kg=Decimal("500"), base_fee=Decimal("12"), cost_per_km=Decimal("0.9")))
    pending_order = Order(id="ord_demo_pending", buyer_id=buyer.id, lot_id=lots[1].id, quantity_kg=Decimal("10"), status="PENDING")
    lots[0].quantity_kg -= Decimal("20")
    lots[1].quantity_kg -= Decimal("20")
    request = BuyerRequest(id="req_demo_tomatoes", buyer_id=buyer.id, product="Tomatoes", quantity_kg=Decimal("100"), max_price_per_kg=Decimal("0.80"), latitude=1.3000, longitude=36.8200, location=WKTElement("POINT(36.82 1.3)", srid=4326), radius_km=50)
    delivered = Order(id="ord_demo_delivered", buyer_id=buyer.id, lot_id=lots[2].id, quantity_kg=Decimal("10"), status="DELIVERED")
    lots[2].quantity_kg -= Decimal("10")
    db.add_all((order, pending_order, pool_order, delivered, request))
    db.flush()
    db.add_all(Attestation(id=f"att_demo_{kind.lower()}", subject_type="order", subject_id=delivered.id, actor_id=actor.id, type=kind) for kind, actor in (("HANDOFF_CONFIRMED", farmer_1), ("PICKUP_CONFIRMED", transporter), ("DELIVERY_CONFIRMED", transporter)))
    db.add(ReputationEvent(user_id=transporter.id, type="DELIVERY_ON_TIME", order_id=delivered.id))

    buyer_token = "token_demo_buyer"
    farmer_token = "token_demo_farmer"
    admin_token = "token_demo_admin"
    transporter_token = "token_demo_transporter"
    db.add_all((Token(token=buyer_token, user_id=buyer.id), Token(token=farmer_token, user_id=farmer_2.id), Token(token=admin_token, user_id=admin.id), Token(token=transporter_token, user_id=transporter.id)))
    return {
        "token": buyer_token,
        "user_id": buyer.id,
        "role": buyer.role,
        "order_id": order.id,
        "request_id": request.id,
        "lot_ids": [lot.id for lot in lots],
        "credentials": {"email": buyer.email, "password": DEMO_PASSWORD},
        "farmer_session": {"token": farmer_token, "user_id": farmer_2.id, "role": farmer_2.role, "farm_id": farm_2.id, "farm": {"id": farm_2.id, "farmer_id": farm_2.farmer_id, "name": farm_2.name, "latitude": farm_2.latitude, "longitude": farm_2.longitude}},
        "transporter_session": {"token": transporter_token, "user_id": transporter.id, "role": transporter.role},
        "admin_session": {"token": admin_token, "user_id": admin.id, "role": admin.role},
    }
