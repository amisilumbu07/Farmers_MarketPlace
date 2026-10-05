"""Talks to blockchain/solana/programs/marketplace-settlement over plain JSON-RPC. Hand-encoded Anchor calls, no Anchor/Rust here."""
import base64
import hashlib
import json
import struct
import time

import httpx
from solders.hash import Hash
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import ID as SYSTEM_PROGRAM
from solders.transaction import Transaction

STATUS_OFFSET = 8 + 32 + 32 + 8  # discriminator + authority + order_hash + amount_minor
COUNT_OFFSET = STATUS_OFFSET + 1  # u32 little-endian: how many attestations the chain holds
STATUS_NAMES = {0: "COMMITTED", 1: "COMPLETED", 2: "REFUNDED"}


def order_hash(order_id: str) -> bytes:
    return hashlib.sha256(order_id.encode()).digest()


def discriminator(name: str) -> bytes:
    return hashlib.sha256(f"global:{name}".encode()).digest()[:8]


class SolanaPaymentProvider:
    name = "solana"

    def __init__(self, rpc_url: str, keypair: Keypair, program_id: str, client: httpx.Client | None = None):
        self.rpc_url, self.authority, self.program = rpc_url, keypair, Pubkey.from_string(program_id)
        self.http = client or httpx.Client(timeout=20)

    @classmethod
    def from_env(cls, env) -> "SolanaPaymentProvider":
        raw = env.get("SOLANA_AUTHORITY_KEYPAIR_JSON") or open(env["SOLANA_AUTHORITY_KEYPAIR"]).read()  # env secret on Vercel, file locally
        keypair = Keypair.from_bytes(bytes(json.loads(raw)))
        return cls(env.get("SOLANA_RPC_URL", "http://127.0.0.1:8899"), keypair, env["SOLANA_PROGRAM_ID"])

    def _rpc(self, method: str, *params):
        body = self.http.post(self.rpc_url, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": list(params)}).json()
        if "error" in body:
            raise RuntimeError(f"{method}: {body['error']}")
        return body["result"]

    def _settlement(self, order_id: str) -> Pubkey:
        return Pubkey.find_program_address([b"settlement", order_hash(order_id)], self.program)[0]

    def _send(self, order_id: str, name: str, args: bytes, creates: bool = False) -> str:
        meta = AccountMeta(self._settlement(order_id), is_signer=False, is_writable=True)
        authority = AccountMeta(self.authority.pubkey(), is_signer=True, is_writable=creates)
        accounts = [meta, authority] + ([AccountMeta(SYSTEM_PROGRAM, False, False)] if creates else [])
        blockhash = Hash.from_string(self._rpc("getLatestBlockhash", {"commitment": "confirmed"})["value"]["blockhash"])
        tx = Transaction.new_signed_with_payer([Instruction(self.program, discriminator(name) + args, accounts)], self.authority.pubkey(), [self.authority], blockhash)
        signature = self._rpc("sendTransaction", base64.b64encode(bytes(tx)).decode(), {"encoding": "base64", "preflightCommitment": "confirmed"})
        for _ in range(30):  # ponytail: ~30 s poll; move to websocket/async worker when sends leave the request path
            try:
                status = (self._rpc("getSignatureStatuses", [signature])["value"] or [None])[0]
            except RuntimeError as error:
                if "429" not in str(error):  # public RPCs rate-limit polling; treat as "not yet"
                    raise
                status = None
            if status and status["err"]:
                raise RuntimeError(f"{name} failed on chain: {status['err']}")
            if status and status["confirmationStatus"] in ("confirmed", "finalized"):
                return signature
            time.sleep(1)
        raise TimeoutError(f"{name} not confirmed: {signature}")

    def create_payment(self, order_id, amount_minor):
        if self.get_status(order_id) != "UNKNOWN":  # a retry after a lost response must not fail on "account already in use"
            return "existing"
        return self._send(order_id, "commit_order", order_hash(order_id) + struct.pack("<Q", amount_minor), creates=True)

    def attest(self, order_id, attestation_hash, seq=None):
        """`seq` is this hash's position in the order's evidence chain. The chain is read first, so a retry after a lost
        reply is a no-op; the program also enforces the position, so a race cannot append twice."""
        data = self._account(order_id)
        if data is None:
            raise RuntimeError(f"order {order_id} is not on chain")
        count = struct.unpack_from("<I", data, COUNT_OFFSET)[0]
        seq = count if seq is None else seq
        if count > seq:
            return "existing"
        if count < seq:
            raise RuntimeError(f"attestation {seq} is ahead of the chain ({count}); an earlier one has not landed")
        return self._send(order_id, "record_attestation", attestation_hash + struct.pack("<I", seq))

    def _settle(self, order_id: str, outcome: int) -> str:
        target, status = STATUS_NAMES[outcome], self.get_status(order_id)
        if status == target:
            return "existing"
        if status != "COMMITTED":
            raise RuntimeError(f"order is {status} on chain, cannot become {target}")
        try:
            return self._send(order_id, "settle", bytes([outcome]))
        except RuntimeError:
            if self.get_status(order_id) == target:  # the first attempt landed after all
                return "existing"
            raise

    def capture(self, order_id):
        return self._settle(order_id, 1)

    def refund(self, order_id):
        return self._settle(order_id, 2)

    def _account(self, order_id) -> bytes | None:
        value = self._rpc("getAccountInfo", str(self._settlement(order_id)), {"encoding": "base64", "commitment": "confirmed"})["value"]
        return base64.b64decode(value["data"][0]) if value else None

    def get_status(self, order_id):
        data = self._account(order_id)
        return STATUS_NAMES[data[STATUS_OFFSET]] if data else "UNKNOWN"
