import argparse

from api.app.shared.database import SessionLocal
from api.app.shared.demo import seed_demo_data


def main() -> None:
    parser = argparse.ArgumentParser(description="Reset the configured database and load marketplace demo data.")
    parser.add_argument("--yes-reset", action="store_true", help="Confirm that existing marketplace rows may be deleted.")
    if not parser.parse_args().yes_reset:
        parser.error("--yes-reset is required because this command clears marketplace tables")
    with SessionLocal() as db:
        result = seed_demo_data(db)
        db.commit()
        print(f"Seeded {len(result['lot_ids'])} lots; buyer request {result['request_id']}")


if __name__ == "__main__":
    main()
