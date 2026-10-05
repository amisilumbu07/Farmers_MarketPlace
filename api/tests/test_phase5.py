import json

import httpx
import pytest
from solders.keypair import Keypair

from api.app.payments import service
from api.app.payments.base import MockPaymentProvider
from api.app.payments.solana_adapter import STATUS_OFFSET, SolanaPaymentProvider, discriminator, order_hash
from api.app.shared.store import ExternalTransaction, Order
from api.app.orders.service import advance
from api.tests.test_phase1 import db  # noqa: F401  (fixture)
from api.tests.test_phase4 import BUYER, FARMER_2, TRANSPORTER, deliver_pooled


class FlakyProvider(MockPaymentProvider):
    fail = True

    def attest(self, order_id, attestation_hash, seq=None):
        if self.fail:
            raise RuntimeError("rpc down")
        return super().attest(order_id, attestation_hash)


@pytest.fixture
def provider(monkeypatch):
    p = FlakyProvider()
    monkeypatch.setattr(service, "_provider", p)
    return p


def rows(session, order_id):
    return {(r.purpose, r.status) for r in session.query(ExternalTransaction).filter_by(order_id=order_id)}


def test_chain_failure_never_blocks_orders_and_retry_recovers(db, provider):  # noqa: F811
    session, _ = db
    service.enqueue(session, "ord_demo_pool_2", "order", "commit", amount=100)  # seeded orders skip the ACCEPTED event
    order = deliver_pooled(session)
    advance(session, order, BUYER, "COMPLETED")
    assert order.status == "COMPLETED"
    assert ("attestation", "FAILED") in rows(session, order.id)
    provider.fail = False
    service.retry_failed(session)
    assert {s for _, s in rows(session, order.id)} == {"CONFIRMED"}
    assert provider.status[order.id] == "COMPLETED"
    assert len(service.retry_failed(session)) == 0


def test_solana_adapter_encodes_anchor_calls():
    sent, state = [], {"account": None}

    def rpc(request):
        body = json.loads(request.content)
        method = body["method"]
        result = {"getLatestBlockhash": {"value": {"blockhash": "11111111111111111111111111111111"}}, "sendTransaction": "sig1", "getSignatureStatuses": {"value": [{"err": None, "confirmationStatus": "confirmed"}]}, "getAccountInfo": {"value": state["account"]}}[method]
        if method == "sendTransaction":
            sent.append(body["params"][0])
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": 1, "result": result})

    provider = SolanaPaymentProvider("http://x", Keypair(), str(Keypair().pubkey()), httpx.Client(transport=httpx.MockTransport(rpc)))
    assert provider.create_payment("ord_1", 1250) == "sig1"
    import base64

    raw = base64.b64decode(sent[0])
    assert discriminator("commit_order") + order_hash("ord_1") + (1250).to_bytes(8, "little") in raw
    state["account"] = {"data": [base64.b64encode(bytes(STATUS_OFFSET) + b"\x01").decode(), "base64"]}
    assert provider.get_status("ord_1") == "COMPLETED"
    assert provider.create_payment("ord_1", 1250) == "existing"  # idempotent retry


def chain_account(status=0, count=0):
    import base64

    return {"data": [base64.b64encode(bytes(STATUS_OFFSET) + bytes([status]) + count.to_bytes(4, "little") + bytes(33)).decode(), "base64"]}


def retrying_provider(account):
    """Provider over a fake RPC; `account` is the on-chain record it sees. Returns (provider, list of sent transactions)."""
    sent = []

    def rpc(request):
        body = json.loads(request.content)
        method = body["method"]
        result = {"getLatestBlockhash": {"value": {"blockhash": "11111111111111111111111111111111"}}, "sendTransaction": "sig1", "getSignatureStatuses": {"value": [{"err": None, "confirmationStatus": "confirmed"}]}, "getAccountInfo": {"value": account}}[method]
        if method == "sendTransaction":
            sent.append(body["params"][0])
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": 1, "result": result})

    return SolanaPaymentProvider("http://x", Keypair(), str(Keypair().pubkey()), httpx.Client(transport=httpx.MockTransport(rpc))), sent


def test_attest_retry_never_appends_twice():
    h = b"\x07" * 32
    provider, sent = retrying_provider(chain_account(count=1))
    assert provider.attest("ord_1", h, seq=0) == "existing"  # already landed: nothing sent
    assert sent == []
    with pytest.raises(RuntimeError, match="earlier one has not landed"):
        provider.attest("ord_1", h, seq=3)
    assert provider.attest("ord_1", h, seq=1) == "sig1"  # its turn: sent with its position
    import base64

    assert discriminator("record_attestation") + h + (1).to_bytes(4, "little") in base64.b64decode(sent[0])


def test_settle_retry_is_idempotent_and_conflicts_surface():
    provider, sent = retrying_provider(chain_account(status=1))  # already COMPLETED
    assert provider.capture("ord_1") == "existing"
    with pytest.raises(RuntimeError, match="COMPLETED on chain, cannot become REFUNDED"):
        provider.refund("ord_1")
    assert sent == []
    provider, sent = retrying_provider(chain_account(status=0))
    assert provider.refund("ord_1") == "sig1" and len(sent) == 1
