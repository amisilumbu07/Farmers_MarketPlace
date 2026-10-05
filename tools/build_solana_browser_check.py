"""Builds output/pdf/solana-devnet-browser-check.pdf. Addresses, signatures and bytes are from the real devnet deploy and smoke run of 2026-10-06."""
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.platypus import PageBreak, SimpleDocTemplate, Spacer

from build_solana_devnet_guide import AMBER, BLUE, DONE, PID, term
from build_solana_ideation import BODY, CAP, GRAY, GREEN, H1, H2, MUTED, SOFT, Diagram, arrow, b, box, p, table, text

EX = "https://explorer.solana.com"
DATA = "DnEweaToajxJ4nSojU854hSqCifDU31LazqxKCADVNZB"
AUTH = "HfJkE5oAGDFGgvftcxcPXFCV5m6CfvM1hAPHZRv6kSsF"
ORDER = "84k9j899AmqGjCWiLqxnk64oW7jgExfpwaRiBn5sFtPh"
DEPLOY = "eW2wAuTfvdG6KXUc26DvmFM7nRJHb6no49NjgxSmstTwNbrmrSD4bUHJV2kBrwNN5HbuCjN1BhnSxdirLPJobTT"
CAPTURE = "34UGk4thUq9tH2gSFRoanNw8anJfNfySmmmTmwpwzMFYNshar5qTXzC5Gw5ZwH6zfGhoicM8ZNFu5YsyRLnvvo5w"


def mono(s):
    return f"<font face='Courier' size='7.3'>{s}</font>"


def d_pages(c):
    text(c, 0, 168, "Four pages in the browser, each answers one question", 9.5, True, GREEN)
    items = [("1  Program page", "Is it on devnet?\nIs it runnable?", DONE), ("2  Deploy transaction", "Who put it there,\nand when?", SOFT), ("3  Order account", "What is stored\nfor one order?", SOFT), ("4  Settle transaction", "Did the program\nrun and succeed?", BLUE)]
    for i, (t, sub, fill) in enumerate(items):
        x = i * 126
        box(c, x, 70, 112, 74, f"{t}\n{sub}", fill, 8)
        if i < 3:
            arrow(c, x + 112, 107, x + 126, 107)
    box(c, 0, 5, 495, 42, "Everything here is read-only: the explorer only looks at the public ledger. It cannot change anything and needs no wallet or login.", AMBER, 8)


def d_program(c):
    text(c, 0, 188, "What the program page should show (labels as the explorer prints them)", 9, True, GREEN)
    rows = [("Address", PID[:22] + "...", "the id in lib.rs and .env"), ("Executable", "Yes", "it is a program, not data"), ("Owner", "BPFLoaderUpgradeab1e...", "the upgradeable loader"),
            ("Upgradeable", "Yes", "authority can ship fixes"), ("Upgrade Authority", AUTH[:14] + "...", "your wallet (see risks)"), ("Balance", "about 0.001 SOL", "just the small program account")]
    y = 164
    for k, v, note in rows:
        box(c, 0, y - 18, 120, 20, k, GRAY, 8, align="left")
        box(c, 125, y - 18, 190, 20, v, DONE, 7.6, align="left")
        text(c, 322, y - 11, note, 7.5, color=MUTED)
        y -= 24
    text(c, 0, 4, "The 1.03 SOL deposit sits in the separate ProgramData account (page 3), not in the program account.", 7.3, color=MUTED)


def d_bytes(c):
    text(c, 0, 108, "The order account is 118 bytes. The Data tab prints them in hex, 16 per row. Our bytes:", 8.5, True, GREEN)
    cells = [("0 to 7", "37 0b db 21\n24 88 28 b6", "Anchor tag", GRAY), ("8 to 79", "...", "hash, amount,\nauthority", GRAY), ("80", "01", "status", DONE), ("81 to 84", "02 00 00 00", "evidence count", DONE), ("85 to 117", "...", "evidence chain", GRAY)]
    x = 0
    for label, hexv, what, fill in cells:
        w = 100 if fill is DONE else 98
        box(c, x, 38, w, 44, hexv, fill, 8.2)
        text(c, x + w / 2, 26, label, 7.5, True, center=True)
        text(c, x + w / 2, 14, what.split("\n")[0], 7.2, color=MUTED, center=True)
        x += w + 1
    text(c, 0, 2, "status: 00 COMMITTED, 01 COMPLETED, 02 REFUNDED.  Count is little-endian: 02 00 00 00 means 2 attestations.", 7.3, color=MUTED)


def build():
    out = Path(__file__).resolve().parents[1] / "output/pdf/solana-devnet-browser-check.pdf"
    doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=50, rightMargin=50, topMargin=46, bottomMargin=46, title="Checking the Solana program on devnet in the browser")
    story = [
        p("Checking the program on devnet, in the browser", H1),
        p("No install, no wallet. Every address and signature below is real: the program was deployed on 2026-10-06 and the smoke test run against it. Paste each link into a browser, or open explorer.solana.com and search for the address.", CAP),
        Spacer(1, 4),
        Diagram(160, d_pages),
        p("Figure 1. Four pages answer four questions.", CAP),
        p("The one thing that goes wrong", H2),
        p(f"Explorer defaults to <b>mainnet</b>. A devnet address pasted there says <b>account not found</b>, which looks like a failed deploy but is not. Always add <font face='Courier'>?cluster=devnet</font> to the link, or use the network switcher at the top right and pick <b>Devnet</b>."),
        PageBreak(),
        p("1. Is the program on devnet?", H1),
        p(mono(f"{EX}/address/{PID}?cluster=devnet")),
        Spacer(1, 4),
        Diagram(196, d_program),
        p("Figure 2. If Executable says Yes and the owner is the upgradeable loader, the program is live on devnet.", CAP),
        p("Same page, other tabs", H2),
        table([
            ("Tab", "What you see", "Use it for"),
            (b("Transaction History"), "Every transaction that touched the program, newest first", "Proof it has been used: the smoke test's commits, attestations and settles"),
            (b("Anchor Program IDL"), "Empty or 'not found'", "Expected. We build with --no-idl and the adapter does not use an IDL"),
            (b("Security / Verified Build"), "Not verified", "Expected for now. A verified build is a Stage 4 hardening step"),
        ], [105, 190, 200]),
        p("Optional: a second opinion on Solscan", H2),
        p(mono(f"https://solscan.io/account/{PID}?cluster=devnet")),
        p("Solscan reads the same ledger. Useful when the Solana Explorer is slow or you want a different layout.", BODY),
        PageBreak(),
        p("2. Who deployed it, and what did it cost?", H1),
        p("The deploy transaction", H2),
        p(mono(f"{EX}/tx/{DEPLOY}?cluster=devnet")),
        p("Look for <b>Result: Success</b>, and under <b>Account Inputs</b> the upgrade authority wallet:", BODY),
        p(mono(f"{EX}/address/{AUTH}?cluster=devnet")),
        p("The program's code is stored in a separate <b>ProgramData</b> account. Its size, 202,920 bytes, matches the built file, and it holds the 1.03 SOL deposit:", BODY),
        p(mono(f"{EX}/address/{DATA}?cluster=devnet")),
        term([("note", "# the same facts from a terminal, if you want to cross-check"), ("cmd", f"solana -u devnet program show {PID}"), ("out", "Owner: BPFLoaderUpgradeab1e11111111111111111111111"), ("out", f"ProgramData Address: {DATA}"), ("out", f"Authority: {AUTH}"), ("out", "Data Length: 202920 (0x318a8) bytes")]),
        p("Real output.", CAP),
        PageBreak(),
        p("3. What is stored for one order?", H1),
        p("Each order gets its own 118-byte account, created by the program's commit step. This one was written by the last smoke run:", BODY),
        p(mono(f"{EX}/address/{ORDER}?cluster=devnet")),
        p("Open the page and the <b>Data</b> tab. The explorer cannot decode our layout (no IDL), so it shows raw hex. That is fine: we only need two spots.", BODY),
        Diagram(125, d_bytes),
        p("Figure 3. Byte 80 is the status and bytes 81 to 84 count the evidence hashes. The values shown are real, from this account.", CAP),
        table([
            ("Field on the page", "Expected value", "Meaning"),
            (b("Owner Program"), PID[:20] + "...", "Our program owns the account, so only it can change the bytes"),
            (b("Data Size"), "118 bytes", "Matches the layout in CLAUDE.md"),
            (b("Executable"), "No", "It is data, not a program"),
            (b("Byte 80"), "01", "COMPLETED: the order was captured"),
            (b("Bytes 81 to 84"), "02 00 00 00", "two attestations were recorded"),
        ], [120, 130, 245]),
        PageBreak(),
        p("4. Did the program run? (a transaction)", H1),
        p("The capture (settle) transaction from the same run:", BODY),
        p(mono(f"{EX}/tx/{CAPTURE}?cluster=devnet")),
        table([
            ("Look at", "Expected", "Why it matters"),
            (b("Result"), "Success", "Failed shows the error code; 0x1770, 0x1771, 0x1772 are our program's own"),
            (b("Fee"), "0.000005 SOL (5,000 lamports)", "The whole cost of recording a settlement"),
            (b("Program Instruction Logs"), "Instruction: Settle", "Proves OUR program ran, not just that something was sent"),
            (b("Compute units"), "3,384 of 200,000", "Tiny: the program only flips a status"),
        ], [125, 140, 230]),
        term([("note", "# program logs for that transaction (real output, via getTransaction)"), ("out", f"Program {PID[:8]}... invoke [1]"), ("out", "Program log: Instruction: Settle"), ("out", f"Program {PID[:8]}... consumed 3384 of 200000 compute units"), ("out", f"Program {PID[:8]}... success")]),
        p("Real output.", CAP),
        p("If you keep the Transaction History tab open and run the smoke test again, a new burst of rows appears within seconds: commit, two attestations, settle. That is the clearest live proof.", BODY),
        PageBreak(),
        p("Quick checklist and what the browser cannot tell you", H1),
        table([
            ("", "Check", "Pass looks like"),
            ("1", "Program page, devnet selected", "Executable Yes, Owner BPFLoaderUpgradeab1e..."),
            ("2", "Authority matches your wallet", "Upgrade Authority = " + AUTH[:12] + "..."),
            ("3", "Transaction History not empty", "rows for commit, attest, settle"),
            ("4", "An order account's Data tab", "118 bytes, owned by our program, byte 80 = 01"),
            ("5", "A transaction's logs", "Instruction: Settle, then success"),
        ], [25, 215, 255]),
        Spacer(1, 6),
        p("The browser cannot tell you", H2),
        table([
            ("Question", "Where to look instead"),
            ("Is the code the same as the repo?", "Not without a verified build. Compare locally: sha256sum target/deploy/marketplace_settlement.so against solana program dump"),
            ("Does the API actually use devnet?", "GET /admin/payments on the backend: CONFIRMED rows with signatures. Production still runs the mock provider"),
            ("Is the upgrade authority safe?", "It is the default wallet on this laptop. Before real users, move it to a multisig (Stage 4)"),
        ], [190, 305]),
    ]
    doc.build(story)
    print(out)


if __name__ == "__main__":
    build()
