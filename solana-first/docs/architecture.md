# Solana-first architecture

## 1. What changes from the current system

The current implementation treats PostgreSQL as the source of truth and Solana as an external payment/attestation adapter. A Solana-first implementation reverses only the shared-trust boundary:

| Concern | Solana-first owner | Why |
|---|---|---|
| Escrow and settlement status | Solana program account | Shared, verifiable, tamper-resistant state |
| Payment token movement | Solana Token/Token-2022 CPI | Atomic settlement and refund rules |
| Order commitment | Solana PDA | Stable commitment hash without private data |
| Delivery evidence | Hashes in program state/events | Evidence can be verified without storing files on-chain |
| Product search and matching | PostgreSQL/PostGIS service | Fast filtering, private fields, flexible queries |
| Farm coordinates and documents | PostgreSQL/object storage | Avoid public, permanent personal data |
| Notifications and routing | API/background services | External systems are not program state |
| UI read model | Indexer-backed API | The frontend should not rebuild business state from raw RPC calls |

Solana is the authority for settlement. PostgreSQL is the authority for operational search and private data.

## 2. Program accounts and PDA plan

Use deterministic seeds and keep account ownership explicit. Never put email addresses, phone numbers, exact private coordinates, or document contents in accounts.

```text
marketplace_config
  seeds: ["config"]

merchant_profile
  seeds: ["merchant", wallet]

produce_offer
  seeds: ["offer", farmer_wallet, offer_id]

buyer_request_commitment
  seeds: ["request", buyer_wallet, request_id]

order_escrow
  seeds: ["order", order_id]

attestation_chain
  seeds: ["attestation", order_id]

dispute
  seeds: ["dispute", order_id, dispute_id]
```

The current database identifiers can be hashed into fixed-size IDs. The chain should never trust an arbitrary client-provided order ID without validating the PDA derivation and authority.

## 3. Minimal program state

```text
Config
  authority, accepted_mint, fee_bps, paused, bump

MerchantProfile
  wallet, role, profile_commitment, active, bump

ProduceOffer
  farmer, product_commitment, quantity_units, price_minor, status, bump

OrderEscrow
  buyer, farmer, order_hash, quantity_units, amount_minor,
  token_mint, escrow_vault, status, created_slot, bump

AttestationChain
  order, count, rolling_hash, last_actor, bump

Dispute
  order, opened_by, evidence_hash, resolution, resolver, bump
```

Keep the state machine on-chain and reject invalid transitions in the program:

```text
COMMITTED → ACCEPTED → READY → IN_TRANSIT → DELIVERED → COMPLETED
     └──────────────→ CANCELLED
     └──────────────→ DISPUTED → COMPLETED | REFUNDED
```

## 4. Instructions

The first program should expose only the smallest complete set:

```text
initialize_config
register_merchant
create_offer
create_order_escrow
accept_order
record_attestation
mark_ready
mark_in_transit
mark_delivered
release_payment
cancel_order
open_dispute
resolve_dispute
```

Every instruction must define:

- required signers;
- writable accounts;
- expected account owners;
- token mint and vault constraints;
- allowed previous status;
- whether it can be retried safely.

## 5. Transaction flow

The buyer does not sign an opaque transaction. The UI displays the cluster, token, amount, recipient/escrow PDA, fee payer, and expected state change before requesting a signature.

```text
1. API creates a private request and deterministic order plan.
2. API returns the order hash and transaction message.
3. Wallet simulates and signs the v1 transaction.
4. Solana program creates escrow and commits the order.
5. Indexer confirms ownership, discriminator, status, and signature.
6. API exposes the indexed state to buyer/farmer dashboards.
```

Use `@solana/kit` with transaction version 1 for new clients. Check wallet support and fall back only when required. Every read that can encounter versioned transactions must request support for the version being used.

## 6. Indexer and consistency

The indexer is not allowed to invent business state. It consumes confirmed program events/accounts, validates the program ID and account discriminator, then upserts a projection.

```text
Solana RPC/WebSocket
        ↓
validated event consumer
        ↓
idempotent event cursor
        ↓
PostgreSQL projection
        ↓
FastAPI read API / Next.js UI
```

Required indexer fields:

```text
signature, slot, block_time, program_id, account_address,
event_type, event_hash, processed_at
```

The indexer must tolerate duplicate delivery, RPC gaps, replays, and temporary provider outages. Keep a reconciliation job that compares recent chain state with the read model.

## 7. Token and privacy rules

- Use a configured accepted mint; never accept a client-supplied mint without authority validation.
- Decide explicitly between SPL Token and Token-2022 before writing the escrow CPI.
- Store amounts in integer minor units on-chain.
- Keep raw buyer/farmer identities off-chain; link wallets through a private account mapping.
- Hash evidence with a canonical format before committing it.
- Never store private keys or seed phrases in the API, repository, or environment committed to Git.

