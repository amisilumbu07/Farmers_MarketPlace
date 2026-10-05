"""End-to-end check of the settlement program on any cluster (local validator or devnet), through the same adapter the API uses.

    SOLANA_RPC_URL=http://127.0.0.1:8899 SOLANA_PROGRAM_ID=<id> SOLANA_AUTHORITY_KEYPAIR=<file> python blockchain/solana/scripts/smoke.py

Needs a funded authority keypair. Exits non-zero on the first failed check."""
import hashlib
import os
import struct
import sys
import time
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from api.app.payments.solana_adapter import SolanaPaymentProvider  # noqa: E402

RPC = os.getenv("SOLANA_RPC_URL", "http://127.0.0.1:8899")
env = {"SOLANA_RPC_URL": RPC, "SOLANA_PROGRAM_ID": os.getenv("SOLANA_PROGRAM_ID", "9ZZ5bejD4NdPr7zf9covKHDig6tcqh628Fdtrm4mT9MU"),
       "SOLANA_AUTHORITY_KEYPAIR": os.getenv("SOLANA_AUTHORITY_KEYPAIR", str(Path.home() / ".config/solana/id.json"))}
chain = SolanaPaymentProvider.from_env(env)
order = f"smoke_{int(time.time())}"
h = [hashlib.sha256(f"evidence-{i}".encode()).digest() for i in range(2)]


def link(sig: str) -> str:
    cluster = "cluster=devnet" if "devnet" in RPC else f"cluster=custom&customUrl={quote(RPC, safe='')}"
    return f"https://explorer.solana.com/tx/{sig}?{cluster}"


def step(label: str, got, want=None):
    ok = want is None or got == want
    print(f"{'PASS' if ok else 'FAIL'}  {label}: {link(got) if isinstance(got, str) and len(got) > 40 else got}")
    if not ok:
        sys.exit(f"expected {want!r}")


def refused(label: str, call, code: str):
    try:
        call()
    except RuntimeError as error:
        step(f"{label} (refused with {code})", code in str(error), True)
    else:
        sys.exit(f"FAIL  {label}: the program accepted it")


print(f"cluster {RPC}\nprogram {chain.program}\nauthority {chain.authority.pubkey()}\norder {order}\norder account {chain._settlement(order)}\n")
if chain._rpc("getAccountInfo", str(chain.program), {"encoding": "base64"})["value"] is None:
    sys.exit(f"STOP  program {chain.program} is not deployed on {RPC}.\n  Local: restart the validator with --bpf-program {chain.program} <path to the .so>.\n  Devnet: run the deploy step first.")
if chain._rpc("getBalance", str(chain.authority.pubkey()), {"commitment": "confirmed"})["value"] == 0:
    sys.exit(f"STOP  the authority {chain.authority.pubkey()} has no SOL on {RPC}.\n  Is SOLANA_AUTHORITY_KEYPAIR set on the same line as the command? Fund it: solana -u <cluster> airdrop 5 {chain.authority.pubkey()}")
step("order not on chain yet", chain.get_status(order), "UNKNOWN")
step("commit_order", chain.create_payment(order, 1250))
step("status after commit", chain.get_status(order), "COMMITTED")
step("commit again is a no-op", chain.create_payment(order, 1250), "existing")
step("attestation 0", chain.attest(order, h[0], 0))
step("attestation 0 retried is a no-op", chain.attest(order, h[0], 0), "existing")
step("attestation 1", chain.attest(order, h[1], 1))
refused("attestation at a taken position, sent raw", lambda: chain._send(order, "record_attestation", h[0] + struct.pack("<I", 0)), "0x1772")  # UnexpectedCount (6002)
step("capture", chain.capture(order))
step("status after capture", chain.get_status(order), "COMPLETED")
step("capture again is a no-op", chain.capture(order), "existing")
refused("refund after capture", lambda: chain.refund(order), "cannot become REFUNDED")
refused("attestation after settlement, sent raw", lambda: chain._send(order, "record_attestation", h[0] + struct.pack("<I", 2)), "0x1770")  # AlreadySettled (6000)
print("\nall checks passed")
