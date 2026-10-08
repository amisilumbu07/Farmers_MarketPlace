# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Farmer marketplace: FastAPI + PostgreSQL/PostGIS backend (`api/`), Next.js frontend (`apps/web/`), and a Solana settlement program (`blockchain/solana/`). `README.md` has the per-phase feature list and `FARMER_MARKETPLACE_BUILD_GUIDE.md` the original spec.

## Commands

```bash
docker compose up -d database                      # PostGIS 17; tests and the API need it
.venv/bin/alembic upgrade head                      # run from the repo root (alembic.ini is there)
.venv/bin/uvicorn app.main:app --app-dir api --reload
.venv/bin/pytest api/tests                          # all tests (they roll back, DB must be migrated)
.venv/bin/pytest api/tests/test_phase5.py::test_attest_retry_never_appends_twice   # single test
cd apps/web && npm run dev                          # Next.js on :3000; set NEXT_PUBLIC_API_URL if the API is elsewhere
```

Frontend routes (`apps/web/app/`): `/` landing page, `/login` demo role chooser (links to `/tests?role=<role>`), `/tests` the original all-in-one console (it auto-signs in from `?role=`). Per-role routes are planned in `output/pdf/step-a-and-frontend-plan.pdf`. Kill leftovers by pid: `pkill -f next-server` also matches your own shell.

No linter is configured. The API serves a legacy static UI from `web/` at `/` (mounted last in `api/app/main.py`).

Solana program (Anchor 0.30.1, from `blockchain/solana/`):

```bash
anchor build --no-idl          # --no-idl is required: the default nightly rustc breaks the IDL step; the adapter does not use the IDL
solana-test-validator --reset --ledger /tmp/sv-ledger --bpf-program <program id> target/deploy/marketplace_settlement.so
SOLANA_AUTHORITY_KEYPAIR=<keypair file> .venv/bin/python blockchain/solana/scripts/smoke.py   # end-to-end check on any cluster; set SOLANA_RPC_URL for devnet
```

Program error codes: 6000 `AlreadySettled` (0x1770), 6001 `BadOutcome` (0x1771), 6002 `UnexpectedCount` (0x1772). The order account is 118 bytes: status at byte 80, attestation count (u32, little-endian) at 81-84.

Program tests run in memory with LiteSVM against the built `.so` (rebuild first): `cd blockchain/solana/tests-svm && cargo test` (standalone crate, Solana 2.x types, only bytes cross to the Anchor 0.30.1 program). The PyPI `litesvm` package is an empty placeholder, do not install it. `smoke.py` (real cluster) and `api/tests/test_phase5.py` (fake RPC) are the other checks. `tools/build_*.py` generate the PDFs in `output/pdf/` and import helpers from `tools/build_solana_ideation.py`, so run them from inside `tools/`.

## Architecture

- **Modular monolith under `api/app/<domain>/`** (`auth, users, farms, catalog, orders, matching, logistics, trust, payments, admin`), each with `routes.py` and often `service.py`. All ORM models live in one file, `api/app/shared/store.py`; there is no repository layer. Auth is bearer tokens stored in the DB (`shared/auth.py`, `require_role(...)`); roles are `buyer, farmer, transporter, admin`.
- **Domains talk through in-process events** (`shared/events.py`, synchronous, same DB transaction). `orders.service.advance()` validates the transition against `VALID_TRANSITIONS` and publishes `order.status_changed`; `trust` (attestations, reputation) and `payments` subscribe. Handler registration happens on import, and `payments/service.py` imports `trust.service` first so the attestation row exists when the payment handler runs. Keep that import order.
- **Payments are a provider-agnostic mirror, never a gate.** `payments/service.py` turns order events into idempotent `external_transactions` rows (unique key `"<order>:<purpose>"`) and executes them through a `PaymentProvider` (`payments/base.py`): `mock` by default, `solana` when `PAYMENT_PROVIDER=solana`. With the `mock` provider rows execute inline; with a real chain they stay `PENDING` and `process_queue()` sends them (oldest first, ties broken commit, attest by seq, settle), driven by `GET /payments/cron` (needs `CRON_SECRET`, disabled when unset; no `vercel.json` cron yet because Hobby plans reject sub-daily schedules) or manual replay with `POST /admin/payments/retry` (admin). A provider failure is stored as `FAILED` and replayed the same way; it must never block an order. Attestations carry a `seq` (their position in the order's evidence chain): the adapter reads the chain before resending and the program rejects a taken slot (`record_attestation(hash, expected_count)`), so a retry after a lost reply is a no-op. `settle` is likewise skipped when the chain already shows that outcome and raises when it shows the opposite one. Only commit/attest/settle call sites in `payments/service.py` write to the chain.
- **Solana adapter** (`payments/solana_adapter.py`) hand-encodes Anchor instructions over plain JSON-RPC with `solders` (no Anchor client). It depends on the program's account layout (`STATUS_OFFSET`, `COUNT_OFFSET`) and instruction names/argument order in `blockchain/solana/programs/marketplace-settlement/src/lib.rs`. Changing one side means changing the other, then `anchor build --no-idl` and rerunning `smoke.py`. The program stores only hashes and a status; no money moves yet. `solana-first/docs/` is a design draft for a later escrow rebuild, not current code.
- **Database URL handling:** `shared/database.py` rewrites `postgresql://` (what Neon/Vercel inject) to `postgresql+psycopg://`. `migrations/env.py` imports the same URL. PostGIS is required (`geoalchemy2`).

## Deployment

Two Vercel projects, both auto-deploy from `main`: backend `farmers-market-place` (root `api`, entry `api/index.py`) and frontend `farmers-market-place-le5n` (root `apps/web`). Neon Postgres holds the data; migrations are run by hand, they do not run on deploy. `NEXT_PUBLIC_API_URL` is baked in at build time, and the backend `CORS_ORIGINS` must have no trailing slash. `ENABLE_DEMO_SEED` exposes an unauthenticated `POST /demo/seed` that wipes all marketplace tables: set it to `0` before real users.

## Environment notes

- Default `solana` CLI config points at a devnet RPC provider, and the default wallet (`~/.config/solana/id.json`) is funded on devnet (5 SOL on 2026-10-06). A local `solana-test-validator` also pre-funds that wallet, so a mistyped `SOLANA_AUTHORITY_KEYPAIR` still "works" locally; `smoke.py` prints the authority it is using, check it. Devnet reports a newer version than the CLI; that is harmless.
- `SOLANA_AUTHORITY_KEYPAIR_JSON` (the keypair file's JSON array) is the env-secret alternative to the `SOLANA_AUTHORITY_KEYPAIR` file path, needed on Vercel.
- The Solana CLI config RPC (`devnet.helius-rpc.com`) has no API key and returns 401: use `solana -u devnet ...` (public endpoint) or put a key in the URL. The public endpoint rate-limits (429); the adapter's confirmation poll treats a 429 as "not yet". Deploy: `solana -u devnet program deploy target/deploy/marketplace_settlement.so --program-id target/deploy/marketplace_settlement-keypair.json` (costs about 1.03 SOL of rent, refundable via `program close`). Explorer links need `?cluster=devnet`.
- Solana's status page covers Mainnet Beta only; check devnet with `solana -u devnet cluster-version` / `epoch-info`.
- Neon secrets are "sensitive" in Vercel: `vercel env pull` returns `[SENSITIVE]`, so the unpooled `DATABASE_URL` for `alembic upgrade head` has to be pasted by the user. Migrations against the production database, devnet/mainnet deploys, and `git push` (which deploys both projects) should be done only when the user asks.
- Stop the local database with `docker compose stop` when finished. Kill a leftover validator with `pkill -f '^solana-test-validator'` (a looser pattern also kills your own shell).

## Where the project stands (as of 2026-10-06)

- Phases 1-4 of the build guide are built; the Solana bridge (the "Phase 5" in the README) exists but runs on the `mock` provider in production and was deployed to devnet on 2026-10-06 (program `9ZZ5bejD4NdPr7zf9covKHDig6tcqh628Fdtrm4mT9MU`, upgrade authority = the default wallet `HfJkE5oAGDFGgvftcxcPXFCV5m6CfvM1hAPHZRv6kSsF`, 13/13 smoke checks pass there). Nothing in production points at it yet.
- The plan is staged: **Stage 1** make the audit trail real (retry fix, `smoke.py`, devnet deploy, queued sends via `process_queue` and the 6 LiteSVM tests are done; remaining: schedule the cron and switch production to `PAYMENT_PROVIDER=solana` with a keyed RPC URL and `SOLANA_AUTHORITY_KEYPAIR_JSON`, then watch a real order on the devnet explorer), **Stage 2** token escrow with a locked three-way split (farmer, transporter, platform), using the QuickNode `finance/escrow` Anchor-v1 example as the template and upgrading Anchor 0.30.1 to 1.2, **Stage 3** pooled transport (fundraiser-style target/deadline/refund), **Stage 4** hardening, paid RPC provider, multisig upgrade authority, audit.
- Open decisions are listed in `output/pdf/solana-integration-ideation-v2.pdf` and `output/pdf/market-feasibility-and-pitch.pdf` (fee level and who pays, who sets the transport price, auto-release when a buyer is silent, dispute resolver, token and currency ramp, first country). Transport is a real per-trip quote locked at commit, not a fixed number (published studies put it at 13.8-27.5% of market price).
- Planning PDFs in `output/pdf/`: `solana-integration-ideation.pdf` (v1 review), `solana-integration-ideation-v2.pdf`, `solana-devnet-testing-guide.pdf`, `solana-devnet-browser-check.pdf` (verify the deploy in the Solana Explorer), `market-feasibility-and-pitch.pdf`, `Colosseum_Project_Lessons_for_Farmer_Marketplace.pdf` (supplied). Pitch guidance already given: do not say the aim is to take users from other Colosseum winners; frame it as building on their rails.
- A `graphify-out/` knowledge graph exists; for questions about the codebase, check `graphify-out/GRAPH_REPORT.md` first.

## Conventions

Code follows a minimal style: shortcuts with a known ceiling are marked `# ponytail:` with the upgrade path (for example, the cron batch in `process_queue` is one pass per tick).
