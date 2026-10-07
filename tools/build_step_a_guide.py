"""Builds output/pdf/step-a-and-frontend-plan.pdf. Backend facts match api/app/payments; frontend facts were read from apps/web (one page.tsx, 209 lines)."""
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.platypus import PageBreak, SimpleDocTemplate, Spacer

from build_solana_devnet_guide import AMBER, BLUE, DONE, PID, term
from build_solana_ideation import BODY, CAP, GRAY, GREEN, H1, H2, MUTED, RED, SOFT, Diagram, arrow, b, box, p, table, text

KEY = "8dxtAKX8UUDCeuKbttr6foBXedV7ZU5X23iUXR9TAacA"


# ---------------------------------------------------------------- diagrams
def d_before_after(c):
    text(c, 0, 218, "BEFORE (today): the mock provider answers instantly, nothing leaves our server", 8.8, True, GREEN)
    for i, (t, f) in enumerate([("Order accepted", SOFT), ("API writes a row\nstatus CONFIRMED (mock)", GRAY), ("Done", SOFT)]):
        box(c, i * 170, 168, 150, 36, t, f, 8)
        if i < 2:
            arrow(c, i * 170 + 150, 186, i * 170 + 170, 186)
    text(c, 0, 142, "AFTER (Step A): the row waits, a timer sends it to Solana devnet", 8.8, True, GREEN)
    box(c, 0, 92, 110, 38, "Order accepted", SOFT, 8)
    box(c, 125, 92, 125, 38, "API writes a row\nstatus PENDING", AMBER, 8)
    box(c, 265, 92, 110, 38, "Done: the buyer\nis not kept waiting", DONE, 7.8)
    arrow(c, 110, 111, 125, 111)
    arrow(c, 250, 111, 265, 111)
    box(c, 125, 30, 125, 38, "Timer (cron), every minute\nGET /payments/cron", BLUE, 7.6)
    box(c, 290, 30, 95, 38, "RPC endpoint\nSOLANA_RPC_URL", GRAY, 7.6)
    box(c, 400, 30, 95, 38, "Program on devnet\n9ZZ5bej...", DONE, 7.6)
    arrow(c, 187, 92, 187, 68, "reads PENDING", MUTED, label_dy=-14)
    arrow(c, 250, 49, 290, 49)
    arrow(c, 385, 49, 400, 49)
    text(c, 0, 8, "When it lands the row turns CONFIRMED and stores the transaction signature you can open in the explorer.", 7.6, color=MUTED)


def d_roadmap(c):
    text(c, 0, 226, "BACKEND AND SOLANA", 8.8, True, GREEN)
    back = [("Phase 1 code\nretry-safe sends,\nqueue, tests", DONE), ("STEP A\nswitch production\nto devnet", AMBER), ("Stage 2\ntoken escrow,\nlocked split", SOFT), ("Stage 3\npooled transport\nrefunds", SOFT), ("Stage 4\nhardening, audit,\nmultisig", SOFT)]
    for i, (t, f) in enumerate(back):
        box(c, i * 101, 160, 90, 56, t, f, 7.6)
        if i < 4:
            arrow(c, i * 101 + 90, 188, i * 101 + 101, 188)
    text(c, 0, 108, "FRONTEND", 8.8, True, GREEN)
    front = [("F0\nshared code\nextracted", SOFT), ("F1\nshell, nav,\nlogin, session", SOFT), ("F2\nbuyer routes", SOFT), ("F3\nfarmer and\ntransport routes", SOFT), ("F4\nadmin and\nchain proof", AMBER), ("F5\npolish, retire\nold page", SOFT)]
    for i, (t, f) in enumerate(front):
        box(c, i * 84, 40, 75, 56, t, f, 7.2)
        if i < 5:
            arrow(c, i * 84 + 75, 68, i * 84 + 84, 68)
    arrow(c, 156, 160, 372, 96, "F4 needs Step A", RED, dash=True, size=7, label_dy=6)
    text(c, 0, 20, "F0 to F3 do not wait for anything on the backend: they can start today, in parallel with Step A.", 7.8, True)
    text(c, 0, 7, "Stage 2 adds payment screens later; the F1 shell is where they will plug in.", 7.6, color=MUTED)


def d_sequence(c):
    text(c, 0, 170, "INSIDE THE REQUEST: fast, the buyer never waits for Solana", 8.8, True, GREEN)
    top = [("1  Farmer taps\nAccept", SOFT), ("2  orders.advance()\npublishes\norder.status_changed", SOFT), ("3  payments handler\nwrites a PENDING\nrow (enqueue)", AMBER), ("4  Reply sent,\nscreen updates", DONE)]
    for i, (t, f) in enumerate(top):
        box(c, i * 127, 100, 112, 54, t, f, 7.4)
        if i < 3:
            arrow(c, i * 127 + 112, 127, i * 127 + 127, 127)
    c.setDash(3, 3)
    c.setStrokeColor(MUTED)
    c.line(0, 84, 495, 84)
    c.setDash()
    text(c, 0, 72, "LATER, ON A TIMER: a separate request, up to a minute afterwards", 8.8, True, GREEN)
    bot = [("5  Cron calls\nGET /payments/cron\nwith the secret", BLUE), ("6  process_queue()\nlocks PENDING and\nFAILED rows,\noldest first", BLUE), ("7  Adapter reads the\nchain, sends only\nwhat is missing", AMBER), ("8  Row becomes\nCONFIRMED and\nstores the signature", DONE)]
    for i, (t, f) in enumerate(bot):
        box(c, i * 127, 4, 112, 58, t, f, 7.2)
        if i < 3:
            arrow(c, i * 127 + 112, 33, i * 127 + 127, 33)


def d_vars(c):
    text(c, 0, 178, "The five settings and what each one does", 9.5, True, GREEN)
    rows = [("PAYMENT_PROVIDER = solana", "the switch: use the chain instead of the mock", AMBER),
            ("SOLANA_PROGRAM_ID", "which program to talk to", SOFT),
            ("SOLANA_RPC_URL", "which door to the network (public, or a keyed one)", SOFT),
            ("SOLANA_AUTHORITY_KEYPAIR_JSON", "the backend's signing key. SECRET.", RED),
            ("CRON_SECRET", "password the timer must send. SECRET.", RED)]
    y = 148
    for k, v, f in rows:
        box(c, 0, y - 20, 215, 24, k, f, 7.8, align="left")
        text(c, 225, y - 12, v, 8, color=MUTED)
        y -= 29
    text(c, 0, 2, "Red = a leaked value lets someone act as your backend. Mark both Sensitive in Vercel.", 7.5, True, color=MUTED)


def d_verify(c):
    text(c, 0, 138, "How you know it worked: follow one order from the app to the explorer", 9.5, True, GREEN)
    for i, (t, f) in enumerate([("1  Run an order\naccept to complete", SOFT), ("2  /admin/payments\nrows are PENDING", AMBER), ("3  Trigger the timer\n(or wait a minute)", BLUE), ("4  Rows CONFIRMED\nwith a signature", DONE), ("5  Open it in the\ndevnet explorer", DONE)]):
        x = i * 100
        box(c, x, 50, 91, 56, t, f, 7.4)
        if i < 4:
            arrow(c, x + 91, 78, x + 100, 78)
    text(c, 0, 24, "Success = every row of a finished order is CONFIRMED: one commit, one per attestation, one settle.", 8, True)
    text(c, 0, 8, "A row that says FAILED is not a disaster: the reason is stored and the next tick retries it.", 8, color=MUTED)


def d_today(c):
    text(c, 0, 148, "TODAY: one file does everything, and forgets you on refresh", 8.8, True, GREEN)
    box(c, 0, 60, 150, 76, "app/page.tsx  (209 lines)\none URL: /\nevery role's screen sits inside it,\nshown or hidden by session.role", AMBER, 7.4)
    box(c, 175, 100, 145, 36, "Session in React state only\nrefresh = signed out", RED, 7.4)
    box(c, 175, 60, 145, 30, "swr installed, never used", GRAY, 7.4)
    box(c, 345, 100, 150, 36, "One 91-line stylesheet,\ntwo breakpoints (620, 768)", SOFT, 7.4)
    box(c, 345, 60, 150, 30, "No deep links: a lot, an order\nor a dispute has no address", RED, 7.4)
    text(c, 0, 36, "It works and is easy to demo. It cannot be bookmarked, shared by link, or opened from a phone notification.", 7.8, True)
    text(c, 0, 20, "Tomorrow's Stage 2 payment screens would make that single file much larger. Splitting now is cheaper than later.", 7.8, color=MUTED)


def d_routes(c):
    text(c, 0, 258, "PROPOSED ROUTES: one folder per role, one shared shell around all of them", 9, True, GREEN)
    box(c, 0, 218, 495, 28, "App shell: header + role-aware navigation + session + loading and error states", DONE, 8)
    cols = [("Public", "/\n/market\n/market/[lot]\n/login", SOFT), ("Buyer", "/buyer\n/buyer/requests/new\n/buyer/requests/[id]\n/buyer/orders", SOFT), ("Farmer", "/farmer\n/farmer/orders\n/farmer/farm", SOFT), ("Transporter", "/transporter\n/transporter/pools\n/transporter/shipments", SOFT), ("Admin", "/admin\n/admin/disputes\n/admin/users\n/admin/lots\n/admin/orders\n/admin/payments", AMBER)]
    for i, (head, body, f) in enumerate(cols):
        x = i * 100
        box(c, x, 176, 95, 26, head, GRAY, 8)
        box(c, x, 70, 95, 100, body, f, 6.7)
        arrow(c, x + 47, 218, x + 47, 202)
    box(c, 0, 24, 495, 34, "Shared by every role:  /orders/[id]  the order timeline: who did what, plus the Solana proof once Step A is live", BLUE, 7.8)
    text(c, 0, 8, "Square brackets are the changing part: /orders/ord_123 opens that order. Admin payments is the only brand-new screen.", 7.5, color=MUTED)


def d_responsive(c):
    text(c, 0, 228, "PHONE FIRST: the same pages, rearranged by screen width", 9, True, GREEN)
    box(c, 0, 24, 118, 190, "", GRAY, 8)
    box(c, 6, 190, 106, 18, "AgriLink            =", DONE, 6.8)
    for i in range(3):
        box(c, 8, 138 - i * 40 + 10, 102, 34, ["Fresh tomatoes\n40 kg", "Maize\n120 kg", "Mangoes\n15 kg"][i], SOFT, 6.6)
    box(c, 6, 28, 106, 18, "Home  Orders  Alerts  Me", AMBER, 6.4)
    text(c, 0, 10, "Under 768 px", 7.8, True)
    text(c, 0, 0, "1 column, bottom tabs, big buttons", 7, color=MUTED)
    box(c, 150, 24, 345, 190, "", GRAY, 8)
    box(c, 156, 190, 333, 18, "AgriLink     Market   Orders   Alerts   Account", DONE, 7.2)
    for r in range(2):
        for k in range(3):
            box(c, 160 + k * 110, 136 - r * 56 + 14, 102, 46, ["Fresh tomatoes\n40 kg", "Maize\n120 kg", "Mangoes\n15 kg", "Onions\n60 kg", "Carrots\n30 kg", "Spinach\n12 kg"][r * 3 + k], SOFT, 6.8)
    text(c, 150, 10, "768 px and wider", 7.8, True)
    text(c, 150, 0, "top navigation, 2 to 3 columns, tables allowed", 7, color=MUTED)


# ---------------------------------------------------------------- document
def build():
    out = Path(__file__).resolve().parents[1] / "output/pdf/step-a-and-frontend-plan.pdf"
    doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=50, rightMargin=50, topMargin=46, bottomMargin=46, title="Step A and the frontend plan")
    story = [
        p("Step A and the frontend plan", H1),
        p("Part 1 closes Phase 1 of the Solana work: switch the live app to devnet. Part 2 shows where that sits in the whole backend plan. Part 3 explains how it works inside. Part 4 is the step-by-step. Part 5 plans the frontend: split the single page into routes and make it work well on phones.", CAP),
        p("In plain words", H2),
        p("&bull; <b>The code for Solana is finished and tested.</b> What is left in Phase 1 is five settings on Vercel and a timer. No programming.<br/>"
          "&bull; <b>Nothing here uses real money.</b> Devnet is Solana's practice network; its coins are free.<br/>"
          "&bull; <b>The frontend does not have to wait.</b> Splitting it into routes can start now. Only its 'on-chain proof' badge needs Step A first."),
        Spacer(1, 4),
        Diagram(225, d_before_after),
        p("Figure 1. The buyer never waits for the blockchain. The API only writes a note; a timer delivers it.", CAP),
        p("What stays the same", H2),
        p("&bull; Orders, listings, matching and every page of the app behave as before.<br/>&bull; If Solana is slow or down, orders still go through. The failed note is kept and retried.<br/>&bull; Orders accepted before the switch have no commit note, so nothing is sent for them. That is intended."),
        PageBreak(),
        p("Part 2: where Step A fits", H1),
        p("The marketplace is built in stages. Each stage changes what the blockchain is trusted with. Step A is the bridge between 'it works on my laptop' and 'the live app really writes to a public ledger'. Every later stage assumes it is done, because it proves the real path (app, queue, key, network, program) end to end before anything valuable depends on it."),
        Spacer(1, 4),
        Diagram(240, d_roadmap),
        p("Figure 2. Backend stages on top, frontend phases below. The dashed arrow is the only hard link between them.", CAP),
        table([
            ("Step", "What it does", "Status", "Needs"),
            (b("Phase 1 code"), "Retry-safe sends, queue, cron route, 6 program tests, devnet deploy", "Done and pushed", "Nothing"),
            (b("Step A"), "Make the live backend actually use devnet", "<b>This guide</b>", "5 settings, redeploy, a timer"),
            (b("Stage 2"), "Token escrow: the program holds the buyer's payment and releases it by a split locked at order time (farmer, transporter, platform fee, capped)", "Planned", "Step A; Anchor 0.30.1 to 1.2; your decisions on fee, who sets transport price, silent-buyer rule, disputes"),
            (b("Stage 3"), "Pooled transport as a shared pot with a target, a deadline and refunds", "Planned", "Stage 2"),
            (b("Stage 4"), "Hardening: paid RPC, multisig upgrade authority, external audit, mainnet decision", "Planned", "Stages 2 and 3, real usage"),
        ], [70, 215, 65, 145]),
        p("Why not go straight to Stage 2?", H2),
        p("Escrow adds money, token accounts and a fee. If the plain path (queue, key, network) has a problem, you would be debugging it and the new money logic together. Step A is a one-hour check that removes the first set of unknowns."),
        PageBreak(),
        p("Part 3: how it works inside", H1),
        p("Two requests are involved, and keeping them apart is the whole idea. The first is the user's own tap and must be fast. The second is a timer that does the slow work."),
        Spacer(1, 4),
        Diagram(185, d_sequence),
        p("Figure 3. The dashed line separates what the user waits for from what happens later.", CAP),
        table([
            ("Step", "Where in the code", "Why it is built this way"),
            (b("2 to 3"), "orders/service.py advance(); payments/service.py on_status_changed and enqueue", "The payment note is written in the same database transaction as the order change, so there is never an order without its note, or the reverse."),
            (b("3"), "enqueue(): mock provider runs inline, a real chain leaves the row PENDING", "The mock is instant, so it needs no timer. A real network call can take seconds, so it must stay out of the user's request."),
            (b("5"), "payments/routes.py run_queue: answers only if the Authorization header equals Bearer CRON_SECRET", "The route is public on the internet, so it is locked by a password. If CRON_SECRET is not set it is switched off completely."),
            (b("6"), "process_queue(): rows locked with skip_locked, sorted commit, then attestations by position, then settle", "Two timers overlapping must not both send. Rows made in one request share a timestamp, so the order is stated, not left to chance."),
            (b("7"), "solana_adapter.py: reads the order's account first, sends only the missing step", "A reply can be lost after a transaction already landed. Reading first, plus the program's expected-position check, makes a repeat harmless."),
            (b("8"), "row status CONFIRMED, external_id = the signature", "The signature is the receipt: anyone can open it in the explorer."),
        ], [40, 230, 225]),
        p("What if a step fails?", H2),
        p("The row becomes FAILED with the reason stored (for example 'rate limited'). The order itself is never blocked or rolled back. The next timer tick retries every PENDING and FAILED row, oldest first, so a failed commit is repeated before the steps that depend on it."),
        PageBreak(),
        p("Part 4: do Step A", H1),
        p("4a. What is already done", H2),
        table([
            ("Item", "Status", "Detail"),
            (b("Backend signing key"), "Created", f"Public address {KEY}. File: ~/.config/solana/farmers-market-backend-devnet.json (permissions 600, outside the git repo). Devnet only. It is separate from your laptop wallet so a leak of one does not expose the other."),
            (b("Funding"), "1 SOL on devnet", "Sent from your laptop wallet. Each order needs about 0.00125 SOL of rent plus 0.000005 SOL per step, so 1 SOL covers hundreds of test orders."),
            (b("Program"), "Deployed", f"{PID}. 13 of 13 smoke checks pass on devnet."),
            (b("Queue and timer route"), "In the live code", "Pushed and deployed. The route stays locked (401) until CRON_SECRET exists."),
            (b("The five settings on Vercel"), "<b>NOT set</b>", "Blocked by the safety rules of my tool, because it means writing secrets to your Vercel account. You do this part."),
        ], [120, 85, 290]),
        p("4b. The five settings", H2),
        Diagram(190, d_vars),
        p("Figure 4. Three plain settings, two secrets.", CAP),
        table([
            ("Name", "Value", "Read by", "If it is wrong"),
            ("PAYMENT_PROVIDER", "solana", "payments/service.py get_provider", "Stays on the mock: nothing reaches the chain, no error"),
            ("SOLANA_PROGRAM_ID", PID, "solana_adapter.py from_env", "Rows FAILED: program not found"),
            ("SOLANA_RPC_URL", "https://api.devnet.solana.com (works, rate-limited; a keyed Helius URL is steadier)", "solana_adapter.py", "Rows FAILED with 429 or connection errors; retried next tick"),
            ("SOLANA_AUTHORITY_KEYPAIR_JSON", "the whole contents of the key file: 64 numbers in square brackets. <b>Sensitive</b>", "solana_adapter.py from_env", "Backend fails to start sending: rows FAILED with a key error"),
            ("CRON_SECRET", "a long random string you make up. <b>Sensitive</b>", "payments/routes.py run_queue", "Timer gets 401; rows stay PENDING"),
        ], [105, 160, 105, 125]),
        PageBreak(),
        p("4c. Choose one way to add them", H2),
        p("<b>Way 1: Vercel dashboard (easiest to see).</b> Open vercel.com, project <b>farmers-market-place</b> (the backend, not the -le5n one). Settings, then Environment Variables. For each row: type the name and value, tick <b>Production</b>, and for the two secrets tick <b>Sensitive</b>. Save."),
        term([("cmd", "cat ~/.config/solana/farmers-market-backend-devnet.json"), ("out", "[12,200,...64 numbers...,31]"), ("note", "# make a cron secret: run this, copy the output"), ("cmd", "python3 -c \"import secrets;print(secrets.token_urlsafe(32))\"")]),
        p("<b>Way 2: one command per setting.</b> Type each line into the Claude Code prompt starting with the exclamation mark, so it runs in this session with your approval. The value goes in through a pipe, so it is not typed into the command itself.", BODY),
        term([
            ("cmd", "cd ~/Dev/singapore/api"),
            ("cmd", "printf '%s' solana | npx vercel env add PAYMENT_PROVIDER production --project farmers-market-place"),
            ("cmd", f"printf '%s' {PID} | npx vercel env add SOLANA_PROGRAM_ID production --project farmers-market-place"),
            ("cmd", "printf '%s' https://api.devnet.solana.com | npx vercel env add SOLANA_RPC_URL production --project farmers-market-place"),
            ("cmd", "cat ~/.config/solana/farmers-market-backend-devnet.json | npx vercel env add SOLANA_AUTHORITY_KEYPAIR_JSON production --project farmers-market-place --sensitive"),
            ("cmd", "printf '%s' YOUR_RANDOM_STRING | npx vercel env add CRON_SECRET production --project farmers-market-place --sensitive"),
        ]),
        p("Check that the names landed (values stay hidden), then redeploy:", CAP),
        term([("cmd", "npx vercel env ls production --project farmers-market-place | grep -E 'SOLANA|CRON|PAYMENT'")]),
        p("Settings only apply to a new deployment. In the dashboard open the backend project, Deployments, the latest one, the three-dot menu, <b>Redeploy</b>. Wait for Ready.", BODY),
        p("4d. Prove it works", H2),
        Diagram(150, d_verify),
        p("Figure 5. One order, followed all the way to the explorer.", CAP),
        PageBreak(),
        p("Run these after the redeploy is Ready. Replace the placeholders.", BODY),
        term([
            ("note", "# get an admin token (this reseeds the demo data: fine while there are no real users)"),
            ("cmd", "curl -s -X POST 'https://farmers-market-place-nine.vercel.app/demo/seed?role=admin'"),
            ("note", "# in the web app: log in as buyer, create an order; farmer accepts; run it to COMPLETED"),
            ("note", "# then look at the notes:"),
            ("cmd", "curl -s -H 'Authorization: Bearer ADMIN_TOKEN' https://farmers-market-place-nine.vercel.app/admin/payments"),
            ("out", '[{"purpose":"order","status":"PENDING","provider":"solana",...}]'),
            ("note", "# trigger the timer by hand instead of waiting"),
            ("cmd", "curl -s -H 'Authorization: Bearer YOUR_CRON_SECRET' https://farmers-market-place-nine.vercel.app/payments/cron"),
            ("out", '{"processed":5}'),
        ]),
        p("Run the admin call again: the rows say CONFIRMED and each has an external_id. That is the transaction signature. Open it:", BODY),
        term([("cmd", "https://explorer.solana.com/tx/<external_id>?cluster=devnet")]),
        p("You should see Result: Success and in the logs <font face='Courier'>Instruction: CommitOrder</font>, <font face='Courier'>RecordAttestation</font> or <font face='Courier'>Settle</font>. The signer is the backend key address from 4a.", BODY),
        p("If something looks wrong", H2),
        table([
            ("What you see", "Meaning", "Fix"),
            (b("Timer call returns 401"), "CRON_SECRET missing, wrong, or you did not redeploy", "Check the name, re-add, redeploy, resend with the exact value"),
            (b("Rows stay PENDING"), "Nothing has called the timer yet", "Call /payments/cron by hand, or schedule it (below)"),
            (b("FAILED, 429"), "The public endpoint is rate-limiting", "Call the timer again, or use a keyed RPC URL"),
            (b("FAILED, insufficient funds"), "Backend key is out of devnet SOL", f"solana -u devnet transfer {KEY} 1"),
            (b("FAILED, AccountNotFound on attest or settle"), "That order's commit has not landed yet", "Nothing: the next tick replays commit first, then the rest, in order"),
            (b("Order screens show a 500"), "Database is missing migration 0004", "alembic upgrade head with the unpooled Neon URL"),
        ], [140, 170, 185]),
        p("Run the timer automatically", H2),
        p("A recurring call to <font face='Courier'>/payments/cron</font> with the header <font face='Courier'>Authorization: Bearer YOUR_CRON_SECRET</font>.<br/>&bull; <b>Vercel Cron</b>: a once-a-minute schedule needs a Pro plan; Hobby only allows daily and would reject the whole deploy otherwise. Tell me your plan and I will add it.<br/>&bull; <b>Any outside scheduler</b> that can send that header every minute, for example a GitHub Actions schedule.<br/>&bull; Until then, call it by hand when you test."),
        p("Undo, in two minutes", H2),
        p("Change <font face='Courier'>PAYMENT_PROVIDER</font> back to <font face='Courier'>mock</font> (or delete it) and redeploy. New orders go back to instant mock rows. Stored notes stay in the database and do no harm."),
        PageBreak(),
        p("Part 5: frontend planning phase", H1),
        p("Goal: replace the one-page demo with a proper multi-route app that works well on a phone, without breaking the live site on the way. This is a plan, not built yet.", CAP),
        Diagram(160, d_today),
        p("Figure 6. What the frontend is today (read from apps/web).", CAP),
        p("What is wrong with one page", H2),
        table([
            ("Problem", "Why it matters"),
            (b("No addresses"), "An order or a lot cannot be linked to, bookmarked or opened from a notification. Support questions become 'scroll down to My orders'."),
            (b("Session lost on refresh"), "On a phone, switching apps often reloads the page, which signs the user out. This is the biggest phone problem."),
            (b("All roles in one file"), "Every change risks another role's screen. Stage 2 would add checkout and fee screens to the same file."),
            (b("One long scroll on a small screen"), "Role cards stack into a very tall page; there is no navigation to jump between 'Orders' and 'Market'."),
            (b("Data loading in many functions"), "load* helpers called by hand after each action; easy to forget one and show stale data. The unused swr package is built for this."),
        ], [135, 360]),
        PageBreak(),
        p("The route map", H2),
        Diagram(270, d_routes),
        p("Figure 7. Every screen that exists today gets its own address. Only /admin/payments is new, and it uses the existing admin endpoints.", CAP),
        p("Where each existing section goes", H2),
        table([
            ("Today (section in page.tsx)", "Becomes"),
            ("Available produce (everyone)", "/market, with /market/[lot] for one lot and the order form"),
            ("Open buyer request, Match plan", "/buyer/requests/new, then /buyer/requests/[id] showing the match plan"),
            ("Create direct order, My orders", "Order form on /market/[lot]; list on /buyer/orders; one order on /orders/[id]"),
            ("Farmer order queue, Farm location", "/farmer/orders and /farmer/farm"),
            ("Pooled transport, Shipment orders", "/transporter/pools and /transporter/shipments"),
            ("Disputes, User moderation, Listing moderation, All orders", "/admin/disputes, /admin/users, /admin/lots, /admin/orders"),
            ("Demo role buttons", "/login (demo roles stay while the demo seed is on; real email login uses the existing /login and /register endpoints)"),
        ], [215, 280]),
        PageBreak(),
        p("Made for phones", H2),
        Diagram(245, d_responsive),
        p("Figure 8. Same content, two arrangements. Phone first, then widen.", CAP),
        table([
            ("Rule", "Detail"),
            (b("Mobile first CSS"), "Write the phone layout as the default; add wider layouts with min-width queries at 768 and 1100 px. Test at 360, 390, 768 and 1280 px."),
            (b("Bottom tab bar on phones"), "4 or 5 role-specific tabs within thumb reach; the top bar only on wider screens. One component, two arrangements."),
            (b("Touch targets"), "Buttons and links at least 44 px high; forms one column; inputs use the right keyboard (number, email) and 16 px text so iPhones do not zoom."),
            (b("Lists as cards"), "Orders and lots are cards on phones. Tables only above 768 px (admin screens)."),
            (b("No horizontal scroll"), "Long IDs wrap or truncate with the full value on tap. Images use fixed aspect ratios so the page does not jump while loading."),
            (b("Weak networks"), "Skeleton placeholders, plain error messages with a retry button, and no spinner that never ends. Server-fetched data cached per route."),
        ], [140, 355]),
        PageBreak(),
        p("How to build it, in order", H2),
        p("The old page stays at <font face='Courier'>/</font> and keeps working until the very end. Each phase below can be pushed on its own; if one goes wrong the live app is untouched."),
        table([
            ("Phase", "What", "Done when", "Needs backend?"),
            (b("F0 Prepare"), "Move api() to lib/api.ts, types to lib/types.ts, and add lib/session.tsx that saves the session in localStorage (wrapped in try/catch, as private mode can block it). Wire swr for data fetching or delete the dependency. No visible change.", "npm run build passes; the old page behaves identically; refresh keeps you signed in", "Maybe: a small GET /me so a stored token can be checked"),
            (b("F1 Shell"), "Root layout with header and role-aware navigation (top bar wide, bottom tabs narrow), /login, a guard that sends the wrong role to /login, shared loading and error components, mobile-first stylesheet.", "Each role sees only its own nav; direct links to protected routes work after refresh", "No"),
            (b("F2 Buyer"), "/market, /market/[lot], /buyer/requests/new and [id], /buyer/orders, /orders/[id] with the order timeline from the existing history endpoint.", "A buyer can place and follow an order using only the new routes, on a phone", "No"),
            (b("F3 Farmer and transporter"), "/farmer/orders, /farmer/farm, /transporter/pools, /transporter/shipments.", "Accept, pickup, deliver and pool confirm all work from the new routes", "No"),
            (b("F4 Admin and chain proof"), "/admin/disputes, users, lots, orders; /admin/payments (list, retry button); a 'Recorded on Solana' badge with explorer link on /orders/[id].", "An order that went through Step A shows its signature link; admin sees FAILED rows and can retry", "<b>Yes</b>: Step A live, plus a small GET /orders/{id}/payments visible to the order's participants"),
            (b("F5 Polish"), "Empty, loading and error states everywhere, keyboard and screen-reader pass, phone Lighthouse check, then replace the old page.tsx at / with the landing page.", "No dead code left in page.tsx; Lighthouse accessibility and performance over 90 on a phone profile", "No"),
        ], [70, 215, 130, 80]),
        p("Backend additions the frontend would ask for", H2),
        table([
            ("Addition", "Size", "Why"),
            (b("GET /me"), "about 5 lines", "Verify a stored token on app start and get the role; today the only way to learn the role is the demo seed reply"),
            (b("GET /orders/{id}/payments"), "about 15 lines", "Lets a buyer, farmer or transporter see the chain status of their own order; today only admins can read payment rows"),
            (b("NEXT_PUBLIC_SOLANA_CLUSTER"), "one env var", "Builds correct explorer links (devnet now, mainnet later) without hard-coding"),
        ], [150, 80, 265]),
        PageBreak(),
        p("Risks and open questions", H2),
        table([
            ("Risk", "Handling"),
            (b("Breaking the live demo"), "Old page stays at / until F5; ship one phase per push; check the Vercel preview URL of each phase before merging."),
            (b("localStorage tokens"), "Acceptable for this demo-grade bearer token; for real users plan an httpOnly cookie. Noted, not solved here."),
            (b("Demo seed in production"), "It wipes data and has no login. Turn ENABLE_DEMO_SEED off before real users and let /login use real accounts."),
            (b("Scope creep into design"), "Keep the AgriLink look; this phase is structure and responsiveness, not a redesign."),
        ], [140, 355]),
        p("Questions for you", H2),
        p("1. Who is the first real user on a phone: farmers, buyers or transporters? That decides whether F2 or F3 goes first.<br/>2. Should a farmer be able to add lots from the app? Today lots are created by the backend or seed only; it is a missing screen, not a layout task.<br/>3. Is the legacy page <font face='Courier'>web/index.html</font> (served by the API) still needed? I would delete it in F5.<br/>4. Languages: the new routes are a good moment to add one if a pilot country needs it."),
        p("The whole to-do, in order", H2),
        table([
            ("#", "Task", "Who", "Needs"),
            ("1", "Add the five Vercel settings (Part 4c) and redeploy", "You", "Vercel access"),
            ("2", "Run one order and check the explorer (Part 4d)", "Me, once you say go", "Step 1"),
            ("3", "Schedule the timer (Vercel Pro cron or an outside scheduler)", "You tell me the plan; I add it", "Step 1"),
            ("4", "Frontend F0 and F1 (shared code, shell, session)", "Me", "Nothing, can start now"),
            ("5", "Frontend F2 and F3 (buyer, farmer, transporter routes)", "Me", "F1"),
            ("6", "Small backend additions (GET /me, GET /orders/{id}/payments)", "Me", "Nothing"),
            ("7", "Frontend F4 and F5", "Me", "Steps 2 and 6"),
            ("8", "Decide fee, transport price rule, silent buyer, disputes, then start Stage 2", "You, then me", "Steps 1 to 3"),
        ], [25, 275, 100, 95]),
    ]
    doc.build(story)
    print(out)


if __name__ == "__main__":
    build()
