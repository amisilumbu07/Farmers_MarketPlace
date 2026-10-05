from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib import colors

S = getSampleStyleSheet()
ROWS = [
    ("Account", "A piece of on-chain storage. Programs hold no data themselves; data lives in accounts the program owns."),
    ("PDA (Program Derived Address)", "An account address computed from seeds + the program id. Ours: seeds [\"settlement\", sha256(order id)], so every order has exactly one predictable record and no one holds its private key."),
    ("Instruction", "One call into the program. We have three: commit_order, record_attestation, settle."),
    ("Signer", "An account that signed the transaction. Only the marketplace authority key may change a record (Anchor's has_one = authority)."),
    ("Transaction & fee", "Instructions are sent in a signed transaction. The authority pays the fee and the one-time rent for the new account."),
    ("Hash", "Only 32-byte fingerprints go on chain. Names, photos and locations stay in the database, but anyone can check them against the hash."),
]
FLOW = [
    ("1. Order accepted", "commit_order creates the order's PDA: order hash, amount (minor units), status COMMITTED."),
    ("2. Each delivery step", "record_attestation: chain = sha256(chain + new hash). Order and content of the evidence become tamper-evident; count goes up."),
    ("3. Completed / refunded", "settle sets status COMPLETED (1) or REFUNDED (2). After this the program rejects every further change."),
]
GUARDS = ["PDA seeds + bump are re-checked on every call, so a fake account is rejected.", "has_one = authority: wrong signer fails.", "require! status == COMMITTED: no changes after settlement, no double settle.", "Outcome must be 1 or 2.", "Creating the same order twice fails (the account already exists)."]


def table(rows):
    t = Table([[Paragraph(f"<b>{a}</b>", S["BodyText"]), Paragraph(b, S["BodyText"])] for a, b in rows], colWidths=[130, 345])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey), ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F5F8F3"))]))
    return t


def p(text, style="BodyText"):
    return Paragraph(text, S[style])


doc = SimpleDocTemplate(str(Path(__file__).resolve().parents[1] / "output/pdf/solana-settlement-explained.pdf"), pagesize=A4, title="Solana settlement explained")
doc.build([
    p("What the Solana code does", "Title"),
    p("The marketplace works without Solana. The Solana program is a shared, public notebook where each order's key facts are written once and cannot be quietly edited. It does not hold money in this version."),
    Spacer(1, 10), p("Basic Solana ideas used", "Heading2"), table(ROWS),
    Spacer(1, 10), p("Life of an order on chain", "Heading2"), table(FLOW),
    Spacer(1, 10), p("What the program refuses (its validation)", "Heading2"),
    *[p(f"&bull; {g}") for g in GUARDS],
    Spacer(1, 10), p("Where the code lives", "Heading2"),
    p("<b>blockchain/solana/programs/marketplace-settlement/src/lib.rs</b> - the Anchor program (Rust).<br/><b>api/app/payments/solana_adapter.py</b> - Python client that builds and sends the transactions.<br/><b>api/app/payments/service.py</b> - listens to order events; failed chain calls are saved as FAILED and retried, never blocking an order."),
])
