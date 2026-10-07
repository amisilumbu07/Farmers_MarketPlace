"""Builds output/pdf/step-a-switch-production-to-devnet.pdf. Describes the Phase 1 closing step; values match the code in api/app/payments."""
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.platypus import PageBreak, SimpleDocTemplate, Spacer

from build_solana_devnet_guide import AMBER, BLUE, DONE, PID, term
from build_solana_ideation import BODY, CAP, GRAY, GREEN, H1, H2, MUTED, RED, SOFT, Diagram, arrow, b, box, p, table, text

KEY = "8dxtAKX8UUDCeuKbttr6foBXedV7ZU5X23iUXR9TAacA"


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


def build():
    out = Path(__file__).resolve().parents[1] / "output/pdf/step-a-switch-production-to-devnet.pdf"
    doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=50, rightMargin=50, topMargin=46, bottomMargin=46, title="Step A: switch production to Solana devnet")
    story = [
        p("Step A: switch the live app to Solana devnet", H1),
        p("This is the last part of Phase 1. The code is done and tested. What is left is settings, not programming. Nothing here moves real money: devnet coins are free test coins.", CAP),
        p("What changes, in one picture", H2),
        Diagram(225, d_before_after),
        p("Figure 1. The buyer never waits for the blockchain. The API only writes a note; a timer delivers it.", CAP),
        p("What stays the same", H2),
        p("&bull; Orders, listings, matching and every page of the app behave as before.<br/>&bull; If Solana is slow or down, orders still go through. The failed note is kept and retried.<br/>&bull; Orders accepted before the switch have no commit note, so nothing is sent for them. That is intended."),
        PageBreak(),
        p("Part 1: what is already done", H1),
        table([
            ("Item", "Status", "Detail"),
            (b("Backend signing key"), "Created", f"Public address {KEY}. File: ~/.config/solana/farmers-market-backend-devnet.json (permissions 600, outside the git repo). Devnet only."),
            (b("Funding"), "1 SOL on devnet", "Sent from your laptop wallet. Each order needs about 0.00125 SOL of rent plus 0.000005 SOL per step."),
            (b("Program"), "Deployed", f"{PID}, 13 of 13 smoke checks pass on devnet."),
            (b("Queue and timer route"), "In the live code", "Pushed to GitHub and deployed. The route stays locked (401) until CRON_SECRET exists."),
            (b("The five settings on Vercel"), "NOT set", "Blocked by the safety rules of my tool, because it means writing secrets to your Vercel account. You do this part."),
        ], [120, 85, 290]),
        p("Part 2: add the five settings", H1),
        Diagram(190, d_vars),
        p("Figure 2. Three plain settings, two secrets.", CAP),
        table([
            ("Name", "Value", "Sensitive?"),
            ("PAYMENT_PROVIDER", "solana", "no"),
            ("SOLANA_PROGRAM_ID", PID, "no"),
            ("SOLANA_RPC_URL", "https://api.devnet.solana.com  (works, but rate-limited; a keyed URL from Helius or similar is steadier)", "no"),
            ("SOLANA_AUTHORITY_KEYPAIR_JSON", "the whole contents of the key file: a list of 64 numbers in square brackets", "<b>yes</b>"),
            ("CRON_SECRET", "a long random string you make up", "<b>yes</b>"),
        ], [150, 270, 75]),
        PageBreak(),
        p("Choose one way to add them", H1),
        p("Way 1: Vercel dashboard (easiest to see)", H2),
        p("1. Open vercel.com, project <b>farmers-market-place</b> (the backend, not the -le5n one).<br/>2. Settings, then Environment Variables.<br/>3. For each row in the table: type the name and value, tick <b>Production</b>, and for the two secrets tick <b>Sensitive</b>. Save.<br/>4. Get the key contents in a terminal with the command below, copy the whole line, paste it as the value."),
        term([("cmd", "cat ~/.config/solana/farmers-market-backend-devnet.json"), ("out", "[12,200,...64 numbers...,31]"), ("note", "# make a cron secret: run this, copy the output"), ("cmd", "python3 -c \"import secrets;print(secrets.token_urlsafe(32))\"")]),
        p("Way 2: one command per setting, from your terminal", H2),
        p("Type each line into the Claude Code prompt starting with the exclamation mark, so it runs in this session with your approval. The value goes in through the pipe, so it is not typed into the command itself.", BODY),
        term([
            ("cmd", "cd ~/Dev/singapore/api"),
            ("cmd", "printf '%s' solana | npx vercel env add PAYMENT_PROVIDER production --project farmers-market-place"),
            ("cmd", f"printf '%s' {PID} | npx vercel env add SOLANA_PROGRAM_ID production --project farmers-market-place"),
            ("cmd", "printf '%s' https://api.devnet.solana.com | npx vercel env add SOLANA_RPC_URL production --project farmers-market-place"),
            ("cmd", "cat ~/.config/solana/farmers-market-backend-devnet.json | npx vercel env add SOLANA_AUTHORITY_KEYPAIR_JSON production --project farmers-market-place --sensitive"),
            ("cmd", "printf '%s' YOUR_RANDOM_STRING | npx vercel env add CRON_SECRET production --project farmers-market-place --sensitive"),
        ]),
        p("Check the names landed (values stay hidden):", CAP),
        term([("cmd", "npx vercel env ls production --project farmers-market-place | grep -E 'SOLANA|CRON|PAYMENT'")]),
        p("Then redeploy", H2),
        p("Settings only apply to a new deployment. In the Vercel dashboard open the backend project, Deployments, the latest one, the three-dot menu, <b>Redeploy</b>. Wait for Ready."),
        PageBreak(),
        p("Part 3: prove it works", H1),
        Diagram(150, d_verify),
        p("Figure 3. One order, followed all the way to the explorer.", CAP),
        p("Run these after the redeploy is Ready. Replace the two placeholders.", BODY),
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
        p("You should see Result: Success and in the logs <font face='Courier'>Instruction: CommitOrder</font>, <font face='Courier'>RecordAttestation</font> or <font face='Courier'>Settle</font>. The backend key address in the page is the one in Part 1.", BODY),
        PageBreak(),
        p("If something looks wrong", H1),
        table([
            ("What you see", "Meaning", "Fix"),
            (b("Timer call returns 401"), "CRON_SECRET missing, wrong, or you did not redeploy", "Check the name, re-add, redeploy, resend with the exact value"),
            (b("Rows stay PENDING"), "Nothing has called the timer yet", "Call /payments/cron by hand, or schedule it (see below)"),
            (b("FAILED, 'getSignatureStatuses 429'"), "The public endpoint is rate-limiting", "Call the timer again, or use a keyed RPC URL"),
            (b("FAILED, insufficient funds"), "Backend key is out of devnet SOL", f"solana -u devnet transfer {KEY} 1"),
            (b("FAILED, 'AccountNotFound' on attest or settle"), "That order's commit step has not landed yet", "Nothing: the next tick replays commit first, then the rest, in order"),
            (b("Order screens show a 500"), "Database is missing migration 0004", "alembic upgrade head with the unpooled Neon URL"),
        ], [140, 170, 185]),
        p("Run the timer automatically", H2),
        p("A recurring call to <font face='Courier'>/payments/cron</font> with the header <font face='Courier'>Authorization: Bearer YOUR_CRON_SECRET</font>. Two options:<br/>&bull; <b>Vercel Cron</b> (needs a Pro plan for a once-a-minute schedule; Hobby only allows daily and rejects the whole deploy otherwise). I will add the schedule once you tell me your plan.<br/>&bull; <b>Any outside scheduler</b> that can send that header every minute, for example a GitHub Actions schedule."),
        p("Undo, in two minutes", H2),
        p("Change <font face='Courier'>PAYMENT_PROVIDER</font> back to <font face='Courier'>mock</font> (or delete it) and redeploy. New orders go back to instant mock rows. Notes already stored stay in the database and do no harm."),
        Spacer(1, 4),
        p("Done when: one finished order shows CONFIRMED rows in /admin/payments and each signature opens as a Success transaction on the devnet explorer. That closes Phase 1; Stage 2 (token escrow) comes next.", CAP),
    ]
    doc.build(story)
    print(out)


if __name__ == "__main__":
    build()
