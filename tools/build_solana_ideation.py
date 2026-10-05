"""Builds output/pdf/solana-integration-ideation.pdf: review of the Solana code + plan, with diagrams."""
import math
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.utils import simpleSplit
from reportlab.platypus import Flowable, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

INK, GREEN, MUTED = colors.HexColor("#1F2A24"), colors.HexColor("#2F6B3A"), colors.HexColor("#5C6B62")
SOFT, BLUE, AMBER, RED, GRAY = (colors.HexColor(h) for h in ("#EAF3E6", "#DCE8F5", "#FBEBC8", "#F6D5D1", "#EFEFEA"))
W = 495  # usable width

S = getSampleStyleSheet()
BODY = ParagraphStyle("body", parent=S["BodyText"], fontSize=9.5, leading=13.5, textColor=INK)
SMALL = ParagraphStyle("small", parent=BODY, fontSize=8.3, leading=11)
H1 = ParagraphStyle("h1", parent=S["Heading1"], fontSize=19, leading=23, textColor=GREEN, spaceAfter=4)
H2 = ParagraphStyle("h2", parent=S["Heading2"], fontSize=13, leading=16, textColor=GREEN, spaceBefore=10, spaceAfter=4)
CAP = ParagraphStyle("cap", parent=BODY, fontSize=8, leading=10, textColor=MUTED, spaceAfter=6)


def p(text, style=BODY):
    return Paragraph(text, style)


# ---------- diagram toolkit ----------
class Diagram(Flowable):
    def __init__(self, h, draw):
        super().__init__()
        self.h, self.fn = h, draw

    def wrap(self, aw, ah):
        return W, self.h

    def draw(self):
        self.fn(self.canv)


def box(c, x, y, w, h, text, fill=SOFT, size=8.3, stroke=INK, align="center"):
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(0.8)
    c.roundRect(x, y, w, h, 5, fill=1, stroke=1)
    lines = []
    for i, para in enumerate(text.split("\n")):
        font = "Helvetica-Bold" if i == 0 else "Helvetica"
        lines += [(font, ln) for ln in simpleSplit(para, font, size, w - 10)]
    top = y + h / 2 + len(lines) * (size + 2) / 2 - size
    c.setFillColor(INK)
    for i, (font, ln) in enumerate(lines):
        c.setFont(font, size)
        ty = top - i * (size + 2)
        if align == "center":
            c.drawCentredString(x + w / 2, ty, ln)
        else:
            c.drawString(x + 6, ty, ln)


def text(c, x, y, s, size=8, bold=False, color=INK, center=False):
    c.setFillColor(color)
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    (c.drawCentredString if center else c.drawString)(x, y, s)


def arrow(c, x1, y1, x2, y2, label=None, color=INK, dash=False, size=7.5, label_dy=5):
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(1.2)
    c.setDash(3, 3) if dash else c.setDash()
    c.line(x1, y1, x2, y2)
    c.setDash()
    a = math.atan2(y2 - y1, x2 - x1)
    c.saveState()
    pth = c.beginPath()
    pth.moveTo(x2, y2)
    for wing in (0.4, -0.4):
        pth.lineTo(x2 - 8 * math.cos(a + wing), y2 - 8 * math.sin(a + wing))
    pth.close()
    c.drawPath(pth, fill=1, stroke=0)
    c.restoreState()
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2 + label_dy
        c.setFont("Helvetica", size)
        tw = c.stringWidth(label, "Helvetica", size)
        c.setFillColor(colors.white)
        c.rect(mx - tw / 2 - 2, my - 2, tw + 4, size + 3, fill=1, stroke=0)
        text(c, mx, my, label, size, color=color, center=True)


# ---------- diagrams ----------
def d_big_picture(c):
    text(c, 0, 328, "TODAY  -  the database is the boss, Solana is a notebook", 9.5, True, GREEN)
    box(c, 0, 255, 110, 55, "Browser\nbuyer / farmer")
    box(c, 190, 255, 130, 55, "FastAPI + Postgres\nsource of truth: orders, private data, search", SOFT)
    box(c, 385, 255, 110, 55, "Solana program\nnotebook: hashes + a status. No money.", BLUE)
    arrow(c, 110, 282, 190, 282, "HTTPS")
    arrow(c, 320, 282, 385, 282, "authority key signs")
    c.setStrokeColor(MUTED)
    c.setLineWidth(0.6)
    c.line(0, 232, W, 232)
    text(c, 0, 212, "THE PLAN  -  Solana holds the money and shared trust state, Postgres keeps everything else", 9.5, True, GREEN)
    box(c, 0, 125, 110, 55, "Browser + wallet\nbuyer signs the payment", SOFT)
    box(c, 190, 125, 130, 55, "Solana program\nescrow vault + order state machine", BLUE)
    box(c, 385, 125, 110, 55, "Indexer\ncopies chain events into the database", AMBER)
    box(c, 0, 20, 110, 55, "FastAPI\nmatching, routing, private data", SOFT)
    box(c, 385, 20, 110, 55, "Postgres / PostGIS\nread model + private data", SOFT)
    arrow(c, 110, 152, 190, 152, "signs deposit")
    arrow(c, 320, 152, 385, 152, "events")
    arrow(c, 440, 125, 440, 75, "writes rows")
    arrow(c, 55, 125, 55, 75, "orders, profiles")
    arrow(c, 385, 47, 110, 47, "reads / writes")
    text(c, 255, 100, "The API never holds user funds", 8, True, GREEN, center=True)
    text(c, 255, 88, "and cannot move them anywhere", 8, False, GREEN, center=True)
    text(c, 255, 76, "the program does not allow.", 8, False, GREEN, center=True)


def d_current_flow(c):
    text(c, 0, 283, "Marketplace event", 8.5, True, MUTED)
    text(c, 197, 283, "Saved to the queue", 8.5, True, MUTED)
    text(c, 345, 283, "Call on the Solana program", 8.5, True, MUTED)
    rows = [
        (225, "Farmer accepts the order\n(status ACCEPTED)", "commit_order\ncreates the order's record on chain"),
        (160, "Pickup / delivery steps\n(an attestation is created)", "record_attestation\nadds the evidence hash to the chain"),
        (95, "Buyer confirms, order is cancelled,\nor a dispute is resolved", "settle\nstatus becomes COMPLETED or REFUNDED"),
    ]
    for y, ev, call in rows:
        box(c, 0, y, 150, 48, ev, SOFT, 8)
        box(c, 197, y, 100, 48, "external_transactions\none row, unique key", AMBER, 7.5)
        box(c, 345, y, 150, 48, call, BLUE, 8)
        arrow(c, 150, y + 24, 197, y + 24)
        arrow(c, 297, y + 24, 345, y + 24)
    box(c, 0, 0, W, 62, "If Solana is down or slow\nThe row is saved as FAILED, the order carries on normally (the marketplace never waits on the chain), and the admin endpoint POST /admin/payments/retry replays failed rows in the order they were created: commit, then attest, then settle.", AMBER, 8)
    arrow(c, 247, 95, 247, 62, "on error", MUTED, dash=True)


def d_state_machine(c):
    text(c, 0, 196, "Order record on chain: it can only move forward, once", 9, True, GREEN)
    box(c, 10, 110, 130, 50, "COMMITTED\nstatus 0. Evidence can still be added.", SOFT)
    box(c, 340, 128, 150, 40, "COMPLETED\nstatus 1. Frozen forever.", colors.HexColor("#CFE6C8"))
    box(c, 340, 70, 150, 40, "REFUNDED\nstatus 2. Frozen forever.", RED)
    arrow(c, 140, 140, 340, 150, "settle(1): farmer is paid")
    arrow(c, 140, 130, 340, 92, "settle(2): buyer is refunded")
    text(c, 75, 98, "record_attestation keeps it COMMITTED", 7.5, color=MUTED, center=True)
    text(c, 75, 88, "and adds 1 to the evidence count", 7.5, color=MUTED, center=True)
    text(c, 0, 52, "Evidence chain: each new value is sha256(previous value + new hash)", 8.5, True, GREEN)
    xs = [0, 130, 260, 390]
    labels = ["start\n32 zero bytes", "after evidence A\nsha256(start + A)", "after evidence B\nsha256(previous + B)", "after evidence C\nsha256(previous + C)"]
    for x, lab in zip(xs, labels):
        box(c, x, 0, 105, 38, lab, BLUE, 7.5)
    for x in xs[:-1]:
        arrow(c, x + 105, 19, x + 130, 19)


def d_escrow(c):
    text(c, 0, 196, "Stage 2: money sits in a vault that only the program controls", 9, True, GREEN)
    box(c, 0, 95, 110, 52, "Buyer wallet\nholds the stablecoin", SOFT)
    box(c, 190, 95, 120, 52, "Escrow vault\nowned by the program, not by us", BLUE)
    box(c, 385, 140, 110, 45, "Farmer wallet\ngets the payment", colors.HexColor("#CFE6C8"))
    box(c, 385, 50, 110, 45, "Buyer wallet\ngets the refund", RED)
    arrow(c, 110, 121, 190, 121, "1  buyer signs deposit")
    arrow(c, 310, 130, 385, 160, "2a  delivery confirmed", label_dy=8)
    arrow(c, 310, 112, 385, 75, "2b  cancel / dispute", label_dy=-14)
    text(c, 0, 30, "The platform key can only press 'release' or 'refund'. It cannot choose another destination,", 8, color=MUTED)
    text(c, 0, 19, "so even a hacked server cannot send escrowed money to itself. That is the real protection stage 2 adds.", 8, color=MUTED)


def d_roadmap(c):
    cols = [
        ("STAGE 1", "Make the notebook real", GREEN,
         ["Fix retry double-writes", "Rust tests for the program", "Deploy to devnet", "Authority key in an env secret", "Send from a worker / cron, not the web request", "Turn on PAYMENT_PROVIDER=solana in staging"],
         "Done when: a full order shows a verifiable record on the devnet explorer."),
        ("STAGE 2", "Add real escrow", colors.HexColor("#3E7FB0"),
         ["Extend the same program with a vault", "Test stablecoin on devnet", "Wallet connect + signed deposit in Next.js", "Farmers add a payout wallet", "Release / refund rules enforced on chain"],
         "Done when: a buyer's money is locked and only released by the rules."),
        ("STAGE 3", "Harden and go live", colors.HexColor("#A5702A"),
         ["Indexer + reconciliation job", "Dispute resolution on chain", "Multisig upgrade authority", "Paid RPC provider + monitoring", "Independent security audit", "Mainnet launch"],
         "Done when: audited, monitored, and money has moved safely in pilot orders."),
    ]
    cw, gap = 155, 15
    for i, (tag, title, col, items, done) in enumerate(cols):
        x = i * (cw + gap)
        c.setFillColor(col)
        c.roundRect(x, 215, cw, 34, 5, fill=1, stroke=0)
        text(c, x + 8, 236, tag, 8, True, colors.white)
        text(c, x + 8, 224, title, 9, True, colors.white)
        c.setFillColor(colors.white)
        c.setStrokeColor(col)
        c.setLineWidth(1)
        c.roundRect(x, 20, cw, 190, 5, fill=1, stroke=1)
        yy = 196
        for it in items:
            for j, ln in enumerate(simpleSplit(it, "Helvetica", 8, cw - 22)):
                text(c, x + 8, yy, "-" if j == 0 else "", 8, color=col)
                text(c, x + 16, yy, ln, 8)
                yy -= 10.5
            yy -= 3
        c.setFillColor(SOFT)
        c.rect(x + 1, 21, cw - 2, 46, fill=1, stroke=0)
        for j, ln in enumerate(simpleSplit(done, "Helvetica-Bold", 7.6, cw - 14)):
            text(c, x + 7, 55 - j * 9.5, ln, 7.6, True, GREEN)
    box(c, 0, 0, 78, 16, "YOU ARE HERE", AMBER, 7)
    text(c, 86, 4, "(code exists and works against a fake RPC; nothing is deployed)", 7.5, color=MUTED)


# ---------- tables ----------
def table(rows, widths, header=True, fills=None):
    data = [[p(str(cell), SMALL) if not isinstance(cell, Flowable) else cell for cell in r] for r in rows]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C9D2CB")),
             ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), SOFT)]
    for r, f in (fills or {}).items():
        style.append(("BACKGROUND", (0, r), (0, r), f))
    t.setStyle(TableStyle(style))
    return t


def b(s):
    return f"<b>{s}</b>"


WORDS = [
    (b("Program"), "The code that runs on Solana (ours is written in Rust with the Anchor framework). Think of it as a tiny server nobody can secretly change."),
    (b("Account / PDA"), "Storage that belongs to a program. A PDA is an account whose address is calculated from a recipe (for us: the word 'settlement' plus a fingerprint of the order id), so every order has one predictable record."),
    (b("Hash"), "A 32-byte fingerprint of some data. We store the fingerprint on chain, not the photos or names, so privacy stays in our database but anyone can prove the data was not altered."),
    (b("Escrow"), "Money held by a neutral vault until agreed conditions are met. Today there is no escrow: the chain stores facts, not funds."),
]

FINDINGS = [
    ("#", "Finding", "Why it matters", "Fix"),
    ("1<br/>" + b("High"), b("The chain holds no money, and one platform key signs everything."), "Buyers and farmers still have to trust the platform. The chain is an audit log, not protection.", "Stage 2 escrow."),
    ("2<br/>" + b("High"), b("Retries can double-apply."), "If a transaction lands but the reply is lost (timeout), the row is marked FAILED and retry sends it again. A repeated attestation appends the same hash twice and changes the chain. A repeated settle fails with 'already settled' and stays FAILED forever. Only commit checks the chain first.", "Before resending, read the account (status, evidence count) and skip if already applied. Treat 'already settled' as success."),
    ("3<br/>" + b("High"), b("Not ready to run on Vercel."), "The authority key is read from a file path. Sends happen inside the web request and poll for up to about 20 seconds. The program id is a local-dev key. The payments code is not committed, so the live backend does not include it, and PAYMENT_PROVIDER defaults to mock.", "Key as an encrypted env secret. Send from a cron or worker. Deploy to devnet with a real program keypair."),
    ("4<br/>" + b("Medium"), b("No tests for the program itself."), "Only a Python test with a fake RPC exists. It proves the bytes are encoded as expected, not that the program rejects a wrong signer or double settle.", "LiteSVM tests: wrong signer, wrong PDA, double settle, bad outcome."),
    ("5<br/>" + b("Medium"), b("Amount built with possibly-float multiplication."), "The code computes int(quantity_kg * price_per_kg * 100). If those fields are floats, a cent can be lost, and this number becomes the on-chain amount. (I have not checked the column types.)", "Use integer cents or Decimal end to end."),
    ("6<br/>" + b("Medium"), b("The plan and the code disagree."), "Plan: seeds [order, id] and 13 instructions. Deployed program: seeds [settlement, hash] and 3 instructions. 'Replace the program' means a new program id and a data migration.", "Extend the current program with a vault instead of a parallel rewrite."),
    ("7<br/>" + b("Low"), b("The plan is big with open questions."), "Seven phases. Undecided: which token, SPL vs Token-2022, farmer wallets, who pays fees. On-chain offers and merchant profiles add cost for little benefit now.", "Answer the four questions on the last page. Skip offers and profiles."),
]
FILLS = {1: RED, 2: RED, 3: RED, 4: AMBER, 5: AMBER, 6: AMBER, 7: GRAY}

GOOD = ["Only hashes and a status go on chain, so no personal data is public or permanent.",
        "The program re-checks the order address, the signer and the status on every call, and refuses any change after settlement.",
        "A chain outage never blocks an order: failures are stored and retried in order.",
        "Each event has a unique key, so the same event is not queued twice.",
        "The payment interface is swappable (mock by default), so the marketplace does not depend on Solana."]


def build():
    out = Path(__file__).resolve().parents[1] / "output/pdf/solana-integration-ideation.pdf"
    doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=50, rightMargin=50, topMargin=46, bottomMargin=46, title="Solana integration - review and ideation")
    story = [
        p("Solana integration: review and ideation", H1),
        p("A plain-language review of the Solana code already in the project, the Solana-first plan, and how to bring them together.", CAP),
        p("The short answer", H2),
        p(f"{b('What exists:')} a small, working bridge. When an order is accepted, delivered or settled, the API writes a record to a Solana program: fingerprints and a status, no money. It has been tested only against a fake network connection, was never run on devnet, and is not active in your live site."),
        Spacer(1, 4),
        p(f"{b('What the plan proposes:')} a rebuild where Solana holds the money (escrow) and the shared trust state, buyers sign with wallets, and an indexer copies chain events into Postgres. So far it is documents only (<font face='Courier'>solana-first/</font> has no code)."),
        Spacer(1, 4),
        p(f"{b('Recommendation:')} do not rebuild. Grow the existing program in three stages: make the audit trail real, then add escrow, then harden for mainnet. Each stage is useful on its own, so you can stop after any of them."),
        p("Four words you need", H2),
        table([(a, c) for a, c in WORDS], [95, 400], header=False),
        p("The big picture: today versus the plan", H2),
        Diagram(335, d_big_picture),
        p("Figure 1. Boxes show who does what. Arrows show who talks to whom.", CAP),
        PageBreak(),
        p("How the current integration works", H1),
        p("Files: <font face='Courier'>api/app/payments/</font> (queue and Python client) and <font face='Courier'>blockchain/solana/programs/marketplace-settlement/</font> (the program). The marketplace announces order events; the payments module listens and mirrors them to Solana."),
        Spacer(1, 6),
        Diagram(300, d_current_flow),
        p("Figure 2. Three order events, three program calls. Every call goes through a saved queue row.", CAP),
        p("What the program remembers about each order", H2),
        p("Each order gets one record with: the platform authority, a fingerprint of the order id, the amount in cents, a status, how many pieces of evidence were added, and a rolling fingerprint of that evidence. Nothing else."),
        Spacer(1, 4),
        Diagram(210, d_state_machine),
        p("Figure 3. The status can move once, from COMMITTED to a final state. The evidence chain makes it impossible to edit or reorder earlier evidence without the later values changing.", CAP),
        PageBreak(),
        p("Review: what is good, and what to fix", H1),
        p("What is already solid", H2),
        *[p(f"&bull; {g}") for g in GOOD],
        p("What needs attention", H2),
        table(FINDINGS, [42, 120, 215, 118], fills=FILLS),
        p("Checked: the adapter test passes. The other test in the same file needs Postgres running and errored on this machine only for that reason. The program is built locally but has no Rust tests and was never deployed.", CAP),
        PageBreak(),
        p("The Solana-first plan: how it fits", H1),
        p("The plan (<font face='Courier'>solana-first/docs</font>) is sound in its main idea: <b>Solana owns settlement; Postgres owns private data, search and maps.</b> That matches what the code already does, plus one big addition: real escrow."),
        p("What the plan adds", H2),
        table([
            ("Piece", "What it does", "Verdict"),
            (b("Escrow vault"), "Program-owned account holds buyer funds until release or refund.", "<b>Do it</b> (stage 2). The main benefit."),
            (b("Wallet connect"), "Buyer signs the deposit in their own wallet. Wallet is for signatures, not for login.", "<b>Do it</b> (stage 2)."),
            (b("Indexer"), "Copies chain events into Postgres, with a job that checks the two agree.", "<b>Do it</b> (stage 3). Needed once users act on chain without the API."),
            (b("On-chain disputes"), "Resolver decides refund or release on chain.", "<b>Later</b> (stage 3). Keep it in the API until real volume."),
            (b("Offers and merchant profiles on chain"), "Product listings and profile commitments as accounts.", "<b>Skip.</b> Search and listings belong in Postgres."),
            (b("13 instructions, 7 account types"), "Full lifecycle on chain.", "<b>Grow gradually.</b> Add an instruction when a stage needs it."),
        ], [118, 235, 142]),
        Spacer(1, 8),
        p("What stage 2 looks like for money", H2),
        Diagram(210, d_escrow),
        p("Figure 4. Funds move only along the two allowed paths.", CAP),
        PageBreak(),
        p("Recommended path", H1),
        p("Keep the marketplace working exactly as it is, and add Solana in layers. After each stage the project is shippable."),
        Spacer(1, 6),
        Diagram(255, d_roadmap),
        p("Figure 5. Three stages. Stage 1 is small; stage 2 is the largest and the one that adds real protection.", CAP),
        p("Decisions I need from you", H2),
        table([
            ("Question", "Why it matters", "My suggestion"),
            (b("1. Do you want real money on chain, or only an audit trail?"), "Decides whether stage 2 happens at all.", "Start with the audit trail (stage 1) and decide with devnet results."),
            (b("2. Which payment token?"), "Escrow code depends on it. SPL vs Token-2022 must be chosen before writing it.", "A regulated stablecoin such as USDC with plain SPL Token. Test with a devnet copy first."),
            (b("3. Will farmers have wallets, and who pays network fees?"), "A farmer with no wallet cannot be paid on chain.", "Platform pays fees (fractions of a cent). Farmers add a payout wallet; start with a few pilot farmers."),
            (b("4. How do users turn local currency into the token and back?"), "Without an on/off ramp the escrow is unusable for real farmers.", "Pick a provider before stage 2. This is a business question, not a code one."),
        ], [165, 160, 170]),
        Spacer(1, 8),
        p(f"{b('Next step if you agree:')} I would start stage 1 with the retry fix and the program tests, since they are small and need no decisions from the list above."),
    ]
    doc.build(story)
    print(out)


if __name__ == "__main__":
    build()
