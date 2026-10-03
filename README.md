# Farmer Marketplace

PostgreSQL/PostGIS-backed marketplace: farmers publish produce, buyers open geographically matched requests, grouped orders reserve inventory transactionally, compatible deliveries share a truck, every delivery step is recorded as evidence, and administrators moderate users, listings and disputes.

**Status:** Phases 1 to 4 of [FARMER_MARKETPLACE_BUILD_GUIDE.md](FARMER_MARKETPLACE_BUILD_GUIDE.md) are built. Phase 5 (payments and Solana settlement) is next.

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

Use **Buyer demo** for matching, grouped orders, confirming receipt and disputes, **Farmer demo** for the order queue, marking produce ready and the farm map, **Transporter demo** for pooled transport, or **Admin demo** for moderation and dispute resolution.

Opening a demo role seeds sample accounts, farms, listings, requests, and orders in PostgreSQL. Set `ENABLE_DEMO_SEED=0` outside local development: `POST /demo/seed` needs no login and wipes all marketplace tables.

For a controlled one-time seed, run `.venv/bin/python -m api.scripts.seed_demo --yes-reset`. This command deletes existing marketplace rows before loading the demo dataset.

## Phases

| Phase | What it adds | Main code |
|---|---|---|
| 1. Foundation | Auth, farmer profiles, farms, produce lots, orders, admin moderation | `api/app/{auth,users,farms,catalog,orders,admin}` |
| 2. Matching | Radius search (PostGIS), explainable score, multi-farmer allocation, saved match plans | `api/app/matching` |
| 3. Pooled transport | Vehicles, pool proposals, separate-vs-pooled cost, quotes, pickup and delivery | `api/app/logistics` |
| 4. Trust | Attestations with evidence hashes, reputation events and score, disputes, order cancellation | `api/app/trust`, `api/app/shared/events.py` |

**Phase 2.** `GET /buyer-requests/{id}/matches` previews an allocation across farmers; `POST /buyer-requests/{id}/orders` revalidates stock and creates linked farmer orders for a complete plan. Score = 0.5 x distance + 0.3 x price + 0.2 x fulfilment risk (lower is better).

**Phase 3.** `POST /transport-pools/propose` groups accepted orders by destination area, delivery window, pickup proximity and vehicle capacity, and keeps a pool only if it saves at least 10%. `POST /transport-pools/{id}/confirm` assigns a vehicle from a quote; `POST /transport-pools/{id}/dissolve` releases a proposed pool. Distances use a mock routing provider (Haversine x 1.3) behind a `RoutingProvider` interface.

**Phase 4.** Order lifecycle: `PENDING > ACCEPTED > READY_FOR_PICKUP > IN_TRANSIT > DELIVERED > COMPLETED`, plus `CANCELLED`, `DISPUTED` and `REFUNDED`. Each step (`/ready`, `/pickup`, `/deliver`, `/complete`) records an attestation once per order and accepts optional evidence (`evidence_url`, `evidence_b64`; only the SHA-256 hash is stored). Reputation is a projection of events: `GET /users/{id}/reputation`. `GET /orders/{id}/history` lists the confirmation chain; `POST /orders/{id}/dispute` and `POST /disputes/{id}/resolve` (admin) handle disputes; `POST /orders/{id}/cancel` restores stock.

Roles: `buyer`, `farmer`, `transporter`, `admin`.

## Tests

```bash
.venv/bin/pytest api/tests
```

Tests need the database running and the migrations applied. They run against PostgreSQL/PostGIS and roll back after each test.

## Documents

PDFs in `output/pdf/`: `matching-scores-and-transport-pooling.pdf` (how the score and pooling work), `phase1-3-build-audit.pdf` (audit against the build guide), `project-stages-1-to-5.pdf` (stages explained), plus the demo and deployment guides.

## Known gaps

No repository layer, no HTTP-level API tests, auth tokens never expire, and no payment module yet (Phase 5). See `phase1-3-build-audit.pdf`.

PostgreSQL is the source of truth. Farm and buyer-request locations use indexed PostGIS geography points; grouped-order finalization locks inventory rows before reserving stock. Road-routing distance remains a later milestone.
