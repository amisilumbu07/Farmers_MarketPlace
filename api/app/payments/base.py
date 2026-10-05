"""The only payment/ledger surface the marketplace knows. Providers: mock (default), solana; fiat/x402 later.
`payment_id` is the order id: every provider derives its own account/reference from it."""
from typing import Protocol


class PaymentProvider(Protocol):
    name: str

    def create_payment(self, order_id: str, amount_minor: int) -> str: ...
    def attest(self, order_id: str, attestation_hash: bytes, seq: int | None = None) -> str: ...  # seq = position in the order's evidence chain
    def capture(self, order_id: str) -> str: ...
    def refund(self, order_id: str) -> str: ...
    def get_status(self, order_id: str) -> str: ...  # COMMITTED / COMPLETED / REFUNDED / UNKNOWN


class MockPaymentProvider:
    name = "mock"

    def __init__(self):
        self.status: dict[str, str] = {}
        self.calls = 0

    def _tx(self) -> str:
        self.calls += 1
        return f"mock_{self.calls}"

    def create_payment(self, order_id, amount_minor):
        self.status[order_id] = "COMMITTED"
        return self._tx()

    def attest(self, order_id, attestation_hash, seq=None):
        return self._tx()

    def capture(self, order_id):
        self.status[order_id] = "COMPLETED"
        return self._tx()

    def refund(self, order_id):
        self.status[order_id] = "REFUNDED"
        return self._tx()

    def get_status(self, order_id):
        return self.status.get(order_id, "UNKNOWN")
