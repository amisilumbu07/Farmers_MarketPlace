# Solana-first implementation plan

## Phase A — Freeze the boundary

Deliverables:

- agree on the accepted token and devnet/localnet policy;
- define the on-chain state machine and PDA seeds;
- define the hash/canonicalization format;
- define which fields remain private/off-chain;
- write account and instruction diagrams.

Exit condition: a reviewer can explain who may sign every instruction and what happens if a transaction is retried.

## Phase B — Program skeleton

Build an Anchor program in `programs/marketplace-core` with no real funds first.

Implement:

1. config and authority checks;
2. order PDA creation;
3. status transitions;
4. attestation rolling hash;
5. dispute resolution;
6. custom errors and events.

Test with LiteSVM or Mollusk. Add negative tests for wrong signer, wrong PDA, wrong mint, invalid transition, duplicate settlement, and replayed instruction.

Exit condition: the program can run a complete mock order lifecycle without token transfers.

## Phase C — Token escrow on localnet/devnet

Add token accounts and CPI transfers only after the state machine is stable.

Implement:

- buyer deposits into the order vault;
- farmer cannot withdraw before the release rule;
- buyer can receive a refund only through the allowed cancellation/dispute path;
- authority fees are bounded and visible;
- all arithmetic uses checked integer operations.

Before any signature, show the transaction summary and simulate it. Use localnet/devnet only during development.

Exit condition: commit, accept, release, cancel, and refund are atomic and idempotent.

## Phase D — Typed web client and wallet UX

Add to a separate Next.js app:

- `@solana/kit` client with transaction version 1;
- Wallet Standard discovery through the Solana wallet plugin;
- supported-version check and fallback behavior;
- account loading with owner/discriminator validation;
- transaction simulation and readable error states;
- links to the correct cluster explorer.

Do not make wallet connection a replacement for application authentication. Use the wallet for authority and signatures; keep private profile/session data in the API.

## Phase E — Indexer/read model

Build `services/indexer` after the first program events exist.

Required behavior:

- consume confirmed events and account changes;
- persist a cursor and processed signature/event key;
- ignore data from unknown program IDs;
- validate account data before decoding;
- replay a slot range safely;
- reconcile indexed order status with chain state.

The existing PostgreSQL/PostGIS tables can become the first projection. Add chain columns instead of replacing private data tables:

```text
chain_order_address
chain_commit_signature
chain_status
chain_last_slot
chain_attestation_hash
```

## Phase F — Migrate one vertical slice

Run both systems for one feature only:

```text
create buyer request in API
→ match lots in PostGIS
→ create order plan
→ commit one order on Solana
→ farmer accepts through a signed instruction
→ record delivery hash
→ release/refund
→ project chain state into PostgreSQL
```

Do not migrate routing, analytics, admin moderation, or all historical orders yet.

Exit condition: a chain-confirmed order is visible in both buyer and farmer interfaces, and replaying indexer events does not duplicate rows.

## Phase G — Production hardening

- upgrade authority controls to multisig or a carefully governed authority;
- use a dedicated RPC provider with rate limits and failover;
- move chain writes to a queue/worker when request latency is measurable;
- add monitoring for failed transactions, stale cursors, escrow balance, and reconciliation gaps;
- audit all token CPIs and PDA constraints;
- publish program IDs and upgrade policy;
- use immutable deployment artifacts and environment-specific configuration.

## What should not move on-chain

Do not put these into Solana accounts:

- names, emails, phone numbers, or identity documents;
- exact farm locations when privacy matters;
- photos or delivery documents;
- product search indexes;
- route geometry and traffic data;
- chat and notification history;
- model prompts, raw AI output, or private business analytics.

## First three coding tasks

1. Replace the settlement-only program with `marketplace-core` account/instruction design, without token movement.
2. Add LiteSVM/Mollusk negative tests for authority and state transitions.
3. Add a minimal Kit wallet client that creates and simulates one localnet/devnet order commitment.

The existing FastAPI payment adapter should remain an adapter during this work. It should not be allowed to define the on-chain state machine.

