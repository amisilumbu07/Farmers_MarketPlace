# Farmer Marketplace — Junior Engineer Build Guide

> **Goal:** Build a maintainable agricultural marketplace in phases without locking the project into AI, blockchain, or x402 too early.
>
> **Core rule:** The marketplace must work without Solana, AI, or x402. These are adapters added around a stable domain model.

---

## 0. What We Are Building

The application connects **farmers**, **buyers**, and later **transporters**.

```text
Farmer lists produce
        ↓
Buyer creates demand
        ↓
Marketplace finds suitable supply
        ↓
Several farmers can satisfy one large order
        ↓
Compatible orders can share transportation
        ↓
Pickup + delivery are confirmed
        ↓
Payment settles
        ↓
Verified transaction history improves reputation
```

### Long-term phases

1. **Phase 1 — Marketplace foundation**
2. **Phase 2 — Geospatial matching & supply aggregation**
3. **Phase 3 — Pooled transportation**
4. **Phase 4 — Trust, reputation & transaction evidence**
5. **Phase 5 — Solana settlement adapter**
6. **Phase 6 — Intelligence / AI (only after real data exists)**
7. **Phase 7 — x402 machine-to-machine payments**

Do not build all seven at once.

---

# 1. Choose a Stable Architecture First

For a junior-friendly MVP, use a **modular monolith** rather than microservices.

```text
farmer-marketplace/
│
├── apps/
│   ├── web/                 # Next.js frontend
│   └── api/                 # FastAPI backend
│
├── packages/
│   ├── contracts/           # Shared API schemas / generated types
│   └── ui/                  # Optional reusable UI components
│
├── services/                # Future external-service adapters
│   ├── payments/
│   ├── routing/
│   ├── blockchain/
│   ├── notifications/
│   └── intelligence/
│
├── infra/
│   ├── docker/
│   ├── migrations/
│   └── deployment/
│
├── docs/
│   ├── architecture.md
│   ├── api.md
│   └── decisions/
│
└── README.md
```

## Recommended stack

| Layer | Recommended technology | Why |
|---|---|---|
| Frontend | **Next.js + TypeScript + React** | Large ecosystem, good web/PWA path |
| UI | **Tailwind CSS + shadcn/ui** | Fast MVP development |
| Backend | **FastAPI + Python** | Clear APIs; excellent later path for optimization/AI |
| API validation | **Pydantic** | Strong request/response contracts |
| ORM | **SQLAlchemy 2.x** | Mature Python database layer |
| Database | **PostgreSQL** | Reliable relational core |
| Geospatial | **PostGIS** | Farmer/buyer proximity queries |
| Migrations | **Alembic** | Version-controlled schema changes |
| Background jobs | **Celery/RQ later** | Do not add until asynchronous work is needed |
| Cache/queue | **Redis later** | Add only when jobs/caching justify it |
| Maps | **MapLibre + OpenStreetMap** | Avoid tying domain logic to a map vendor |
| Routing | **OSRM / GraphHopper adapter** | Road routes without coupling core logic |
| Optimization | **Google OR-Tools later** | Vehicle routing / allocation problems |
| Blockchain | **Solana + Anchor (Rust)** | Phase 5 only |
| Testing | **Pytest + Vitest/Playwright** | Unit/API/end-to-end coverage |
| Containers | **Docker Compose** | Consistent local environment |

### Important version rule

Pin major dependencies. Do not install libraries randomly into the application.

```text
Frontend dependency → package.json
Backend dependency  → pyproject.toml / requirements lock
Solana program      → separate program directory/toolchain
```

The Solana/Rust toolchain should **not** live inside the Python backend environment.

---

# 2. Domain Model — Build This Before Fancy Features

The domain model should not know whether payment uses Stripe, mobile money, USDC, Solana, or x402.

Start with these entities:

```text
User
├── FarmerProfile
├── BuyerProfile
└── TransporterProfile (later)

Farm
Product
ProduceLot
BuyerRequest
Order
OrderItem
Shipment
Payment
Attestation
ReputationEvent
```

### Example ProduceLot

```json
{
  "id": "lot_123",
  "farmer_id": "farmer_42",
  "product": "tomato",
  "quantity_kg": 150,
  "price_per_kg": 0.70,
  "latitude": -1.2921,
  "longitude": 36.8219,
  "available_from": "2026-10-10",
  "status": "available"
}
```

### Order state machine

Never represent order status with random strings changed anywhere in the code.

```text
DRAFT
  ↓
PENDING
  ↓
ACCEPTED
  ↓
READY_FOR_PICKUP
  ↓
IN_TRANSIT
  ↓
DELIVERED
  ↓
COMPLETED

Exceptional:
CANCELLED
DISPUTED
REFUNDED
```

Create one application service responsible for valid state transitions.

---

# PHASE 1 — Marketplace Foundation

## Objective

Prove that a farmer can publish produce and a buyer can find and order it.

### Build

**Farmer**
- Register/login
- Create farmer profile
- Create farm
- Add location
- Create/edit/deactivate produce listings

**Buyer**
- Register/login
- Browse products
- Filter by product/price
- View farmer/listing
- Create order/request

**Admin**
- Basic user/listing moderation
- View orders

### Backend modules

```text
api/app/
├── auth/
├── users/
├── farms/
├── catalog/
├── orders/
├── payments/
├── shared/
└── main.py
```

Each module should approximately contain:

```text
catalog/
├── models.py
├── schemas.py
├── repository.py
├── service.py
└── routes.py
```

**Route → Service → Repository → Database**

Do not put business rules directly in API routes.

### Minimum API

```text
POST   /auth/register
POST   /auth/login
GET    /products
POST   /farms
POST   /lots
GET    /lots
GET    /lots/{id}
PATCH  /lots/{id}
POST   /buyer-requests
POST   /orders
GET    /orders/{id}
```

### Phase 1 definition of done

A test user can:

```text
Farmer → list 100kg tomatoes
Buyer → discover tomatoes
Buyer → create an order
Farmer → accept order
Buyer → mark simple demo order complete
```

No blockchain. No AI. No x402.

---

# PHASE 2 — Location Matching & Farmer Aggregation

## Objective

Allow one buyer request to be filled by one or several nearby farmers.

### Add PostGIS

Store locations as geographic points and query within a radius.

```text
Buyer request
    ↓
Product filter
    ↓
Availability filter
    ↓
PostGIS radius search
    ↓
Candidate farmers
    ↓
Rank candidates
```

### Do not use DFS for shortest path

DFS is useful for traversal/reachability, not weighted shortest road paths.

Use:

- **PostGIS/Haversine** for initial proximity.
- **Dijkstra or A\*** through a routing engine for road distance/time.

### First ranking formula

Keep it explainable.

```text
score =
    distance_weight × normalized_distance
  + price_weight    × normalized_price
  + risk_weight     × fulfilment_risk
```

Lower score = better match.

Do not use machine learning yet.

### Supply aggregation

Request:

```text
Buyer needs 400kg tomatoes
```

Available:

```text
Farmer A → 150kg
Farmer B → 100kg
Farmer C → 200kg
```

Allocation:

```text
A 150 + B 100 + C 150 = 400kg
```

Create a `MatchPlan`/`Allocation` object before creating the final order.

### Keep matching behind an interface

```python
class MatchingEngine:
    def match(self, request):
        ...
```

Today it can use deterministic rules.

Later it can use OR-Tools or AI without rewriting order management.

---

# PHASE 3 — Pooled Transportation

## Objective

Reduce delivery cost by combining compatible orders.

### New entities

```text
Transporter
Vehicle
Shipment
ShipmentStop
TransportPool
TransportQuote
```

### Simple first algorithm

Do **not** start with an advanced global vehicle-routing solver.

Group orders using:

1. destination area/geohash;
2. requested delivery window;
3. pickup proximity;
4. vehicle capacity.

```text
Order A ─┐
Order B ─┼── same destination/time → Pool 1
Order C ─┘

Order D ───── different destination → Pool 2
```

Then compare:

```text
separate_delivery_cost
vs
pooled_delivery_cost
```

Only create a pool when it saves enough money and still meets delivery constraints.

### Later optimization

Introduce **Google OR-Tools** when real data shows the heuristic is insufficient.

Possible future problem:

```text
Capacitated Vehicle Routing Problem (CVRP)
+ pickup/delivery
+ time windows
```

Keep optimization in:

```text
services/routing/
```

not inside `orders/`.

### Routing provider interface

```python
class RoutingProvider:
    def route(self, stops): ...
    def estimate(self, origin, destination): ...
```

Possible implementations:

```text
OSRMRoutingProvider
GraphHopperRoutingProvider
MockRoutingProvider
```

This prevents vendor lock-in.

---

# PHASE 4 — Trust, Evidence & Reputation

## Objective

Create useful trust before introducing blockchain.

### Do not start with stars

Store **events**.

```text
ORDER_COMPLETED
DELIVERY_ON_TIME
DELIVERY_LATE
QUALITY_ACCEPTED
QUALITY_REJECTED
DISPUTE_OPENED
DISPUTE_RESOLVED
ORDER_CANCELLED
```

A reputation score is a projection of those events.

```text
Events → Reputation Calculator → Current Score
```

That means you can change the scoring formula later without losing history.

### Attestations

Create an `Attestation` model now even before Solana exists.

```json
{
  "subject_type": "shipment",
  "subject_id": "shipment_45",
  "actor_id": "transporter_9",
  "type": "PICKUP_CONFIRMED",
  "timestamp": "...",
  "evidence_url": "...",
  "evidence_hash": "..."
}
```

Possible confirmation sequence:

```text
Farmer confirms handoff
        ↓
Transporter confirms pickup
        ↓
Transporter confirms delivery
        ↓
Buyer confirms receipt
        ↓
Order completed
        ↓
Reputation events generated
```

This data model is deliberately blockchain-ready.

---

# PHASE 5 — Solana Trust & Settlement Adapter

## Objective

Add blockchain where multiple parties benefit from a shared verifiable record.

Do not migrate the marketplace database onto Solana.

### Architecture

```text
                    Next.js
                       │
                    FastAPI
                       │
        ┌──────────────┼──────────────┐
        ↓              ↓              ↓
   PostgreSQL     PaymentPort    AttestationPort
                       │              │
                       └──────┬───────┘
                              ↓
                       Solana Adapter
                              ↓
                       Solana Program
```

### Define payment interfaces before Solana

```python
class PaymentProvider:
    def create_payment(self, order): ...
    def get_status(self, payment_id): ...
    def capture(self, payment_id): ...
    def refund(self, payment_id): ...
```

Possible implementations:

```text
MockPaymentProvider
FiatPaymentProvider
SolanaPaymentProvider
```

The order service talks to `PaymentProvider`, **never directly to Solana SDK code**.

### Put on-chain

Potentially:

- order/payment commitment;
- settlement status;
- important delivery attestation hashes;
- dispute resolution result;
- optional reputation checkpoint.

### Keep off-chain

- farmer personal information;
- exact private locations;
- photos;
- chat messages;
- search;
- routing;
- raw reviews;
- large documents;
- AI output.

### Solana directory

Keep programs isolated:

```text
blockchain/
└── solana/
    ├── programs/
    │   └── marketplace-settlement/
    ├── tests/
    └── Anchor.toml
```

Do not import Rust/Anchor dependencies into FastAPI.

The backend communicates through a small blockchain adapter/client.

---

# PHASE 6 — Intelligence / AI

## Objective

Use accumulated marketplace data to improve decisions.

Do this only when you have enough reliable data.

### Good future use cases

```text
Demand forecasting
Supply-risk forecasting
Price recommendations
Fraud/anomaly detection
Transport-pool recommendations
Multilingual farmer assistant
Image-assisted quality inspection
```

### Keep AI behind interfaces

```python
class DemandForecastProvider:
    def forecast(self, product, region, horizon): ...
```

The rest of the marketplace should work if this provider is disabled.

### Data pipeline

```text
Operational PostgreSQL
        ↓
Analytics/warehouse layer
        ↓
Feature preparation
        ↓
Model
        ↓
Prediction API
        ↓
Marketplace recommendation
```

Do not train models directly against uncontrolled production tables.

---

# PHASE 7 — Optional x402 Layer

## Objective

Allow software/AI agents to pay automatically for digital services.

**x402 is not the primary farmer checkout mechanism.**

It belongs at the service boundary.

### Example

```text
Buyer Procurement Agent
        │
        ├── Market-price API ── x402 payment
        │
        ├── Weather API ─────── x402 payment
        │
        ├── Quality API ─────── x402 payment
        │
        └── Transport API ───── x402 payment
        │
        ↓
Marketplace matching
        ↓
Normal order
        ↓
Solana/local settlement
```

### Prepare for x402 from day one without installing it

Do this by defining a generic service-payment interface:

```python
class ServicePaymentProvider:
    def authorize(self, service, amount, metadata): ...
    def settle(self, authorization): ...
```

Later:

```text
NoOpServicePaymentProvider
        ↓ replace with
X402ServicePaymentProvider
```

The matching engine should not know what x402 is.

### Example future directory

```text
services/
└── payments/
    ├── base.py
    ├── order_payment.py
    ├── service_payment.py
    ├── solana_adapter.py
    └── x402_adapter.py       # Phase 7
```

This is the key to avoiding architecture conflict.

---

# 3. Architecture Rules the Junior Engineer Must Follow

## Rule 1 — Domain logic must not depend on infrastructure

Bad:

```python
def create_order(order):
    solana_client.send_transaction(...)
```

Better:

```python
def create_order(order, payment_provider):
    payment_provider.create_payment(order)
```

---

## Rule 2 — External services always get adapters

Use interfaces for:

```text
Payments
Blockchain
Routing
Maps
Notifications
Object storage
AI
x402
```

Then vendors can change without rewriting the application.

---

## Rule 3 — PostgreSQL is the operational source of truth

Do not make the frontend reconstruct application state from blockchain events.

```text
PostgreSQL = operational application state
Solana     = settlement/shared verification layer
```

Synchronize important chain events back into the database.

---

## Rule 4 — Use events for cross-module actions

Example:

```text
ORDER_DELIVERED
      │
      ├── Reputation module updates history
      ├── Payment module releases payment
      ├── Notification module sends message
      └── Blockchain module records proof
```

Initially these can be simple in-process domain events.

Later they can move to a queue without changing the domain concept.

---

## Rule 5 — Avoid premature microservices

Start:

```text
1 frontend
1 backend
1 PostgreSQL database
```

not:

```text
12 services
5 queues
3 databases
Kubernetes
```

Split services only when scaling/team boundaries justify it.

---

# 4. Recommended Database Skeleton

```text
users
farmer_profiles
buyer_profiles
transporter_profiles
farms
products
produce_lots
buyer_requests
match_plans
match_allocations
orders
order_items
shipments
shipment_stops
transport_pools
payments
attestations
reputation_events
external_transactions
```

### `external_transactions`

Create this early so external payment systems remain generic.

```text
id
provider                # mock / fiat / solana / x402 later
external_id
purpose                 # order / refund / service_api
amount
currency
status
metadata_json
created_at
updated_at
```

Do **not** create columns such as `solana_tx` throughout unrelated tables.

Keep provider-specific identifiers centralized.

---

# 5. Frontend Skeleton

```text
apps/web/
├── app/
│   ├── auth/
│   ├── marketplace/
│   ├── farmer/
│   │   ├── dashboard/
│   │   ├── farms/
│   │   └── listings/
│   ├── buyer/
│   │   ├── requests/
│   │   └── orders/
│   ├── logistics/
│   └── orders/
│
├── components/
├── features/
│   ├── marketplace/
│   ├── orders/
│   ├── maps/
│   └── payments/
│
└── lib/
    ├── api/
    ├── auth/
    └── config/
```

Do not call Solana directly from random React components.

Use:

```text
UI → frontend service/hook → backend API → payment/blockchain adapter
```

Wallet signing is the exception when user authorization genuinely requires it, and even then isolate wallet code inside the payment feature.

---

# 6. Testing Strategy by Phase

### Phase 1

- authentication tests;
- listing CRUD;
- order-state tests;
- permissions;
- API integration tests.

### Phase 2

- radius-query tests;
- deterministic ranking tests;
- partial-allocation tests;
- insufficient-supply cases.

### Phase 3

- capacity tests;
- incompatible time windows;
- pooling savings calculation;
- route-provider failure fallback.

### Phase 4

- reputation event generation;
- duplicate attestation prevention;
- dispute cases;
- evidence hashing.

### Phase 5

- blockchain adapter mocked in normal backend tests;
- separate Solana program tests;
- failed transaction/retry handling;
- chain/database reconciliation.

### Phase 7

- x402 adapter contract tests;
- payment-required response handling;
- duplicate payment/idempotency;
- failed service delivery after payment.

---

# 7. Security Rules

Never store:

- private wallet keys in source code;
- secrets in Git;
- passwords in plaintext;
- unnecessary personal data on-chain.

Use environment variables/secrets management.

Validate authorization on the backend even when the frontend hides a button.

Every payment operation needs an **idempotency key** so retries cannot accidentally charge twice.

Every external webhook/chain event should be verified before changing order state.

---

# 8. Suggested Development Milestones

## Milestone A — Local marketplace

```text
[ ] Repository created
[ ] Docker local environment
[ ] PostgreSQL/PostGIS
[ ] Authentication
[ ] Farmer profile
[ ] Farm
[ ] Produce listing
[ ] Buyer search
[ ] Order
[ ] Basic tests
```

## Milestone B — Smart aggregation

```text
[ ] Buyer request
[ ] Radius search
[ ] Candidate ranking
[ ] Multi-farmer allocation
[ ] Match-plan UI
```

## Milestone C — Logistics

```text
[ ] Transporter profile
[ ] Vehicle
[ ] Shipment
[ ] Pooling heuristic
[ ] Route adapter
[ ] Cost-saving comparison
```

## Milestone D — Trust

```text
[ ] Attestations
[ ] Evidence hashes
[ ] Reputation events
[ ] Disputes
[ ] Transaction history
```

## Milestone E — Solana

```text
[ ] PaymentProvider interface stable
[ ] Solana adapter
[ ] Testnet/devnet flow
[ ] Settlement program
[ ] Delivery proof hash
[ ] Chain/database reconciliation
```

## Milestone F — Data intelligence

```text
[ ] Analytics events
[ ] Clean historical dataset
[ ] Baseline forecasts
[ ] Recommendation interface
```

## Milestone G — x402

```text
[ ] ServicePaymentProvider already exists
[ ] Identify a real paid machine service
[ ] Add x402 adapter
[ ] Test agent/API payment
[ ] Keep normal marketplace checkout unchanged
```

---

# 9. What the First Demo Should Show

Do not demo every future feature.

Demo this story:

```text
1. Farmer A lists 150kg tomatoes.
2. Farmer B lists 300kg tomatoes.
3. Buyer requests 400kg.
4. System finds both farms and creates a 150 + 250 allocation.
5. Another compatible buyer order exists nearby.
6. System shows separate transport vs pooled transport cost.
7. Buyer confirms order.
8. Farmer/transporter/buyer confirm fulfilment.
9. Transaction becomes verified and reputation updates.
10. Optional: show a Solana settlement/proof transaction.
```

Then explain x402 as the future machine-payment layer rather than forcing it into the demo.

---

# 10. Final Architecture

```text
                         ┌─────────────────┐
                         │   Next.js Web   │
                         └────────┬────────┘
                                  │ REST/API
                         ┌────────▼────────┐
                         │     FastAPI     │
                         │ Modular Monolith│
                         └────────┬────────┘
                                  │
       ┌──────────────────────────┼──────────────────────────┐
       │                          │                          │
       ▼                          ▼                          ▼
 PostgreSQL/PostGIS         RoutingPort                PaymentPort
       │                          │                          │
       │                    OSRM/GraphHopper        ┌───────┴────────┐
       │                                           │                │
       │                                      Fiat/Mock       Solana Adapter
       │                                                            │
       │                                                        Solana Program
       │
       ├──────── Reputation / Attestations
       │
       └──────── Domain Events
                    │
              Future adapters
       ┌────────────┼──────────────┐
       ▼            ▼              ▼
      AI         Weather API    Service Payments
                                      │
                                   x402
                                 (Phase 7)
```

---

# 11. The Most Important Engineering Principle

> **Design interfaces for future capabilities; do not install future complexity.**

From Phase 1, create clean boundaries for:

- `PaymentProvider`
- `RoutingProvider`
- `MatchingEngine`
- `AttestationProvider`
- `NotificationProvider`
- `DemandForecastProvider`
- `ServicePaymentProvider`

But initially implement only what the current phase needs.

This gives the project room to grow into Solana, AI and x402 without making a junior engineer debug seven ecosystems before the first farmer can list a tomato.
