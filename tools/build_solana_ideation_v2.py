"""Builds output/pdf/solana-integration-ideation-v2.pdf: RPC decision, QuickNode repo comparison,
three-layer (farmer / transporter / buyer) model, fee design. Thinking phase: nothing here is built."""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.platypus import PageBreak, SimpleDocTemplate, Spacer

from build_solana_ideation import AMBER, BLUE, BODY, CAP, GRAY, GREEN, H1, H2, INK, MUTED, RED, SOFT, W, Diagram, arrow, b, box, p, table, text

DONE = colors.HexColor("#CFE6C8")
TEAL = colors.HexColor("#3E7FB0")
BROWN = colors.HexColor("#A5702A")


def wrap_lines(c, x, y, s, size, width, color=INK, bold=False, lead=None):
    """Draw wrapped text from (x, y) downward; returns the next free y."""
    font = "Helvetica-Bold" if bold else "Helvetica"
    for ln in simpleSplit(s, font, size, width):
        text(c, x, y, ln, size, bold, color)
        y -= lead or size + 2.2
    return y


# ---------------- diagrams ----------------
def d_rpc(c):
    text(c, 0, 280, "An RPC node is the doorway between our servers and the Solana network", 9, True, GREEN)
    box(c, 0, 205, 140, 55, "Our API / worker\nsends transactions and checks the result")
    box(c, 178, 205, 140, 55, "RPC node (any provider)\nchosen by ONE setting: SOLANA_RPC_URL", AMBER)
    box(c, 355, 205, 140, 55, "Solana network\ndevnet now, mainnet later", BLUE)
    arrow(c, 140, 232, 178, 232)
    arrow(c, 318, 232, 355, 232)
    box(c, 355, 140, 140, 42, "Buyer / farmer wallets\nbring their own connection", GRAY, 7.8)
    arrow(c, 425, 182, 425, 205, color=MUTED, dash=True)
    text(c, 0, 160, "Answer for today: no paid RPC needed yet.", 9.5, True, GREEN)
    text(c, 0, 147, "Switching providers later is a settings change, not a code change.", 8, color=MUTED)
    cards = [
        ("Stage 1: local + devnet", "No paid node. Program tests run in memory (LiteSVM), and devnet uses the free public endpoint.", SOFT, GREEN),
        ("Stage 2: devnet with wallets", "Still free. Expect rate limits; our retry queue already absorbs failed calls.", SOFT, GREEN),
        ("Stage 3: mainnet pilot", "DECIDE HERE. Paid provider with failover and websockets (the indexer needs them).", AMBER, BROWN),
    ]
    for i, (title, body, fill, edge) in enumerate(cards):
        box(c, i * 170, 20, 155, 100, f"{title}\n{body}", fill, 8, edge)


def d_compare(c):
    text(c, 0, 256, "Fit for our marketplace (my judgement, not a measurement)", 9, True, GREEN)
    rows = [
        ("escrow", 90, "BASE. Vault owned by the order account, cancel path, rent refund, guard against switched terms, LiteSVM + Kani tests."),
        ("fundraiser", 70, "BORROW for pooled transport: target, deadline, refund if the target is missed, anyone may close."),
        ("managed-fund", 50, "BORROW the fee rules: cap in basis points, fixed at creation, no setter to raise it, anyone may collect."),
        ("token-swap", 22, "Has an admin-fee claim. The trading math is not needed."),
        ("order-book", 10, "Matching engine. Our matching lives in Postgres/PostGIS."),
        ("lending", 5, "Interest and liquidation: a different problem."),
        ("betting-market, options,\nperpetual-futures, prop-amm", 3, "Financial-market products, unrelated to delivering goods."),
    ]
    y = 224
    for name, score, note in rows:
        col = GREEN if score >= 50 else colors.HexColor("#B5BEB7")
        for i, ln in enumerate(name.split("\n")):
            text(c, 0, y + 8 - i * 9, ln, 8, True)
        c.setFillColor(GRAY)
        c.rect(118, y + 4, 100, 12, fill=1, stroke=0)
        c.setFillColor(col)
        c.rect(118, y + 4, max(score, 3) * 1.0, 12, fill=1, stroke=0)
        wrap_lines(c, 228, y + 13, note, 7.4, 267, lead=8.6)
        y -= 36


def d_layers(c):
    bands = [
        (238, SOFT, "LAYER 1  -  FARMER (supply)", "Lists lots, accepts the order, hands goods to the transporter. Paid when delivery is confirmed: goods price minus the farmer fee.", "accepts terms"),
        (128, AMBER, "LAYER 2  -  TRANSPORTER (the middle)", "Collects from one or several farmers (pooling) and delivers to one or several buyers. Paid the transport price that was locked at commit.", "attests"),
        (18, BLUE, "LAYER 3  -  BUYER (demand)", "Deposits goods + transport + buyer fee in one signature. Confirms receipt, or gets the money back if the rules say so.", "deposits"),
    ]
    for y, fill, title, body, label in bands:
        c.setFillColor(fill)
        c.setStrokeColor(INK)
        c.setLineWidth(0.8)
        c.roundRect(0, y, 265, 86, 6, fill=1, stroke=1)
        text(c, 8, y + 71, title, 8.3, True)
        wrap_lines(c, 8, y + 57, body, 7.8, 249, lead=9.8)
        arrow(c, 265, y + 43, 330, y + 43, label, size=6.8)
    arrow(c, 132, 238, 132, 214, "goods", GREEN)
    arrow(c, 132, 128, 132, 104, "goods", GREEN)
    c.setFillColor(colors.white)
    c.setStrokeColor(INK)
    c.roundRect(320, 18, 175, 306, 6, fill=1, stroke=1)
    text(c, 407, 309, "Solana program (one order)", 8.3, True, center=True)
    box(c, 330, 252, 155, 50, "Locked terms\nprice, three-way split and fee cap, fixed at commit", SOFT, 7.6)
    box(c, 330, 145, 155, 56, "Attestation chain\nhashes of handover, pickup and delivery", BLUE, 7.6)
    box(c, 330, 62, 155, 46, "Escrow vault\nholds the deposit; only the program can move it", BLUE, 7.6)
    box(c, 330, 26, 155, 26, "Treasury: receives only the platform fee", AMBER, 7)
    arrow(c, 407, 62, 407, 52, color=MUTED)


def d_wins(c):
    cards = [
        ("Buyer wins", "Money is locked, not trusted to a stranger. Pooled delivery can cost less than a solo trip.", DONE),
        ("Farmer wins", "Sees the funds locked before shipping, so no chasing payment. Reaches more buyers.", DONE),
        ("Transporter wins", "Pay is locked for the trip. Pooling means fuller loads and fewer empty miles.", DONE),
        ("Platform wins", "A small capped fee, only on orders that complete. No float yield, no hidden cut.", AMBER),
    ]
    for i, (t, body, fill) in enumerate(cards):
        box(c, i * 126, 0, 117, 105, f"{t}\n{body}", fill, 7.8)


def d_swimlane(c):
    lanes = [("FARMER", 215, SOFT), ("TRANSPORTER", 130, AMBER), ("BUYER", 45, BLUE)]
    for name, y, fill in lanes:
        c.setFillColor(fill)
        c.setStrokeColor(colors.HexColor("#C9D2CB"))
        c.setLineWidth(0.5)
        c.rect(0, y, W, 75, fill=1, stroke=1)
        text(c, 4, y + 34, name, 7.2, True, MUTED)
    col = lambda i: 78 + i * 84  # noqa: E731
    steps = [  # (column, lane y, text)
        (0, 45, "1  Commit + deposit\nbuyer signs the exact split"),
        (1, 215, "2  Accept order\nfarmer signs the terms"),
        (2, 215, "3a  Hand over goods\nfarmer attests"),
        (2, 130, "3b  Pick up\ntransporter attests"),
        (3, 130, "4  Deliver\ntransporter attests"),
        (4, 45, "5  Confirm receipt\nthe split is released"),
    ]
    pos = {}
    for i, (cidx, y, label) in enumerate(steps):
        x = col(cidx)
        box(c, x, y + 10, 78, 55, label, colors.white, 7)
        pos[i] = (x, y + 10)
    for a, bb in [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)]:
        (x1, y1), (x2, y2) = pos[a], pos[bb]
        if abs(x1 - x2) < 1:  # same column: vertical
            arrow(c, x1 + 39, y1 if y2 < y1 else y1 + 55, x2 + 39, y2 + 55 if y2 < y1 else y2)
        elif abs(y1 - y2) < 1:
            arrow(c, x1 + 78, y1 + 27, x2, y2 + 27)
        else:
            arrow(c, x1 + 78, y1 + 27, x2, y2 + 27) if False else arrow(c, x1 + 78, y1 + 40 if y2 > y1 else y1 + 15, x2, y2 + 15 if y2 > y1 else y2 + 40)
    box(c, 0, 0, 160, 34, "No acceptance by the deadline\nBuyer reclaims everything", RED, 7)
    box(c, 168, 0, 160, 34, "Delivered but buyer is silent\nAuto-release after a set window?", AMBER, 7)
    box(c, 336, 0, 159, 34, "Problem reported\nResolver picks from fixed outcomes", AMBER, 7)


def d_split(c):
    text(c, 0, 172, "Buyer signs ONE deposit of 109.50 (example numbers, not a proposal)", 9, True, GREEN)
    total = 109.5
    parts = [(98.5, DONE, "Farmer 98.50"), (8.0, AMBER, ""), (3.0, TEAL, "")]
    x = 0
    seg = []
    for amt, col, lab in parts:
        w = amt / total * W
        c.setFillColor(col)
        c.setStrokeColor(INK)
        c.setLineWidth(0.8)
        c.rect(x, 115, w, 38, fill=1, stroke=1)
        seg.append((x, w))
        x += w
    text(c, seg[0][1] / 2, 130, "Farmer receives 98.50  (price 100.00 minus 1.50 farmer fee)", 8.3, True, center=True)
    box(c, 235, 40, 135, 45, "Transporter 8.00\nthe transport price, as agreed at commit", AMBER, 7.4)
    box(c, 385, 40, 110, 45, "Platform 3.00\n1.50 buyer fee + 1.50 farmer fee", colors.HexColor("#D5E4F1"), 7.4)
    arrow(c, seg[1][0] + seg[1][1] / 2, 115, 330, 85)
    arrow(c, seg[2][0] + seg[2][1] / 2, 115, 470, 85)
    text(c, 0, 92, "Buyer pays:", 8, True)
    text(c, 0, 80, "100.00 goods", 8)
    text(c, 0, 69, "+   8.00 transport", 8)
    text(c, 0, 58, "+   1.50 buyer fee", 8)
    text(c, 0, 47, "= 109.50 deposit", 8, True)
    text(c, 0, 20, "The program refuses the order unless the parts add up to the deposit, and the split can never change afterwards.", 8, color=MUTED)
    text(c, 0, 9, "Network fees (fractions of a cent) are sponsored by the platform out of its 3.00. Account rent is refunded when the order closes.", 8, color=MUTED)


def d_roadmap(c):
    cols = [
        ("STAGE 1", "Make the notebook real", GREEN, ["Fix retry double-writes", "Program tests (LiteSVM)", "Deploy to devnet", "Key as env secret", "Send from a worker"], "Done: a full order is visible on the devnet explorer."),
        ("STAGE 2", "Escrow + three-way split", TEAL, ["Use escrow (Anchor v1) as the template", "Upgrade Anchor 0.30 to 1.2", "Transporter becomes a signer", "Wallet connect + deposit", "Capped fee, locked per order"], "Done: money locked and split only by the rules."),
        ("STAGE 3", "Pooled transport", BROWN, ["Pool account from the fundraiser pattern", "Minimum load + deadline", "Refund if the trip does not fill", "Pooling savings shared fairly"], "Done: a pooled trip pays all parties or refunds all."),
        ("STAGE 4", "Harden + go live", colors.HexColor("#7A4E8C"), ["Indexer + reconciliation", "Pick the paid RPC provider", "Multisig upgrade authority", "Independent audit", "Mainnet pilot"], "Done: audited and monitored."),
    ]
    cw, gap = 115, 11.67
    for i, (tag, title, col, items, done) in enumerate(cols):
        x = i * (cw + gap)
        c.setFillColor(col)
        c.roundRect(x, 232, cw, 38, 5, fill=1, stroke=0)
        text(c, x + 6, 257, tag, 7.6, True, colors.white)
        for j, ln in enumerate(simpleSplit(title, "Helvetica-Bold", 8, cw - 12)):
            text(c, x + 6, 246 - j * 9, ln, 8, True, colors.white)
        c.setFillColor(colors.white)
        c.setStrokeColor(col)
        c.setLineWidth(1)
        c.roundRect(x, 18, cw, 208, 5, fill=1, stroke=1)
        yy = 211
        for it in items:
            for j, ln in enumerate(simpleSplit(it, "Helvetica", 7.4, cw - 20)):
                text(c, x + 6, yy, "-" if j == 0 else "", 7.4, color=col)
                text(c, x + 13, yy, ln, 7.4)
                yy -= 9.4
            yy -= 3
        c.setFillColor(SOFT)
        c.rect(x + 1, 19, cw - 2, 50, fill=1, stroke=0)
        yy = 58
        for ln in simpleSplit(done, "Helvetica-Bold", 7.2, cw - 12):
            text(c, x + 6, yy, ln, 7.2, True, GREEN)
            yy -= 9
    box(c, 0, 0, 78, 14, "YOU ARE HERE", AMBER, 6.5)
    text(c, 84, 4, "(before stage 1; nothing below is built)", 7.5, color=MUTED)


# ---------------- content ----------------
VARIANTS = [
    ("Copy in the repo", "What it is", "For us"),
    (b("anchor-v1"), "Anchor 1.2.0, which its README calls the current stable release.", b("Use this.") + " Same framework family as our code (ours is 0.30.1, so one upgrade step)."),
    (b("anchor (v2)"), "Anchor 2.0.0-rc.1: a release candidate.", "Avoid for code that holds money until it is final."),
    (b("native"), "No framework; everything by hand.", "More code and more mistakes, no benefit for us."),
    (b("quasar"), "A different framework.", "Would mean learning a new toolchain. Not now."),
    (b("kani-proofs"), "Model-checks the arithmetic for every input, not just test cases.", "Copy the idea for our split: total in equals total out."),
]

FEES = [
    ("Option", "Who pays", "Good", "Risk", "Verdict"),
    (b("A. Buyer service fee"), "Buyer", "Simple and visible.", "Raises the buyer's price.", b("Use") + ", small."),
    (b("B. Farmer commission"), "Farmer", "Buyer's price stays flat.", "Farmers may trade outside the platform if it is high.", b("Use") + ", small."),
    (b("C. Pooling success fee"), "Taken from realised savings", "Platform earns only when pooling actually saves money.", "Needs an honest price for the solo trip to measure against.", b("Stage 3.")),
    (b("D. Sponsor network fees"), "Platform, from A and B", "Users never need to hold SOL.", "Costs are tiny but real.", b("Use.")),
    (b("E. Dispute fee or bond"), "Losing party", "Pays for the resolver.", "Adds complexity.", b("Later.")),
    (b("F. Paid extras"), "Whoever buys them", "Quality checks, analytics: off-chain, no custody.", "Needs customers.", b("Later.")),
    (b("G. Earn yield on escrowed money"), "Nobody agreed", "Looks like free money.", "It uses people's funds; they could be locked or lost.", b("Never.")),
]

RULES = [
    ("Rule", "How the program enforces it", "Copied from"),
    ("1. The split is locked", "Buyer signs exact amounts. The program checks the parts add up to the deposit with checked arithmetic, and no instruction can change them later.", "escrow tests + Kani idea"),
    ("2. The fee has a ceiling", "A maximum (for example 5%) lives in the code. Each order stores its own fee, so a later change cannot touch open orders. No setter raises the cap.", "managed-fund"),
    ("3. Payout addresses are pinned", "Farmer, transporter and treasury accounts are fixed at commit. The platform key can only press 'release' or 'refund', never choose a destination.", "escrow account constraints"),
    ("4. Terms cannot be switched", "Accepting signs a hash of the terms, so an order cancelled and recreated with worse terms is refused.", "escrow bait-and-switch guard"),
    ("5. Deadline refund", "If the order is not completed by its deadline, the buyer can reclaim without the platform's help.", "fundraiser refund"),
    ("6. Fees go only to the treasury", "Anyone may trigger the fee collection, but the destination is fixed, so triggering it earns nothing.", "managed-fund collect_fees"),
    ("7. Resolver is boxed in", "A dispute can only end as: release, refund, or the pre-agreed split among the same three parties. Never to a new address.", "new design"),
    ("8. The program cannot be swapped", "Upgrade authority goes to a multisig, then time-locked or frozen. Without this, 'no stealing' is only a promise, because the owner could ship a new program.", "plan, phase G"),
]

INSTR = [
    ("Instruction", "Signed by", "Template"),
    ("make_order (deposit + locked split)", "buyer", "escrow: make_offer"),
    ("accept_order", "farmer", "new"),
    ("attest_handover / attest_pickup / attest_delivery", "farmer / transporter / transporter", "our record_attestation"),
    ("confirm_receipt (releases the split)", "buyer", "escrow: take_offer"),
    ("cancel_order (before acceptance)", "buyer", "escrow: cancel_offer"),
    ("refund_after_deadline", "buyer or anyone", "fundraiser: refund"),
    ("open_dispute / resolve_dispute", "buyer or farmer / resolver", "v1 plan"),
    ("open_pool / join_pool / close_pool", "transporter / order / anyone after deadline", "fundraiser"),
    ("collect_fees (pays the treasury only)", "anyone", "managed-fund"),
]

DECISIONS = [
    ("Question", "Why it matters", "My suggestion"),
    (b("1. Fee level and who pays it"), "Sets revenue and how competitive you are.", "Start low, split between buyer and farmer, with a cap in the code. Adjust with real orders."),
    (b("2. Who sets the transport price?"), "It is locked at commit, so someone must propose it.", "The transporter quotes; the buyer sees it before signing. Algorithm suggestions later."),
    (b("3. What if the buyer never confirms?"), "Money could sit forever.", "Auto-release after a fixed window once delivery is attested and no problem is reported."),
    (b("4. Who is the dispute resolver?"), "They decide contested orders.", "Platform admin first, boxed to the fixed outcomes. Multisig panel later."),
    (b("5. Token and on/off ramp"), "Same open questions as v1.", "USDC on plain SPL Token, and choose a currency ramp before stage 2."),
    (b("6. Is pooling in the first escrow release?"), "Pooling adds a second set of accounts and instructions to build and test.", "No. Ship single-order escrow first (stage 2), pooling second (stage 3)."),
]


def build():
    out = Path(__file__).resolve().parents[1] / "output/pdf/solana-integration-ideation-v2.pdf"
    doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=50, rightMargin=50, topMargin=46, bottomMargin=46, title="Solana integration - ideation v2")
    story = [
        p("Solana integration, version 2", H1),
        p("Thinking phase. Nothing in this document is built. It answers three questions and redraws the design with the transporter in the middle.", CAP),
        p("Three questions, short answers", H2),
        table([
            ("Question", "Short answer"),
            (b("1. Do we need an RPC node now?"), "<b>No paid one.</b> Program tests run in memory and devnet has a free public endpoint. Pick a provider before the mainnet pilot. Our code only needs one setting, so changing later is easy. (page 2)"),
            (b("2. Which QuickNode finance example fits best?"), "<b>escrow</b>, the Anchor v1 copy, as the base. Borrow <b>fundraiser</b> for pooled transport (target, deadline, refund) and <b>managed-fund</b> for fee rules (capped, fixed, no setter). (page 3)"),
            (b("3. How does the three-layer model work, and who pays?"), "Farmer, transporter and buyer each sign their own step. The buyer deposits once, and the program splits it by terms locked at commit. A small capped fee on completed orders pays for the platform. Nobody's money is lent or moved anywhere the rules do not allow. (pages 4 to 7)"),
        ], [150, 345]),
        p("What changed from version 1", H2),
        p("&bull; Version 1 said: extend the current program with a vault. Version 2 refines that: use the <b>escrow</b> example as the template for it, and upgrade Anchor from 0.30.1 to 1.2 as part of the same step."),
        p("&bull; The transporter is now a full participant that signs pickup and delivery, not just a name in the database."),
        p("&bull; Money design is explicit: one deposit, one locked three-way split, one capped fee."),
        p("&bull; The roadmap has four stages. Pooled transport gets its own stage."),
        p("Who wins in this design", H2),
        Diagram(110, d_wins),
        p("Figure 1. Everyone is paid from the same locked deposit; nobody is paid from someone else's pocket.", CAP),
        PageBreak(),
        p("Do we need an RPC node now?", H1),
        p("An RPC node is a server that answers questions about the blockchain and accepts transactions for it. Our payments code already talks to one through the single setting <font face='Courier'>SOLANA_RPC_URL</font>. Wallets (Phantom and similar) use their own connections, so you do not provide one for users."),
        Spacer(1, 6),
        Diagram(290, d_rpc),
        p("Figure 2. Where the RPC node sits, and what each stage needs.", CAP),
        p("When a paid provider becomes worth it", H2),
        p("&bull; <b>Real money:</b> the public endpoints are rate-limited and carry no promise of uptime, which is not acceptable once funds depend on it."),
        p("&bull; <b>The indexer:</b> it needs a steady feed of events (websockets or frequent polling)."),
        p("&bull; <b>Failover:</b> a second endpoint to switch to if the first fails."),
        p("&bull; <b>Real traffic:</b> many buyers acting at once."),
        p("What to compare: request limits and price, websocket support, failover options, devnet and mainnet in one plan, support. QuickNode is one candidate. I have not compared provider prices, so shortlist two or three at stage 3.", BODY),
        PageBreak(),
        p("Which QuickNode example fits best?", H1),
        p("The repo's <font face='Courier'>finance</font> folder has twelve examples. I read the code and README of escrow, fundraiser, managed-fund and token-swap; the others I judged from their folder names and descriptions."),
        Spacer(1, 4),
        Diagram(270, d_compare),
        p("Figure 3. The score is a judgement of how much each example helps this project.", CAP),
        p("Verdict: build on escrow", H2),
        p("Escrow is the smallest complete money program: one order account, one vault, three instructions, and tests. Its limit is that it swaps token for token in one atomic step, and our goods are physical, so there is a delivery in between. We keep its structure and add a delivery-confirmation step before release. It also charges no fee at all, so the fee split is ours to add, using managed-fund's rules."),
        p("Which copy of each example", H2),
        table(VARIANTS, [95, 205, 195]),
        PageBreak(),
        p("The three-layer model", H1),
        p("Farmers and buyers are the two outer layers. The transporter is the middle layer: goods pass through them, and their signed pickup and delivery are the evidence the program waits for before releasing money."),
        Spacer(1, 6),
        Diagram(335, d_layers),
        p("Figure 4. Green arrows are goods. Each layer signs only its own step; the program holds the money and the evidence.", CAP),
        PageBreak(),
        p("One order, step by step", H1),
        Spacer(1, 8),
        Diagram(285, d_swimlane),
        p("Figure 5. Who signs what. Boxes at the bottom are the unhappy paths.", CAP),
        p("What each unhappy path means", H2),
        p("&bull; <b>No acceptance:</b> the farmer never accepts. After the deadline the buyer reclaims the whole deposit, with no help from the platform."),
        p("&bull; <b>Silent buyer:</b> delivery is attested but the buyer never confirms. Open question 3 on the last page: release automatically after a fixed window unless a problem is reported."),
        p("&bull; <b>Problem reported:</b> a resolver can pick release, refund or the pre-agreed split. They cannot send money to a new address."),
        p("Instructions in this design", H2),
        table(INSTR, [215, 160, 120]),
        PageBreak(),
        p("Who pays, and how the platform earns", H1),
        Diagram(190, d_split),
        p("Figure 6. A worked example. The percentages are placeholders for a decision, not a recommendation.", CAP),
        p("Ways to earn, compared", H2),
        table(FEES, [92, 70, 120, 133, 80]),
        p("Recommended start: A plus B at a low combined rate, with option D paid out of it. Add C when pooling exists. Never F.", BODY),
        PageBreak(),
        p("How it stays honest: no stealing", H1),
        p("These are the rules the program should enforce, so honesty does not depend on a promise. None is built yet. Each one is copied from an example in the repo, or marked as new."),
        Spacer(1, 4),
        table(RULES, [120, 280, 95]),
        p("Rule 8 matters most in practice. Unless the program's upgrade key is controlled, a platform could replace the program with a different one, so a multisig and later a frozen or time-locked upgrade is part of going live.", CAP),
        PageBreak(),
        p("Roadmap, version 2", H1),
        Diagram(275, d_roadmap),
        p("Figure 7. Four stages. Each one is useful alone, so you can stop after any of them.", CAP),
        p("Decisions I need from you", H2),
        table(DECISIONS, [150, 150, 195]),
        Spacer(1, 6),
        p(f"{b('Next step if you agree:')} stage 1 is unchanged from version 1: fix the retry double-writes and add the program tests. It needs none of the decisions above."),
    ]
    doc.build(story)
    print(out)


if __name__ == "__main__":
    build()
