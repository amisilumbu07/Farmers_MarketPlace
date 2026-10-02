# Farmer Marketplace

PostgreSQL/PostGIS-backed marketplace: farmers publish produce, buyers open geographically matched requests, grouped orders reserve inventory transactionally, and administrators moderate users and listings.

## Run

```bash
docker compose up -d database
python -m venv .venv
.venv/bin/pip install -r api/requirements.txt
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --app-dir api --reload
```

API docs: <http://127.0.0.1:8000/docs>

Test UI: <http://127.0.0.1:8000/>

Next.js UI:

```bash
cd apps/web
npm install
npm run dev
```

Open <http://localhost:3000/> after starting the API. Set `NEXT_PUBLIC_API_URL` if the API runs somewhere else.

Use **Buyer demo** for matching and grouped order creation, **Farmer demo** for the order queue and farm map, or **Admin demo** for moderation and order visibility.

Opening a demo role seeds sample accounts, farms, listings, requests, and orders in PostgreSQL. Set `ENABLE_DEMO_SEED=0` outside local development.

For a controlled one-time seed, run `.venv/bin/python -m api.scripts.seed_demo --yes-reset`. This command deletes existing marketplace rows before loading the demo dataset.

Demo walkthrough: [farmer-marketplace-demo.pdf](/home/amisiespoir-07/Dev/singapore/output/pdf/farmer-marketplace-demo.pdf)

Phase 2 adds radius filtering and an explainable score based on normalized distance, price, and fulfilment risk. `GET /buyer-requests/{request_id}/matches` previews an allocation across farmers; `POST /buyer-requests/{request_id}/orders` revalidates stock and creates linked farmer orders for a complete plan.

Run the Phase 1 flow check:

```bash
.venv/bin/pytest api/tests
```

PostgreSQL is the source of truth. Farm and buyer-request locations use indexed PostGIS geography points; grouped-order finalization locks inventory rows before reserving stock. Road-routing distance remains a later milestone.
# Farmers_MarketPlace
