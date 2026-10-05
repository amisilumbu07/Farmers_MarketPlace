"""Builds output/pdf/todo-before-and-after-push.pdf: a plain checklist for the next session."""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, XPreformatted

GREEN, INK, MUTED = colors.HexColor("#2F6B3A"), colors.HexColor("#1B2A20"), colors.HexColor("#5B6B60")
H1 = ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=GREEN, spaceAfter=4)
H2 = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=12.5, leading=16, textColor=GREEN, spaceBefore=12, spaceAfter=4)
BODY = ParagraphStyle("b", fontName="Helvetica", fontSize=9.5, leading=13, textColor=INK)
SMALL = ParagraphStyle("s", parent=BODY, fontSize=8.6, leading=11.5, textColor=MUTED)
CODE = ParagraphStyle("c", fontName="Courier", fontSize=8, leading=10.4, textColor=colors.HexColor("#E7EFE9"))
STEP = ParagraphStyle("t", parent=BODY, fontName="Helvetica-Bold", fontSize=10.5, leading=14)


def code(s):
    t = Table([[XPreformatted(s, CODE)]], colWidths=[445])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#14201A")), ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    return t


def task(n, title, why, cmd=None, expect=None):
    body = [Paragraph(title, STEP), Paragraph(why, BODY)]
    if cmd:
        body += [Spacer(1, 3), code(cmd)]
    if expect:
        body += [Spacer(1, 3), Paragraph("<b>You should see:</b> " + expect, SMALL)]
    t = Table([[Paragraph(f"<b>[  ]</b>", ParagraphStyle("x", parent=BODY, fontName="Courier-Bold", fontSize=11)), body]], colWidths=[34, 461])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#C9D2CB")), ("BOTTOMPADDING", (0, 0), (-1, -1), 9), ("TOPPADDING", (0, 0), (-1, -1), 7)]))
    return KeepTogether(t)


def build():
    out = Path(__file__).resolve().parents[1] / "output/pdf/todo-before-and-after-push.pdf"
    doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=50, rightMargin=50, topMargin=46, bottomMargin=46, title="To-do: safe push and redeploy")
    s = [
        Paragraph("To-do for tomorrow: push and check", H1),
        Paragraph("Nothing is pushed yet. The commit (76cf151) is saved locally only. Do these in order. Tick each box.", BODY),
        Paragraph("The short version", H2),
        Paragraph("The website itself will not change. The only risk is that the database table the new code writes to (<font face='Courier'>external_transactions</font>) might not exist on Neon. Step 1 settles that before you push.", BODY),
        Paragraph("Before you push", H2),
        task(1, "Make sure the database is up to date (migration 0004)", "Needs the <b>unpooled</b> Neon URL (Neon, Connect, uncheck 'Connection pooling'). Run it from the project root. It is safe to run twice.",
             "export DATABASE_URL='paste-the-unpooled-url-here'\n.venv/bin/alembic upgrade head", "no error. If already done, no 'Running upgrade' line appears."),
        task(2, "Optional: slim the backend install", "Pillow, reportlab and pytest are not needed to run the API. Only do this if the Vercel build fails on size, not before.", None, "nothing to do unless the backend build fails."),
        Paragraph("Push", H2),
        task(3, "Push to main", "This starts a build of both Vercel projects. Wait for both to say Ready.", "git push", "Backend and frontend both Ready in the Vercel dashboard (a few minutes)."),
        Paragraph("After the build is Ready", H2),
        task(4, "Check the web page still loads", "Open the frontend, click Buyer demo, and make sure produce listings appear. No red error line.", "https://farmers-market-place-le5n.vercel.app", "listings and no error banner."),
        task(5, "Check the new payments table works", "<b>Warning:</b> this demo call wipes and reseeds all demo data. That is fine today, but not once real users exist. Step A gets an admin token, step B uses it.",
             "curl -s -X POST 'https://farmers-market-place-nine.vercel.app/demo/seed?role=admin'\n# copy the \"token\" value from the answer, then:\ncurl -s -H 'Authorization: Bearer PASTE_TOKEN' \\\n  https://farmers-market-place-nine.vercel.app/admin/payments",
             "<font face='Courier'>[]</font> (an empty list). A 500 error means step 1 was not done: go back and run the migration."),
        task(6, "Run one order end to end", "As a buyer create an order, then use the farmer, transporter and buyer demos to accept, pick up, deliver and complete it. Then run the step 5 payments call again.", None, "rows with status CONFIRMED and provider mock."),
        Paragraph("If something breaks", H2),
        task(7, "Roll back", "In Vercel, open the backend project, Deployments, pick the previous one and choose Instant Rollback. Or locally: <font face='Courier'>git revert 76cf151</font> then push. The new table is harmless to leave.", None, None),
        Paragraph("Later, not tomorrow", H2),
        Paragraph("&#8226; Commit your small page.tsx change ('Use lot' feedback). It is not in the commit.<br/>"
                  "&#8226; Before real users: set <font face='Courier'>ENABLE_DEMO_SEED</font> to 0 on the backend.<br/>"
                  "&#8226; To use devnet from production: add an RPC URL with an API key, plus PAYMENT_PROVIDER=solana and the key as an env secret. Not needed yet.<br/>"
                  "&#8226; Finish Phase 1: move the chain calls out of the web request, add Rust tests.<br/>"
                  "&#8226; Clean-up list from the ponytail audit (about 890 lines of old generators and a second UI).<br/>"
                  "&#8226; Pick a first country and fee level (open decisions in the feasibility PDF).", BODY),
        Spacer(1, 8),
        Paragraph("Already done and verified today: program deployed to devnet (13/13 smoke checks), commit saved, browser-check PDF written.", SMALL),
    ]
    doc.build(s)
    print(out)


if __name__ == "__main__":
    build()
