"""Builds output/pdf/elevator-pitch.pdf (5 pages). Status claims match CLAUDE.md; partner names are targets, not agreements."""
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.platypus import PageBreak, SimpleDocTemplate, Spacer

from build_solana_devnet_guide import AMBER, BLUE, DONE
from build_solana_ideation import BODY, CAP, GRAY, GREEN, H1, H2, MUTED, RED, SOFT, Diagram, arrow, b, box, p, table, text


def d_need(c):
    text(c, 0, 178, "Three people lose today, so nobody can rely on anybody", 9.5, True, GREEN)
    items = [("Farmers\nSell alone, one small lot at a time.\nNo steady buyer.", RED), ("Buyers\nNeed a steady quantity.\nOne farm cannot give it.", RED), ("Trucks\nRun half empty.\nTransport is 13.8% to 27.5%\nof the market price.", RED)]
    for i, (t, col) in enumerate(items):
        box(c, i * 168, 95, 159, 66, t, AMBER if col is RED else SOFT, 7.8)
        arrow(c, i * 168 + 80, 95, 247, 66)
    box(c, 70, 8, 355, 56, "The marketplace turns many small farms into one reliable supplier:\ncollect supply, match it to demand, share the truck.", DONE, 8.6)


def d_chain(c):
    text(c, 0, 188, "One shared record that none of the three can quietly edit", 9.5, True, GREEN)
    for i, name in enumerate(("Farmer\nsays: packed", "Transporter\nsays: picked up, delivered", "Buyer\nsays: received")):
        x = i * 168
        box(c, x, 130, 159, 40, name, SOFT, 8)
        arrow(c, x + 80, 130, 247, 105)
    box(c, 120, 62, 255, 43, "Solana record\nfingerprint of each step + order status", BLUE, 8.6)
    box(c, 0, 4, 240, 46, "ON THE CHAIN\nFingerprints (hashes), status, who signed", DONE, 7.8)
    box(c, 255, 4, 240, 46, "NOT ON THE CHAIN\nNames, photos, prices detail, quality judgement", GRAY, 7.8)


def d_layers(c):
    text(c, 0, 218, "Three layers: farmers and buyers are the blocks, transport is the layer between", 9.5, True, GREEN)
    box(c, 0, 80, 130, 120, "LAYER 1\nFARMERS\nList quantity and price.\nPool with neighbours to fill one order.", SOFT, 8.2)
    box(c, 182, 80, 131, 120, "LAYER 2\nTRANSPORTERS\nQuote per trip.\nShare one truck across orders.", AMBER, 8.2)
    box(c, 365, 80, 130, 120, "LAYER 3\nBUYERS\nPost demand.\nGet one steady supply.", BLUE, 8.2)
    arrow(c, 130, 160, 182, 160, "goods", GREEN)
    arrow(c, 313, 160, 365, 160, "goods", GREEN)
    arrow(c, 365, 110, 313, 110, "payment", MUTED, dash=True)
    arrow(c, 182, 110, 130, 110, "payment", MUTED, dash=True)
    box(c, 0, 8, 495, 52, "Trust record on Solana runs under all three: signed pickup and delivery, a settlement outcome, and a reputation history each party can carry.", DONE, 8.4)


def d_money(c):
    text(c, 0, 188, "Money path: local currency in, local currency out, with a ramp partner at each end", 9, True, GREEN)
    steps = [("Buyer\npays in local currency", SOFT), ("Local exchanger\nlocal currency to stablecoin", AMBER), ("Escrow on Solana\nholds until delivery", BLUE), ("Local exchanger\nstablecoin to local currency", AMBER), ("Farmer + transporter\npaid locally", SOFT)]
    for i, (t, fill) in enumerate(steps):
        x = i * 100
        box(c, x, 112, 91, 56, t, fill, 7.2)
        if i < 4:
            arrow(c, x + 91, 140, x + 100, 140)
    text(c, 0, 94, "Colosseum teams that already solved a piece of this (examples to approach, none has agreed):", 8, True)
    box(c, 0, 30, 160, 52, "Nomad\nNigeria off-ramp and payments app", GRAY, 7.8)
    box(c, 167, 30, 160, 52, "Ripe\nQR merchant payments, Southeast Asia", GRAY, 7.8)
    box(c, 334, 30, 161, 52, "MCPay\nx402 pay-per-call, later for price and weather data", GRAY, 7.6)
    text(c, 0, 8, "Our part is the farm-to-buyer coordination. We do not rebuild their rails.", 8, True, GREEN)


def build():
    out = Path(__file__).resolve().parents[1] / "output/pdf/elevator-pitch.pdf"
    doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=50, rightMargin=50, topMargin=46, bottomMargin=46, title="Farmer Marketplace elevator pitch")
    story = [
        p("Farmer Marketplace", H1),
        p("One reliable supplier from many small farms, with a shared record of who did what. A five-page pitch.", CAP),
        p("1. The need", H2),
        p("A restaurant, hotel or retailer wants a steady quantity of produce. A small farm has a few hundred kilos and no way to reach that buyer. The truck between them is often half empty, and the trip eats a large share of the price."),
        Spacer(1, 4),
        Diagram(190, d_need),
        p("Figure 1. Everyone in the chain loses a little, and together they lose the sale.", CAP),
        table([
            ("Fact", "Number", "Source and caveat"),
            (b("Transport as a share of market price"), "13.8% (Bangladesh, Indonesia), 27.5% (Kenya, Malawi)", "ReCAP / SLoCaT rural transport factsheet, 2015, food grains. Fresh produce likely costs more."),
            (b("Pooling idea"), "Compatible orders share one pickup and one truck", "Savings are not measured yet. Real trip quotes in the pilot corridor decide the fee design."),
        ], [135, 160, 200]),
        PageBreak(),
        p("2. Why blockchain, and only for one job", H1),
        p("Three parties who do not know each other must agree on what happened: the farmer packed it, the transporter moved it, the buyer received it. If one company keeps that record, each party has to trust that company. A shared public record removes that single point of trust."),
        Spacer(1, 4),
        Diagram(200, d_chain),
        p("Figure 2. The chain keeps fingerprints and a status. Everything private stays off it.", CAP),
        table([
            ("What blockchain gives", "In this app"),
            (b("A record nobody can quietly rewrite"), "Each pickup and delivery step is fingerprinted and stored in order; a retry can never add the same step twice"),
            (b("Settlement that anyone can check"), "The order ends as COMPLETED or REFUNDED, and the program refuses to flip it afterwards"),
            (b("A history that follows the person"), "Reputation built from signed steps, portable if they move to another platform"),
            (b("What it does NOT do"), "It cannot tell if the tomatoes were good. Disputes still need a person or a rule"),
        ], [165, 330]),
        p("Fast and cheap: a settle step cost 0.000005 SOL (5,000 lamports) on devnet.", CAP),
        PageBreak(),
        p("3. The three layers", H1),
        p("The farmers and buyers are the two blocks that want to trade. Transport is the middle layer that makes the trade physically possible, and gets its own pay."),
        Spacer(1, 4),
        Diagram(230, d_layers),
        p("Figure 3. Goods move left to right, payment moves right to left, the trust record sits under all of it.", CAP),
        table([
            ("Layer", "Who", "What they do", "What they get"),
            (b("1"), "Farmers", "List lots; pool with neighbours to fill a big order", "A buyer they could not reach alone, paid on delivery"),
            (b("2"), "Transporters", "Quote a price per trip; share a truck across orders", "A fuller truck and a locked fare per trip"),
            (b("3"), "Buyers", "Post demand; receive one combined supply", "Steady quantity and a verified delivery record"),
        ], [40, 80, 205, 170]),
        p("The platform fee is planned as a capped slice of a split locked when the order is made (farmer, transporter, platform), so no one can take more later. That split is the next build stage, not live yet.", CAP),
        PageBreak(),
        p("4. Partnering with local-currency exchangers and other Colosseum teams", H1),
        p("Farmers and drivers want local money, not tokens. Buyers pay in local money too. Exchange companies that convert local currency to and from Solana-based stablecoins are the bridge. We should plug into them, and into other Colosseum teams who already built a piece."),
        Spacer(1, 4),
        Diagram(205, d_money),
        p("Figure 4. We own the middle, escrow and coordination. Partners own the two ends.", CAP),
        table([
            ("Partner", "What they get", "What we get"),
            (b("Local-currency exchanger"), "Steady, recurring volume: every order and every payout runs through them, on both sides", "Local-currency payout without building licences or banking links"),
            (b("Colosseum payment teams (e.g. Nomad, Ripe)"), "A real-world use case and transaction flow for their rails; shared story in the ecosystem", "Proven local rails and users in their markets"),
            (b("x402 teams (e.g. MCPay), later"), "A paying customer for price, weather and logistics data", "Paid data feeds without building them"),
        ], [140, 180, 175]),
        p("Pitch wording: say we build on their rails and bring them volume. Do not say we want to take their users; the whole value is that we are complementary.", CAP),
        p("Status: these are proposals. No partner has been contacted or agreed. Which exchangers are licensed in the pilot country must be checked locally.", CAP),
        PageBreak(),
        p("5. Where we are, and the 30-second version", H1),
        table([
            ("Built and working", "Planned"),
            ("Marketplace, matching, pooled transport, trust and reputation (phases 1 to 4); API and web app live on Vercel with a Neon database. Solana program deployed to devnet; all 13 end-to-end checks pass there. Retries cannot double-record a step.",
             "Real escrow with the locked three-way split; production on the Solana provider (today it runs a mock); chain calls moved to a background worker; Rust tests; paid RPC; multisig upgrade authority; audit."),
        ], [247, 248]),
        Spacer(1, 6),
        p("Elevator script, about 30 seconds", H2),
        p("<i>\"Small farmers cannot supply restaurants and shops reliably, and half-empty trucks eat a fifth of the price. We combine many farms into one supplier, match them to buyers, and pool the transport. Solana keeps a shared record of each pickup and delivery and settles the order, so no one has to trust a middleman. Farmers and drivers get paid in local currency through exchange partners, so no one needs to hold crypto. We are looking for one pilot corridor, a local-currency exchanger to partner with, and a few cooperatives and buyers to test with.\"</i>"),
        Spacer(1, 4),
        p("Check before you say it", H2),
        table([
            ("Claim in the script", "Make sure"),
            ("a fifth of the price", "Sources say 13.8% to 27.5% for grain. Say 'up to a quarter' or quote the study; replace with your own pilot quote when you have it"),
            ("get paid in local currency", "True only once an exchanger is signed. Until then say 'we are lining up'"),
            ("Solana settles the order", "Today the settlement record exists on devnet; money does not move yet. Say 'records and settles', not 'holds funds', until escrow is built"),
        ], [150, 345]),
        Spacer(1, 6),
        p("Open choices (fee level, who sets the transport price, first country, dispute rule) are in solana-integration-ideation-v2.pdf and market-feasibility-and-pitch.pdf.", CAP),
    ]
    doc.build(story)
    print(out)


if __name__ == "__main__":
    build()
