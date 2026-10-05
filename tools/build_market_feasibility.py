"""Builds output/pdf/market-feasibility-and-pitch.pdf: transport-cost correction, where the app could work, Colosseum partners, pitch advice."""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import PageBreak, SimpleDocTemplate, Spacer

from build_solana_ideation import AMBER, BLUE, BODY, CAP, GRAY, GREEN, H1, H2, INK, MUTED, RED, SMALL, SOFT, W, Diagram, arrow, b, box, p, table, text

DONE = colors.HexColor("#CFE6C8")
TEAL = colors.HexColor("#3E7FB0")
LINK = "#1A5FB4"


def link(url, label=None):
    return f'<link href="{url}" color="{LINK}">{label or url}</link>'


def hbar(c, x, y, label, value, vmax, maxw, color, fmt, label_w=70, size=7.6):
    text(c, x, y + 3, label, size, True)
    w = value / vmax * maxw
    c.setFillColor(color)
    c.rect(x + label_w, y, w, 12, fill=1, stroke=0)
    text(c, x + label_w + w + 4, y + 3, fmt, size)


# ---------------- diagrams ----------------
def d_share(c):
    text(c, 0, 118, "Transport as a share of the price the buyer finally pays (food grains, same study)", 8.8, True, GREEN)
    hbar(c, 0, 85, "My v2 example", 8, 30, 260, colors.HexColor("#B5BEB7"), "8%  (a placeholder I made up)", 110)
    hbar(c, 0, 58, "Bangladesh, Indonesia", 13.8, 30, 260, TEAL, "13.8%", 110)
    hbar(c, 0, 31, "Kenya, Malawi", 27.5, 30, 260, colors.HexColor("#A5702A"), "27.5%", 110)
    text(c, 0, 8, "Source: ReCAP / SLoCaT rural transport factsheet (2015). Grains, not fresh organic produce, so cold-chain freight would cost more.", 7.4, color=MUTED)


def d_deposits(c):
    text(c, 0, 128, "Same 100.00 of goods, same 3.00 platform fee, three transport costs (illustrative)", 8.8, True, GREEN)
    rows = [("Placeholder  8.00", 8.0), ("Asia study  13.80", 13.8), ("Africa study  27.50", 27.5)]
    scale = 300 / 129.0
    for i, (label, t) in enumerate(rows):
        y = 88 - i * 32
        deposit = 98.5 + t + 3.0
        x = 120
        text(c, 0, y + 7, label, 7.8, True)
        for amt, col in ((98.5, DONE), (t, AMBER), (3.0, TEAL)):
            c.setFillColor(col)
            c.setStrokeColor(INK)
            c.setLineWidth(0.6)
            c.rect(x, y, amt * scale, 20, fill=1, stroke=1)
            x += amt * scale
        text(c, x + 6, y + 7, f"buyer deposits {deposit:.2f}", 7.8)
    for x, col, lab in ((120, DONE, "Farmer 98.50"), (215, AMBER, "Transporter"), (290, TEAL, "Platform 3.00")):
        c.setFillColor(col)
        c.rect(x, 2, 8, 8, fill=1, stroke=1)
        text(c, x + 12, 3, lab, 7.4)


def d_demand(c):
    text(c, 0, 168, "Organic spend per person, euros a year (2024)", 8.6, True, GREEN)
    for i, (n, v) in enumerate([("Switzerland", 481), ("Denmark", 373), ("Austria", 292), ("EU average", 110), ("Europe average", 70)]):
        hbar(c, 0, 138 - i * 26, n, v, 481, 110, GREEN if i < 3 else colors.HexColor("#B5BEB7"), str(v), 68)
    text(c, 262, 168, "Biggest organic markets, billion euros (2024)", 8.6, True, GREEN)
    for i, (n, v) in enumerate([("USA", 60.4), ("Germany", 17.0), ("China", 15.5), ("France", 12.2), ("Italy", 5.2)]):
        hbar(c, 262, 138 - i * 26, n, v, 60.4, 110, TEAL if i < 3 else colors.HexColor("#B5BEB7"), f"{v:.1f}", 56)
    text(c, 0, 14, "Share of all food sales that is organic: Switzerland 12.3%, Denmark 11.6%, Austria 11.4%.  World total: 145.0 billion euros.", 7.8, color=MUTED)
    text(c, 0, 3, "Source: FiBL, The World of Organic Agriculture 2026 (data year 2024).", 7.4, color=MUTED)


SCORE_FILL = {1: "#F6D5D1", 2: "#FBEBC8", 3: "#EFEFEA", 4: "#DCEBD3", 5: "#BFDDB3"}
REGIONS = [  # name, demand, supply, payment need, pooling benefit, ease
    ("Southeast Asia (VN, PH, ID)", 2, 4, 4, 4, 3),
    ("Nigeria, Kenya", 1, 4, 5, 5, 2),
    ("India", 2, 5, 3, 4, 2),
    ("Brazil, Ecuador, Mexico", 2, 4, 3, 3, 2),
    ("USA", 5, 3, 1, 3, 2),
    ("Switzerland, Denmark, Austria", 5, 2, 1, 2, 3),
    ("Germany, France, Italy", 4, 3, 1, 2, 3),
    ("China", 4, 3, 1, 3, 1),
]


def d_grid(c):
    heads = ["Organic\ndemand", "Small-farm\nsupply", "Payment\npain", "Pooling\nbenefit", "Ease of\nstarting", "Total"]
    x0, cw, rh = 150, 56, 24
    for j, h in enumerate(heads):
        for k, ln in enumerate(h.split("\n")):
            text(c, x0 + j * cw + cw / 2, 232 - k * 9, ln, 7.2, True, MUTED, center=True)
    for i, (name, *sc) in enumerate(REGIONS):
        y = 200 - i * rh
        text(c, 0, y + 8, name, 7.8, True)
        for j, v in enumerate(sc):
            c.setFillColor(colors.HexColor(SCORE_FILL[v]))
            c.setStrokeColor(colors.white)
            c.rect(x0 + j * cw, y, cw - 2, rh - 2, fill=1, stroke=0)
            text(c, x0 + j * cw + cw / 2 - 1, y + 8, str(v), 8.5, True, center=True)
        tot = sum(sc)
        c.setFillColor(GREEN if tot >= 16 else colors.HexColor("#5C6B62"))
        c.rect(x0 + 5 * cw, y, cw - 2, rh - 2, fill=1, stroke=0)
        text(c, x0 + 5 * cw + cw / 2 - 1, y + 8, str(tot), 9, True, colors.white, center=True)
    text(c, 0, 4, "Scores 1 (poor) to 5 (strong) are my judgement from the evidence below; they are not measurements.", 7.6, color=MUTED)


def d_corridor(c):
    box(c, 0, 80, 150, 100, "PRO-BIO DEMAND\nSwitzerland, Denmark, Austria, Germany, France.\nHighest organic spend per person.\nCards and bank transfers already work, so a blockchain adds little.", BLUE, 7.6)
    box(c, 345, 80, 150, 100, "SUPPLY + PAYMENT PAIN\nIndia, Southeast Asia, Nigeria, Kenya, Latin America.\nMany small farms, high transport share, expensive or slow payments.", DONE, 7.6)
    box(c, 175, 135, 145, 45, "PHASE 1: domestic pilot\npooled trucks + stablecoin payout inside one country", AMBER, 7.4)
    arrow(c, 345, 157, 320, 157, color=GREEN)
    box(c, 175, 80, 145, 45, "PHASE 2: export corridor\nUSDC escrow from cooperatives to pro-bio buyers", colors.HexColor("#E9E3F3"), 7.4)
    arrow(c, 345, 102, 320, 102, color=GREEN)
    arrow(c, 175, 102, 150, 102, color=GREEN)
    text(c, 0, 55, "The tension: the countries that eat the most organic food are the ones that need blockchain payments the least.", 8.3, True, GREEN)
    text(c, 0, 43, "So start where payment and transport pain is biggest, and treat the pro-bio countries as the later destination, not the first pilot.", 8, color=INK)
    text(c, 0, 25, "Phase 2 adds certification, customs and cross-border cold chain. I have not researched those costs.", 7.8, color=MUTED)


def d_partners(c):
    text(c, 0, 238, "Ideas to test with each project (none is an agreement; I found no public user numbers for any of them)", 8.6, True, GREEN)
    box(c, 190, 95, 115, 70, "Farmer Marketplace\npooled supply, escrow, three-way settlement", DONE, 8)
    left = [(185, "Nomad", "cash out to local currency (Nigeria)", BLUE), (115, "Ripe", "pay with local QR e-wallets (Southeast Asia)", BLUE), (45, "Home Harvest", "small growers with surplus", SOFT)]
    right = [(185, "GreenKWh", "rural cooperatives, cold-storage power (India)", AMBER), (115, "MCPay", "paid data feeds later (x402)", AMBER), (45, "DePlan", "inactive: nothing to pool", GRAY)]
    for y, n, t, col in left:
        box(c, 0, y, 140, 48, f"{n}\n{t}", col, 7.4)
        arrow(c, 140, y + 24, 190, 130, color=MUTED)
    for y, n, t, col in right:
        box(c, 355, y, 140, 48, f"{n}\n{t}", col, 7.4)
        arrow(c, 355, y + 24, 305, 130, color=MUTED)


def d_say(c):
    box(c, 0, 8, 240, 135, "AVOID\n\"We will steal users from other Colosseum winners.\"\n\nIt sounds hostile, claims numbers you cannot show, and is aimed at people who may be judging you or investing in the same accelerator.", RED, 8.2)
    box(c, 255, 8, 240, 135, "SAY INSTEAD\n\"We plug into the rails other Solana teams built, like local off-ramps and QR payments, so farmers get paid in local currency without us rebuilding them.\"\n\n\"Our first customers are X cooperatives and Y buyers.\"", DONE, 8.2)
    arrow(c, 240, 76, 255, 76, color=GREEN)


# ---------------- tables ----------------
EVIDENCE = [
    ("Region", "What the evidence says", "Biggest risk"),
    (b("Southeast Asia"), "Vietnam, Indonesia and the Philippines are in the 2025 top-10 for crypto adoption. Indonesia's transport share of price is 13.8% (grain study). Ripe (a Colosseum winner) already pays merchants in the Philippines through local QR wallets.", "Domestic demand for organic produce not measured here; island logistics."),
    (b("Nigeria, Kenya"), "Nigeria is top-10 for adoption and a leading stablecoin market; transport is 27.5% of price in Kenya and Malawi, and freight tariffs run up to six times higher than comparable Asian journeys, so pooling saves the most here.", "Currency swings, thin organic demand, regulatory change."),
    (b("India"), "Ranked first for crypto adoption three years running. Organic production rose to 46.99 lakh tonnes in 2024-25 and organic food exports to USD 665 million, with a target of USD 2 billion by 2030, largely through farmer cooperatives (FPOs).", "Strong domestic payment rails; demanding crypto tax and regulation."),
    (b("Latin America"), "Ecuador is the leading organic supplier to the EU; Mexico and Ecuador are the largest exporters to EU and US markets. Brazil is top-10 for adoption.", "Export certification and customs, not local trucking."),
    (b("USA, Europe, China"), "Largest and richest organic demand (USA 60.4 bn, Germany 17.0 bn, China 15.5 bn, France 12.2 bn euros). Switzerland leads per person at 481 euros.", "Existing payment rails work well, so the chain adds little; incumbents are strong."),
]

PROJECTS = [
    ("Project", "Result", "Links"),
    (b("Home Harvest"), "Breakout hackathon, DePIN track, 3rd. 'The world's largest ReFi community of connected growers.'", link("https://blog.colosseum.com/announcing-the-winners-of-the-solana-breakout-hackathon/", "Breakout winners")),
    (b("GreenKWh"), "Formerly Svachsakthi, India-based off-grid renewable-energy network. Chosen for Colosseum Accelerator Cohort 2 (cohort made of Radar hackathon founders). The Radar 1st place comes from your file; I did not re-verify it.", link("https://blog.colosseum.com/introducing-colosseum-accelerator-cohort-2/", "Cohort 2") + "<br/>" + link("https://thegrid.id/profiles/greenkwh", "Profile")),
    (b("Ripe"), "Renaissance hackathon, DeFi and Payments, 4th. Scan GCash or Venmo QR codes and pay with Solana USDC; the merchant receives local currency in their own e-wallet.", link("https://arena.colosseum.org/projects/explore/587", "Colosseum Arena") + "<br/>" + link("https://bitpinas.com/feature/ph-based-projects-solana-renaissance/", "Bitpinas article")),
    (b("Nomad"), "Renaissance, DeFi and Payments, 3rd. Nigeria-based payment app that streamlines off-ramping.", link("https://arena.colosseum.org/projects/explore/829", "Colosseum Arena") + "<br/>" + link("https://blog.colosseum.com/announcing-the-winners-of-the-solana-renaissance-hackathon/", "Renaissance winners")),
    (b("MCPay"), "Cypherpunk hackathon, Stablecoin track winner; Colosseum Accelerator Cohort 4. Pay-per-use MCP tools using x402.", link("https://blog.colosseum.com/announcing-the-winners-of-the-solana-cypherpunk-hackathon/", "Cypherpunk winners") + "<br/>" + link("https://blog.colosseum.com/announcing-colosseums-accelerator-cohort-4/", "Cohort 4") + "<br/>" + link("https://ethglobal.com/showcase/mcpay-fun-y16d3", "ETHGlobal page")),
    (b("DePlan"), "Renaissance, Consumer Apps, 5th. Pay-as-you-go subscriptions. Your file says the main site is offline; I did not re-check.", link("https://arena.colosseum.org/projects/explore/153", "Colosseum Arena") + "<br/>" + link("https://solanacompass.com/projects/deplan", "Solana Compass")),
]

SOURCES = [
    ("Fact", "Source"),
    ("Organic market size, per person spend, shares (2024)", link("https://www.fibl.org/en/info-centre/news/global-organic-market-hits-all-time-high-in-2024", "FiBL global release") + "<br/>" + link("https://www.fibl.org/fileadmin/documents/en/news/2026/MR-EUROPE-2026-02-10-ENGLISH-final.pdf", "FiBL Europe release (PDF)")),
    ("Transport share of price, tariffs, producer share", link("https://assets.publishing.service.gov.uk/media/57a0898840f0b652dd000284/61280-SloCat_2015_RuralTransportandAgriculture_FactSheet_ReCAP_Eng_v150910.pdf", "ReCAP / SLoCaT factsheet 2015 (PDF)")),
    ("Crypto adoption ranking 2025", link("https://decrypt.co/337855/us-crypto-adoption-on-the-rise-following-regulatory-momentum-chainalysis", "Decrypt on the Chainalysis index")),
    ("India organic production and exports", link("https://indiaseatradenews.com/india-targets-2-billion-in-organic-food-exports-by-2030/", "India Sea Trade News") + "<br/>" + link("https://indiancooperative.com/featured/co-ops-drive-organic-revolution-india-targets-rs-20k-crores-exports/amp", "Indian Cooperative")),
    ("Colosseum winners and cohorts", "See the links in the project table."),
]

DECISIONS = [
    ("Question", "Why it matters", "My suggestion"),
    (b("1. Which country first?"), "Decides the partners, the currency and the payout route.", "Choose between Southeast Asia and Nigeria or Kenya after 3 to 5 conversations with cooperatives. Both score highest here."),
    (b("2. Is your target Singapore?"), "Your project folder is called singapore, but I did not research it.", "Tell me and I will add it as a region."),
    (b("3. Which buyers pay a premium locally?"), "Local organic demand is thin in the highest-scoring regions.", "Test restaurants, hotels and retailers, not households."),
    (b("4. Collect real transport quotes"), "My 8, 13.8 and 27.5 are examples. Real trips decide the fee design.", "Ask 3 transporters per corridor for price per trip, load and distance."),
]


def build():
    out = Path(__file__).resolve().parents[1] / "output/pdf/market-feasibility-and-pitch.pdf"
    doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=50, rightMargin=50, topMargin=46, bottomMargin=46, title="Market feasibility, partners and pitch")
    story = [
        p("Where could this app work?", H1),
        p("Market feasibility, a corrected transport model, the Colosseum projects, and what to say in the pitch. Thinking phase; nothing here is built.", CAP),
        p("Short answers", H2),
        table([
            ("Question", "Short answer"),
            (b("Was 8 of 100 a fair transport cost?"), "<b>No.</b> It was a placeholder I made up. A 2015 ReCAP/SLoCaT factsheet puts transport at <b>13.8%</b> of market price in Bangladesh and Indonesia and <b>27.5%</b> in Kenya and Malawi. Your instinct was right. (page 2)"),
            (b("Where is the demand for organic food?"), "Switzerland, Denmark and Austria spend the most per person (481, 373 and 292 euros a year). The biggest total markets are the USA, Germany and China. (page 3)"),
            (b("Where is the best place to start?"), "No single country is proven. On my scoring, <b>Southeast Asia and Nigeria or Kenya</b> come out highest, because payments and transport hurt most there. The high-organic countries are the later destination. (pages 4 and 5)"),
            (b("Can we pool users from Colosseum winners?"), "Not by taking them. I found <b>no public user numbers</b>, and the projects serve different users. Partnerships with a few of them are realistic. (pages 6 and 7)"),
            (b("Should the pitch say you hope to steal users?"), "<b>No.</b> Say you build on their rails and name your own first customers instead. (page 7)"),
        ], [165, 330]),
        p("What this changes in version 2", H2),
        p("&bull; Transport is the biggest cost block after the goods themselves, so it must be a <b>real quote per trip</b>, locked at commit, not a fixed number."),
        p("&bull; The platform fee should stay a small share of the <b>goods</b> price (the 3.00 example), so it does not balloon when transport is expensive."),
        p("&bull; Pooling matters more than I showed: it matters most exactly where transport is a quarter of the price."),
        PageBreak(),
        p("Transport costs: correcting the example", H1),
        Diagram(125, d_share),
        p("Figure 1. The study measured food grains in 2015. Treat the numbers as a floor for fresh organic produce, which needs cold or fast transport.", CAP),
        p("Other findings from the same factsheet: freight tariffs were up to six times higher in Africa than in Asia for comparable journeys, and producers received 75 to 90% of the final price in Asia but only 30 to 60% in Africa.", BODY),
        Spacer(1, 6),
        p("What it does to the money split", H2),
        Diagram(145, d_deposits),
        p("Figure 2. Only the transporter's slice and the buyer's deposit move. The farmer and platform amounts stay the same, which is why the fee is a share of goods.", CAP),
        p("How a real transport price should be set", H2),
        p("The transporter quotes the cost of the whole trip (driver, vehicle, fuel, tolls, cooling). The app divides it among the orders on the trip by weight and by how far each goes, and each order's share is locked when the buyer commits. The Solana program only ever sees the final amount per order."),
        p("Why pooling matters, with a worked example", H2),
        table([
            ("Truck load", "Cost per kilogram vs a half-full truck", "Reading"),
            ("50% full", "100%", "The baseline: a typical solo trip (assumed)."),
            ("70% full", "71% (a 29% saving)", "Pooling two or three small orders."),
            ("85% full", "59% (a 41% saving)", "A well-planned pooled trip."),
        ], [100, 190, 205]),
        p("Arithmetic only: the cost per kilogram falls by baseline load divided by new load. The 50% starting load is an assumption; replace it with real data.", CAP),
        PageBreak(),
        p("Where organic demand is", H1),
        Diagram(185, d_demand),
        p("Figure 3. Pro-bio demand is concentrated in a few European countries; the largest total markets are the USA, Germany and China.", CAP),
        p("What this does and does not tell us", H2),
        p("&bull; <b>Demand is not where blockchain helps.</b> Switzerland, Denmark and Austria already have cheap, trusted payments. Escrow and stablecoins add little there."),
        p("&bull; <b>Supply is elsewhere.</b> Ecuador is the leading organic supplier to the EU, and Mexico and Ecuador are among the largest exporters to the EU and US. India's organic exports reached USD 665 million in 2024-25."),
        p("&bull; <b>Missing data.</b> The sources I read give no organic spend per person for India, Southeast Asia or Africa. Local demand there has to be measured by interviews, not assumed."),
        p("&bull; <b>Singapore.</b> Your project folder is called singapore, but I did not research it."),
        PageBreak(),
        p("Which region fits best?", H1),
        Diagram(255, d_grid),
        p("Figure 4. Each column is a question: is there organic demand, are there many small farms, do payments hurt today, would pooling save money, and is it easy to start?", CAP),
        table(EVIDENCE, [85, 280, 130]),
        p("The totals are my judgement from the evidence above. Small changes in a score can reorder the top three, so treat them as a shortlist, not a ranking.", CAP),
        PageBreak(),
        p("Recommendation: a two-phase corridor", H1),
        Diagram(235, d_corridor),
        p("Figure 5. Prove pooling and stablecoin payout inside one country first, then connect to pro-bio buyers.", CAP),
        p("What to confirm before choosing", H2),
        table(DECISIONS, [150, 150, 195]),
        PageBreak(),
        p("The Colosseum projects, with links", H1),
        p("These are the six projects in your file. Result lines come from Colosseum's own posts where I could open them; where I could not, the table says so."),
        Spacer(1, 4),
        table(PROJECTS, [75, 280, 140]),
        p("The Arena links come from Colosseum's own winners post; I did not open each Arena page. Re-check status before any formal submission.", CAP),
        Spacer(1, 6),
        p("How to reach these communities", H2),
        Diagram(255, d_partners),
        p("Figure 6. Partnership ideas, strongest at the top. Nomad and Ripe are the most concrete because both already move money between stablecoins and local currency.", CAP),
        PageBreak(),
        p("Can we pool their customers, and should the pitch say so?", H1),
        p("Pooling customers", H2),
        p("&bull; <b>Taking users is not realistic.</b> These projects serve different people (energy, payments, developer tools, home growers), so there is little overlap to take, and I found no public numbers for any of them."),
        p("&bull; <b>Partnering is realistic.</b> A farmer paid in USDC needs a way to cash out; a buyer may want to pay from a local wallet. Nomad and Ripe solve exactly those steps. Whether they offer integrations or partnerships is unknown to me, so ask them."),
        p("&bull; <b>Use the community channel.</b> Colosseum cohorts and hackathon alumni share introductions. A working demo that uses a peer's rails is a far stronger message than a claim about their users."),
        p("Should you say you hope to steal users?", H2),
        Diagram(150, d_say),
        p("Figure 7. Same ambition, different wording.", CAP),
        p("My advice is <b>no</b>, for five reasons:"),
        p("1. <b>Judges and investors.</b> Colosseum selected several of these teams for its accelerator (GreenKWh in cohort 2, MCPay in cohort 4). A judge may know them personally."),
        p("2. <b>It cannot be backed up.</b> You have no data on their users, and a claim you cannot support weakens the rest of your pitch."),
        p("3. <b>It is aimed at the wrong thing.</b> They do not sell farm produce. Your real competition is informal trading, wholesalers and existing farm marketplaces."),
        p("4. <b>It signals zero-sum thinking.</b> The strongest Solana pitches show an ecosystem effect: you bring new, real-world users onto shared rails."),
        p("5. <b>What impresses is concrete traction.</b> Name your first cooperatives and buyers, and one transport quote."),
        PageBreak(),
        p("Sources", H1),
        table(SOURCES, [190, 305]),
        Spacer(1, 8),
        p("Limits of this study", H2),
        p("&bull; The regional scores are my judgement and use only the sources listed. No survey or interview data was collected."),
        p("&bull; Transport figures are from a 2015 grain study; fresh organic produce is likely to cost more."),
        p("&bull; I found no organic spend per person for India, Southeast Asia or Africa."),
        p("&bull; I did not research regulation of crypto payments or organic certification in any country. Check both with a local adviser before choosing a pilot."),
    ]
    doc.build(story)
    print(out)


if __name__ == "__main__":
    build()
