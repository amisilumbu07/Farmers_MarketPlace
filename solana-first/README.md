# Farmer Marketplace — Solana-first draft

This directory is a clean architecture draft for rebuilding the marketplace with Solana as the settlement and shared-trust core.

It is intentionally separate from the current PostgreSQL-first application. The current app remains the working reference implementation; this directory defines the next architecture before code is migrated.

## Core decision

Solana owns shared financial and trust state:

- order commitments and escrow state;
- farmer/buyer settlement obligations;
- delivery and quality attestation hashes;
- dispute outcomes;
- compact reputation checkpoints.

The chain does **not** own personal data, private farm coordinates, product search, photos, chat, routing, or large documents.

```text
Next.js + Solana wallet
          │
          ▼
Solana program ─────── token escrow, order state, attestations
          │
          ├── indexer/read model ── PostgreSQL/PostGIS
          │                         private data, search, maps
          │
          └── API/services ──────── matching, routing, notifications
```

## Draft layout

```text
solana-first/
├── README.md
├── docs/
│   ├── architecture.md
│   └── implementation-plan.md
├── programs/
│   └── marketplace-core/       # Anchor program; planned replacement for settlement-only program
├── apps/
│   └── web/                    # Next.js + @solana/kit + wallet standard
├── services/
│   ├── api/                    # FastAPI orchestration and private-data API
│   └── indexer/                # Chain events → PostgreSQL read model
├── packages/
│   ├── idl/                    # Generated program IDL and typed client
│   └── domain/                 # Shared status/types; no provider SDK imports
└── tests/
    ├── program/                # LiteSVM/Mollusk unit tests
    └── integration/            # Surfpool end-to-end tests
```

## First implementation rule

Do not migrate the whole existing system at once. Prove one vertical slice first:

```text
buyer connects wallet
→ creates a request off-chain
→ receives an allocated order plan
→ signs a Solana commitment/escrow transaction
→ farmer accepts
→ delivery attestation is recorded
→ buyer releases or disputes settlement
→ indexer updates the application read model
```

See [docs/architecture.md](docs/architecture.md) and [docs/implementation-plan.md](docs/implementation-plan.md).

