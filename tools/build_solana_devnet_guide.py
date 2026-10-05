"""Builds output/pdf/solana-devnet-testing-guide.pdf. Outputs marked 'real output' were captured on this machine."""
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import KeepTogether, PageBreak, SimpleDocTemplate, Spacer, Table, TableStyle, XPreformatted

from build_solana_ideation import AMBER, BLUE, BODY, CAP, GRAY, GREEN, H1, H2, INK, MUTED, RED, SOFT, W, Diagram, arrow, b, box, p, table, text

DONE = colors.HexColor("#CFE6C8")
PID = "9ZZ5bejD4NdPr7zf9covKHDig6tcqh628Fdtrm4mT9MU"
TERM = ParagraphStyle("term", fontName="Courier", fontSize=7.3, leading=9.4, textColor=colors.HexColor("#E7EFE9"))
KIND = {"cmd": "#7EE0A0", "out": "#E7EFE9", "note": "#9FB3A6", "bad": "#F2A39B"}


def term(lines, title=None):
    """lines: (kind, text) tuples. Dark terminal block; 'cmd' lines get a $ prompt."""
    rows = []
    for kind, s in lines:
        prefix = "$ " if kind == "cmd" else ""
        rows.append(f'<font color="{KIND[kind]}">{escape(prefix + s)}</font>')
    t = Table([[XPreformatted("\n".join(rows), TERM)]], colWidths=[W])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#14201A")), ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                           ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7), ("ROUNDEDCORNERS", [5, 5, 5, 5])]))
    return t


# ---------------- diagrams ----------------
def d_path(c):
    text(c, 0, 168, "The whole path, in order", 9.5, True, GREEN)
    steps = [("1  Check the network", "Is devnet alive?"), ("2  Fund a wallet", "Free test SOL"), ("3  Build", "anchor build"), ("4  Deploy", "to devnet"), ("5  Smoke test", "all the checks"), ("6  Read results", "in the explorer")]
    for i, (t, sub) in enumerate(steps):
        x = i * 84
        box(c, x, 85, 75, 60, f"{t}\n{sub}", SOFT if i < 4 else (DONE if i == 4 else BLUE), 7.6)
        if i < 5:
            arrow(c, x + 75, 115, x + 84, 115)
    text(c, 0, 62, "Steps 1 to 5 happen in your terminal. Step 6 happens in your browser.", 8, color=MUTED)
    box(c, 0, 5, 495, 42, "Do the whole path on a local validator first: it is free, instant and offline. Then repeat on devnet, where the network is shared and public.", AMBER, 8)


def d_where(c):
    box(c, 0, 105, 150, 62, "Your terminal\nsolana CLI, smoke.py, the API", SOFT)
    box(c, 175, 105, 145, 62, "RPC endpoint\napi.devnet.solana.com or your provider", AMBER)
    box(c, 345, 105, 150, 62, "Devnet validators\nthe shared test network", BLUE)
    arrow(c, 150, 136, 175, 136)
    arrow(c, 320, 136, 345, 136)
    box(c, 345, 10, 150, 52, "Explorer / Solscan\nread-only view in your browser", GRAY)
    arrow(c, 420, 62, 420, 105, "reads", MUTED)
    box(c, 0, 10, 150, 52, "Faucet\ngives free test SOL (devnet only)", GRAY)
    arrow(c, 75, 62, 75, 105, "sends SOL", MUTED)
    text(c, 175, 40, "Mainnet has the same shape", 8, True, GREEN)
    text(c, 175, 28, "but real money. Not yet.", 8, False, GREEN)


def d_smoke(c):
    text(c, 0, 178, "What the smoke test proves: green passes, grey does nothing on purpose, red is refused on purpose", 8.5, True, GREEN)
    items = [
        ("commit_order", DONE), ("attest #0", DONE), ("attest #0 again\nno-op", GRAY), ("attest #1", DONE),
        ("attest at taken slot\nREFUSED 0x1772", RED), ("capture\nCOMPLETED", DONE), ("capture again\nno-op", GRAY), ("refund after capture\nREFUSED (conflict)", RED),
        ("attest after settle\nREFUSED 0x1770", RED),
    ]
    for i, (label, fill) in enumerate(items):
        row, col = divmod(i, 5)
        x, y = col * 99, 115 - row * 62
        box(c, x, y, 90, 46, f"{i + 1}  {label}", fill, 7.3)
    text(c, 0, 20, "Steps 5, 8 and 9 are the cases that were untested before Phase 1.", 8, color=MUTED)
    text(c, 0, 9, "Retries that already landed are now harmless, and conflicting outcomes are refused.", 8, color=MUTED)


def d_layout(c):
    text(c, 0, 118, "What one order record looks like on chain (118 bytes). Amber = what the checker reads.", 8.5, True, GREEN)
    cells = [("discriminator", "bytes 0-7", GRAY), ("authority", "8-39", GRAY), ("order_hash", "40-71", GRAY), ("amount (cents)", "72-79", GRAY),
             ("status", "80", AMBER), ("attest. count", "81-84", AMBER), ("evidence chain", "85-116", GRAY), ("bump", "117", GRAY)]
    for i, (name, rng, fill) in enumerate(cells):
        box(c, i * 62, 45, 57, 50, f"{name}\n{rng}", fill, 6.6)
    text(c, 0, 24, "status: 0 = COMMITTED, 1 = COMPLETED, 2 = REFUNDED.   count: how many evidence hashes were recorded.", 7.8, color=MUTED)
    text(c, 0, 13, "evidence chain: each new value is sha256(previous value + new hash).", 7.8, color=MUTED)


# ---------------- content ----------------
LOCAL_OUT = [
    ("out", "cluster http://127.0.0.1:8899"),
    ("out", f"program {PID}"),
    ("out", "authority EDQ8vRwX...kVS7eSK"),
    ("out", "order smoke_1791221002"),
    ("out", "order account CkpRiw21WoZHUwCVci1mjPCGJy5Giy1tWCmk4erkKYeB"),
    ("out", ""),
    ("out", "PASS  order not on chain yet: UNKNOWN"),
    ("out", "PASS  commit_order: https://explorer.solana.com/tx/2nBvEA2c...?cluster=custom&customUrl=..."),
    ("out", "PASS  status after commit: COMMITTED"),
    ("out", "PASS  commit again is a no-op: existing"),
    ("out", "PASS  attestation 0: https://explorer.solana.com/tx/Qi2TfGv5...?cluster=custom&customUrl=..."),
    ("out", "PASS  attestation 0 retried is a no-op: existing"),
    ("out", "PASS  attestation 1: https://explorer.solana.com/tx/5LC2auvi...?cluster=custom&customUrl=..."),
    ("out", "PASS  attestation at a taken position, sent raw (refused with 0x1772): True"),
    ("out", "PASS  capture: https://explorer.solana.com/tx/5h7mH5GjwvaCGZYBQ...?cluster=custom&customUrl=..."),
    ("out", "PASS  status after capture: COMPLETED"),
    ("out", "PASS  capture again is a no-op: existing"),
    ("out", "PASS  refund after capture (refused with cannot become REFUNDED): True"),
    ("out", "PASS  attestation after settlement, sent raw (refused with 0x1770): True"),
    ("out", ""),
    ("out", "all checks passed"),
]

WEB_CHECKERS = [
    ("Tool", "Link", "Use it for"),
    (b("Solana Explorer"), "explorer.solana.com/?cluster=devnet", "Paste a transaction signature, program id or account address. Shows instructions, logs, and errors."),
    (b("Solscan"), "solscan.io/?cluster=devnet", "Same idea with a different interface. Handy as a second opinion."),
    (b("Solana status page"), "status.solana.com", "Official status. <b>Covers Mainnet Beta only</b>; it does not list devnet, so use the commands above for devnet."),
    (b("Devnet faucet"), "faucet.solana.com", "Free devnet SOL. Limit is 2 requests per 8 hours without signing in; a GitHub login raises it."),
]

ERRORS = [
    ("What you see", "What it means", "What to do"),
    ("Attempt to debit an account but found no record of a prior credit", "The authority wallet has no SOL on this cluster.", "solana -u devnet airdrop 2 &lt;address&gt;, or use the web faucet."),
    ("airdrop request failed / 429", "Devnet faucet rate limit.", "Wait, use faucet.solana.com, or test on the local validator."),
    ("custom program error: 0x1770", "6000 AlreadySettled: the order is finished.", "Expected when testing; in production it means a duplicate settle."),
    ("custom program error: 0x1771", "6001 BadOutcome: outcome was not 1 or 2.", "Only the adapter sends outcomes; this signals a bug."),
    ("custom program error: 0x1772", "6002 UnexpectedCount: that evidence slot is taken or out of order.", "Expected when replaying; the adapter now skips these."),
    ("Allocate: account already in use", "commit_order was sent twice for one order.", "The adapter checks first; this appears only with raw sends."),
    ("TimeoutError: not confirmed", "The transaction may or may not have landed.", "Safe to retry now: the adapter reads the chain first."),
    ("ProgramAccountNotFound / program does not exist", "The cluster you are talking to does not have our program. On localhost, the validator was started without --bpf-program, or an older validator or Surfpool is still using port 8899.", "Stop everything on 8899, restart with the Terminal A commands, check solana -u localhost program show. The smoke script now stops with this message."),
    ("authority is not the key you expected", "The environment variable and the command were split by a blank line or a missing backslash, so the default wallet was used.", "Put SOLANA_AUTHORITY_KEYPAIR=... on the same line as the python command (the guide now does)."),
    ("Error: Building IDL failed", "The nightly Rust on this machine breaks an IDL helper.", "Build with anchor build --no-idl. The adapter does not use the IDL."),
    ("insufficient funds for rent (deploy)", "Deploying needs about 1.4 SOL of rent.", "Fund the deployer wallet first."),
]


def build():
    out = Path(__file__).resolve().parents[1] / "output/pdf/solana-devnet-testing-guide.pdf"
    doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=50, rightMargin=50, topMargin=46, bottomMargin=46, title="Testing the Solana program on devnet")
    story = [
        p("Testing the Solana program on devnet", H1),
        p("A terminal guide. Green blocks are commands to type. Output marked <b>real output</b> was captured on this machine; output marked <b>expected</b> was not run here.", CAP),
        Spacer(1, 4),
        Diagram(180, d_path),
        p("Figure 1. The path from a clean machine to a verified program.", CAP),
        p("Three places you can test", H2),
        table([
            ("", "Local validator", "Devnet", "Mainnet"),
            (b("Cost"), "Free", "Free test SOL", "Real money"),
            (b("Speed"), "Instant, offline", "Real network, a few seconds per step", "Real network"),
            (b("Shared with others"), "No, only you", "Yes, public", "Yes, public"),
            (b("Use it for"), "Every code change", "Proving it works on a real cluster", b("Not yet.") + " After audit and pilot."),
        ], [95, 120, 150, 130]),
        p("Check your tools first", H2),
        term([("cmd", "solana --version"), ("out", "solana-cli 3.1.13 (src:437252fc; feat:534737035, client:Agave)"), ("cmd", "anchor --version"), ("out", "anchor-cli 0.30.1")]),
        p("Real output. Other versions usually work; if the build fails, compare against these.", CAP),
        PageBreak(),
        p("Step 1: Is devnet alive? (the network checker)", H1),
        p("These read-only commands cost nothing and need no wallet. Run them any time something looks wrong: if they fail, the problem is the network or your connection, not our program."),
        Spacer(1, 4),
        term([
            ("cmd", "solana -u devnet cluster-version"), ("out", "4.4.0-beta.0"),
            ("cmd", "solana -u devnet epoch-info"),
            ("out", "Block height: 495049569"), ("out", "Slot: 507805687"), ("out", "Epoch: 1175"),
            ("out", "Epoch Completed Percent: 47.613%"), ("out", "Epoch Completed Time: 13h 33m 37s/1day 4h 35m 5s (15h 1m 28s remaining)"),
            ("cmd", "solana -u devnet block-height"), ("out", "495049569"),
            ("cmd", "curl -s https://api.devnet.solana.com -X POST -H 'Content-Type: application/json' \\"),
            ("cmd", "     -d '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"getHealth\"}'"),
            ("out", "{\"jsonrpc\":\"2.0\",\"result\":\"ok\",\"id\":1}"),
        ]),
        p("Real output. A healthy network answers within a second, <b>block height keeps rising</b> when you run it twice a few seconds apart, and getHealth says ok.", CAP),
        p("Optional: solana -u devnet ping -c 3 sends tiny real transactions and measures confirmation time. It needs a funded wallet.", BODY),
        Spacer(1, 6),
        Diagram(175, d_where),
        p("Figure 2. What talks to what. The RPC endpoint is the only thing you may swap later (setting SOLANA_RPC_URL).", CAP),
        p("Checkers in your browser", H2),
        table(WEB_CHECKERS, [95, 130, 270]),
        PageBreak(),
        p("Step 2: A wallet with test SOL", H1),
        p("Add -u devnet to each command instead of changing your global setting. Your CLI is currently pointed at a devnet provider, so a global change would only matter if you also use other clusters."),
        Spacer(1, 4),
        term([
            ("cmd", "solana address"), ("out", "<your wallet address>"),
            ("cmd", "solana -u devnet balance"), ("out", "5 SOL"),
            ("note", "# below 2 SOL? ask the faucet (2 tries per 8 hours without a GitHub login):"),
            ("cmd", "solana -u devnet airdrop 2"), ("out", "Requesting airdrop of 2 SOL ... 7 SOL  (expected)"),
        ]),
        p("The balance line is real output from your wallet. A deploy needs about 1.4 SOL of rent plus a few cents of fees, so 5 SOL is plenty.", CAP),
        p("Step 3: Test locally first", H1),
        p("Open <b>two terminals</b>. Terminal A runs a private test network with our program already loaded. Terminal B runs the checks."),
        Spacer(1, 4),
        term([
            ("note", "# Terminal A  (leave it running; stop any other validator or Surfpool first)"),
            ("cmd", "cd ~/Dev/singapore"),
            ("cmd", f"ID={PID}"),
            ("cmd", "SO=blockchain/solana/target/deploy/marketplace_settlement.so"),
            ("cmd", "solana-test-validator --reset --ledger /tmp/sv-ledger --bpf-program $ID $SO"),
            ("note", ""),
            ("note", "# Terminal B  (paste one line at a time, with no blank lines between them)"),
            ("cmd", "cd ~/Dev/singapore"),
            ("cmd", "solana-keygen new --no-bip39-passphrase --force -o /tmp/auth.json"),
            ("cmd", "solana -u localhost airdrop 5 $(solana-keygen pubkey /tmp/auth.json)"),
            ("cmd", f"solana -u localhost program show {PID}"),
            ("cmd", "SOLANA_AUTHORITY_KEYPAIR=/tmp/auth.json .venv/bin/python blockchain/solana/scripts/smoke.py"),
        ]),
        p("The program show line must print a Program Id before you continue; if it says the program does not exist, the validator in terminal A was not started with --bpf-program. Stop the validator with Ctrl+C when you finish. The throwaway key never touches your real wallet; do not reuse its seed phrase for anything real.", CAP),
        PageBreak(),
        p("What a passing run looks like", H1),
        p("This is real output from the run done while writing this guide, against the rebuilt program. Links are shortened here; in your terminal each one opens the transaction in the explorer."),
        Spacer(1, 4),
        term(LOCAL_OUT),
        Spacer(1, 8),
        Diagram(185, d_smoke),
        p("Figure 3. The checks, grouped. Red boxes are supposed to be refused: if one is accepted, the script stops and says so.", CAP),
        PageBreak(),
        p("Step 4: Build the program", H1),
        term([
            ("cmd", "cd blockchain/solana"),
            ("cmd", "anchor build --no-idl"),
            ("out", "Finished `release` profile [optimized] target(s) in 0.33s   (real output)"),
            ("cmd", "solana-keygen pubkey target/deploy/marketplace_settlement-keypair.json"),
            ("out", PID),
        ]),
        p("The key printed must equal the program id written in the code (declare_id!). The keypair file is git-ignored; never commit it, because whoever holds it can claim the program address.", CAP),
        p("Step 5: Deploy to devnet", H1),
        term([
            ("cmd", "solana program deploy target/deploy/marketplace_settlement.so \\"),
            ("cmd", "    --program-id target/deploy/marketplace_settlement-keypair.json -u devnet"),
            ("out", f"Program Id: {PID}   (expected)"),
            ("cmd", f"solana program show {PID} -u devnet"),
            ("out", "Program Id: 9ZZ5...mT9MU"), ("out", "Owner: BPFLoaderUpgradeab1e11111111111111111111111"),
            ("out", "Authority: <your wallet address>      Data Length: 202920 (0x318a8) bytes"),
        ]),
        p("The show output is real on the local validator; on devnet the Authority is your wallet, which is what lets you upgrade it. Running the same deploy command again upgrades the program in place.", CAP),
        p("Good to know before you deploy", H2),
        p("&bull; <b>It is public.</b> Anyone can read a devnet program and call it. That is fine for testing, since only the authority key can change a record."),
        p("&bull; <b>Rent is locked, not spent.</b> Roughly 1.4 SOL stays locked in the program account. <font face='Courier'>solana program close</font> can recover it, but a closed program id can never be reused. Check <font face='Courier'>solana program close --help</font> before using it."),
        p("&bull; <b>Version skew is normal.</b> Devnet reported 4.4.0-beta.0 while your CLI is 3.1.13; that does not affect this program."),
        PageBreak(),
        p("Step 6: Run the smoke test on devnet", H1),
        term([
            ("cmd", "cd ~/Dev/singapore"),
            ("cmd", "SOLANA_RPC_URL=https://api.devnet.solana.com \\"),
            ("cmd", "    .venv/bin/python blockchain/solana/scripts/smoke.py"),
            ("out", "(the same PASS lines as before; the links end in ?cluster=devnet)   (expected)"),
        ]),
        p("It uses your default wallet (~/.config/solana/id.json) as the authority because the script's default is that path. Each commit, attest and capture costs a fraction of a cent.", CAP),
        p("Step 7: Read the results in the explorer", H2),
        p("1. Click or paste any link from the output. The transaction page shows <b>Success</b>, the instruction name and the program logs."),
        p("2. Paste the program id into the explorer's search box (with the devnet network selected) to see the program and its recent transactions."),
        p("3. The run prints an <b>order account</b> line near the top. That address holds the order's record; look it up:"),
        term([
            ("cmd", "solana account <order account address> -u devnet"),
            ("out", "Owner: 9ZZ5bejD4NdPr7zf9covKHDig6tcqh628Fdtrm4mT9MU"),
            ("out", "Length: 118 (0x76) bytes"),
            ("out", "0050:   01 02 00 00  00 bf fe 45  1a 63 b1 48  7d 45 42 94   .......E.c.H}EB."),
            ("note", "         ^^ status = 01 (COMPLETED)    ^^ ^^ ^^ ^^ count = 02 00 00 00 (two evidence hashes)"),
        ]),
        p("Real output from a local run, trimmed. Byte 80 (row 0050, first value) is the status; bytes 81 to 84 are the evidence count, stored smallest byte first.", CAP),
        Spacer(1, 6),
        Diagram(125, d_layout),
        p("Figure 4. Bytes 80 and 81 to 84 are the status and the evidence count: the two values the adapter checks before it resends anything.", CAP),
        p("Watch the program work live", H2),
        term([("note", "# in a second terminal, then run the smoke test again"), ("cmd", f"solana logs {PID} -u devnet"), ("out", "Program log: Instruction: CommitOrder   (expected)")]),
        PageBreak(),
        p("When something goes wrong", H1),
        table(ERRORS, [155, 165, 175]),
        p("The three custom program errors are the program's own: 6000 = 0x1770, 6001 = 0x1771, 6002 = 0x1772 (6000 is 0x1770 in hexadecimal).", CAP),
        p("Optional: test through the API", H2),
        p("Start the API with the Solana provider switched on, then run an order through accept, pickup, delivery and complete in the demo app. Every step leaves a row you can read at <font face='Courier'>GET /admin/payments</font> (admin token from <font face='Courier'>/demo/seed?role=admin</font>): <b>CONFIRMED</b> with a signature, or <b>FAILED</b> with the reason, which <font face='Courier'>POST /admin/payments/retry</font> replays safely. This route was not run in this session; the smoke test above covers the program itself."),
        Spacer(1, 4),
        term([
            ("cmd", "docker compose up -d                       # local database"),
            ("cmd", "PAYMENT_PROVIDER=solana SOLANA_RPC_URL=https://api.devnet.solana.com \\"),
            ("cmd", f"  SOLANA_PROGRAM_ID={PID} \\"),
            ("cmd", "  SOLANA_AUTHORITY_KEYPAIR=$HOME/.config/solana/id.json \\"),
            ("cmd", "  .venv/bin/uvicorn app.main:app --app-dir api --reload"),
        ]),
        p("Next after this guide: deploy to devnet, run the smoke test there, then move the sending into a worker so it leaves the web request (the rest of Phase 1).", BODY),
    ]
    doc.build(story)
    print(out)


if __name__ == "__main__":
    build()
