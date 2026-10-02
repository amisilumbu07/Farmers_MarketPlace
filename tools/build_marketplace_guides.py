from pathlib import Path
from textwrap import wrap

from PIL import Image as PILImage, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "pdf"
TMP = ROOT / "tmp" / "pdfs" / "marketplace-guides"
OUT.mkdir(parents=True, exist_ok=True)
TMP.mkdir(parents=True, exist_ok=True)

GREEN = colors.HexColor("#19764A")
PURPLE = colors.HexColor("#5733A5")
INK = colors.HexColor("#17221B")
MUTED = colors.HexColor("#66736A")
PAPER = colors.HexColor("#F5F8F3")
LINE = colors.HexColor("#DDE7DC")
AMBER = colors.HexColor("#B45F06")
RED = colors.HexColor("#B42318")
WHITE = colors.white

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
if Path(FONT).exists():
    pdfmetrics.registerFont(TTFont("Guide", FONT))
    pdfmetrics.registerFont(TTFont("Guide-Bold", FONT_BOLD))
    BASE_FONT, BOLD_FONT = "Guide", "Guide-Bold"
else:
    BASE_FONT, BOLD_FONT = "Helvetica", "Helvetica-Bold"


def make_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitleX", fontName=BOLD_FONT, fontSize=30, leading=35, textColor=WHITE, alignment=TA_LEFT, spaceAfter=12))
    styles.add(ParagraphStyle(name="SubtitleX", fontName=BASE_FONT, fontSize=12, leading=18, textColor=colors.HexColor("#E9E1FA"), spaceAfter=12))
    styles.add(ParagraphStyle(name="H1X", fontName=BOLD_FONT, fontSize=22, leading=27, textColor=PURPLE, spaceBefore=5, spaceAfter=10))
    styles.add(ParagraphStyle(name="H2X", fontName=BOLD_FONT, fontSize=15, leading=20, textColor=GREEN, spaceBefore=8, spaceAfter=6))
    styles.add(ParagraphStyle(name="H3X", fontName=BOLD_FONT, fontSize=11.5, leading=15, textColor=INK, spaceBefore=5, spaceAfter=4))
    styles.add(ParagraphStyle(name="BodyX", fontName=BASE_FONT, fontSize=9.4, leading=14, textColor=INK, spaceAfter=6))
    styles.add(ParagraphStyle(name="SmallX", fontName=BASE_FONT, fontSize=7.6, leading=11, textColor=MUTED, spaceAfter=4))
    styles.add(ParagraphStyle(name="BulletX", fontName=BASE_FONT, fontSize=9.2, leading=13.5, textColor=INK, leftIndent=13, firstLineIndent=-8, bulletIndent=3, spaceAfter=4))
    styles.add(ParagraphStyle(name="CodeX", fontName="Courier", fontSize=7.5, leading=10.5, textColor=colors.HexColor("#F5F5F5"), backColor=colors.HexColor("#25252A"), borderPadding=7, spaceBefore=3, spaceAfter=7))
    styles.add(ParagraphStyle(name="CellX", fontName=BASE_FONT, fontSize=7.5, leading=10, textColor=INK))
    styles.add(ParagraphStyle(name="CellBoldX", fontName=BOLD_FONT, fontSize=7.5, leading=10, textColor=INK))
    styles.add(ParagraphStyle(name="CenterX", fontName=BASE_FONT, fontSize=8.2, leading=12, textColor=MUTED, alignment=TA_CENTER))
    return styles


S = make_styles()


def P(text, style="BodyX"):
    return Paragraph(text, S[style])


def bullet(text):
    return Paragraph(f"- {text}", S["BulletX"])


def code(text):
    return Paragraph(text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>"), S["CodeX"])


def callout(title, text, tone="info"):
    palette = {"info": (colors.HexColor("#EDE7FA"), PURPLE), "ok": (colors.HexColor("#E7F4EB"), GREEN), "warn": (colors.HexColor("#FFF3DA"), AMBER), "bad": (colors.HexColor("#FDECEA"), RED)}
    bg, edge = palette[tone]
    table = Table([[P(title, "CellBoldX"), P(text, "CellX")]], colWidths=[35 * mm, 137 * mm])
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), bg), ("BOX", (0, 0), (-1, -1), 1, edge), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7), ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    return table


def data_table(headers, rows, widths=None):
    data = [[P(str(h), "CellBoldX") for h in headers]] + [[P(str(v), "CellX") for v in row] for row in rows]
    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PURPLE), ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("GRID", (0, 0), (-1, -1), .5, LINE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, PAPER]),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def page_decor(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(PURPLE)
    canvas.rect(0, h - 13 * mm, w, 13 * mm, fill=1, stroke=0)
    canvas.setFont(BOLD_FONT, 8)
    canvas.setFillColor(WHITE)
    canvas.drawString(18 * mm, h - 8.5 * mm, "HARVEST HUB - FARMER MARKETPLACE")
    canvas.setStrokeColor(LINE)
    canvas.line(18 * mm, 14 * mm, w - 18 * mm, 14 * mm)
    canvas.setFillColor(MUTED)
    canvas.setFont(BASE_FONT, 7)
    canvas.drawString(18 * mm, 9 * mm, "Generated from the repository on 2 October 2026")
    canvas.drawRightString(w - 18 * mm, 9 * mm, f"Page {doc.page}")
    canvas.restoreState()


def cover(story, title, subtitle, label):
    story.extend([Spacer(1, 26 * mm)])
    block = Table([[P(label.upper(), "SmallX")], [P(title, "TitleX")], [P(subtitle, "SubtitleX")]], colWidths=[174 * mm])
    block.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), PURPLE), ("TEXTCOLOR", (0, 0), (-1, -1), WHITE), ("LEFTPADDING", (0, 0), (-1, -1), 16), ("RIGHTPADDING", (0, 0), (-1, -1), 16), ("TOPPADDING", (0, 0), (-1, 0), 12), ("BOTTOMPADDING", (0, -1), (-1, -1), 16)]))
    story.extend([block, Spacer(1, 12 * mm), callout("Current database status", "Not reachable on this machine. PostgreSQL port 5432 refused the connection, and the local Docker daemon requires administrator access. The schema and deployment configuration are ready, but rows could not be inserted during this check.", "warn"), Spacer(1, 8 * mm), P("Repository: /home/amisiespoir-07/Dev/singapore", "SmallX"), P("Branch: main | Git remote: not configured", "SmallX"), PageBreak()])


def font(size=28, bold=False):
    path = FONT_BOLD if bold else FONT
    return ImageFont.truetype(path, size) if Path(path).exists() else ImageFont.load_default()


def rounded(draw, box, fill, outline=None, radius=18, width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def text(draw, xy, value, size=26, fill="#17221B", bold=False, max_width=None):
    f = font(size, bold)
    if max_width:
        avg = max(8, int(max_width / max(size * .56, 1)))
        value = "\n".join(wrap(value, avg))
    draw.multiline_text(xy, value, font=f, fill=fill, spacing=6)


def save_ui_images():
    images = {}
    im = PILImage.new("RGB", (1600, 900), "#F8FAF5"); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1600, 180), fill="#5733A5"); text(d, (90, 45), "Harvest Hub", 62, "white", True); text(d, (92, 118), "Phase 2 supply matching for farmers and buyers", 25, "#E7DDFF")
    text(d, (90, 230), "Choose a demo role", 35, bold=True)
    for i, (name, desc, color) in enumerate((("Buyer demo", "Open a request and match nearby supply", "#19764A"), ("Farmer demo", "Review and accept assigned orders", "#5733A5"), ("Admin demo", "Moderate users, listings, and orders", "#B45F06"))):
        x = 90 + i * 500; rounded(d, (x, 310, x + 440, 640), "white", "#DDE7DC"); d.rectangle((x, 310, x + 440, 326), fill=color); text(d, (x + 28, 365), name, 35, color, True); text(d, (x + 28, 440), desc, 24, "#66736A", max_width=380); rounded(d, (x + 28, 555, x + 240, 610), color, radius=12); text(d, (x + 55, 568), "Open interface", 20, "white", True)
    text(d, (90, 760), "Illustrated from the current Next.js interface", 22, "#66736A")
    path = TMP / "roles.png"; im.save(path); images["roles"] = path

    im = PILImage.new("RGB", (1600, 900), "#F8FAF5"); d = ImageDraw.Draw(im); text(d, (70, 35), "Buyer request and grouped match", 42, "#5733A5", True)
    rounded(d, (70, 120, 760, 820), "white", "#DDE7DC"); text(d, (105, 155), "Open buyer request", 30, bold=True)
    fields = [("Product", "Tomatoes"), ("Quantity", "100 kg"), ("Maximum price", "0.80 / kg"), ("Search radius", "50 km"), ("Pickup", "1.3000, 36.8200")]
    for i, (label, value) in enumerate(fields):
        y = 230 + i * 100; text(d, (110, y), label, 18, "#66736A", True); rounded(d, (300, y - 10, 700, y + 48), "#F8FAF5", "#B9C9BA", 10); text(d, (320, y + 2), value, 20)
    rounded(d, (110, 735, 390, 790), "#19764A", radius=10); text(d, (150, 747), "Find nearby supply", 20, "white", True)
    rounded(d, (825, 120, 1530, 820), "white", "#DDE7DC"); text(d, (865, 155), "Complete match", 30, "#19764A", True); text(d, (865, 215), "100 of 100 kg allocated", 22)
    for y, qty, lot, km, price, score in ((300, "60 kg", "lot_demo_tomatoes", "0.90 km", "0.70/kg", "0.352"), (465, "40 kg", "lot_demo_tomatoes_sunrise", "1.39 km", "0.75/kg", "0.395")):
        rounded(d, (860, y, 1490, y + 125), "#F5F8F3", "#DDE7DC", 12); text(d, (885, y + 18), f"{qty} from {lot}", 22, bold=True); text(d, (885, y + 67), f"{km} | {price} | score {score}", 19, "#66736A")
    rounded(d, (865, 690, 1215, 755), "#19764A", radius=12); text(d, (915, 706), "Create grouped order", 21, "white", True)
    path = TMP / "buyer.png"; im.save(path); images["buyer"] = path

    im = PILImage.new("RGB", (1600, 900), "#F8FAF5"); d = ImageDraw.Draw(im); text(d, (70, 35), "Farmer and administrator views", 42, "#5733A5", True)
    rounded(d, (70, 120, 760, 820), "white", "#DDE7DC"); text(d, (105, 155), "Farmer order queue", 30, bold=True)
    for y, oid, qty, status in ((240, "ord_demo_pending", "10 kg tomatoes", "PENDING"), (420, "ord_demo_1", "20 kg tomatoes", "ACCEPTED")):
        rounded(d, (105, y, 720, y + 130), "#F5F8F3", "#DDE7DC", 12); text(d, (130, y + 20), oid, 22, bold=True); text(d, (130, y + 62), qty, 20, "#66736A"); text(d, (530, y + 20), status, 18, "#19764A", True)
    rounded(d, (105, 650, 330, 710), "#19764A", radius=10); text(d, (150, 665), "Accept order", 20, "white", True)
    rounded(d, (825, 120, 1530, 820), "white", "#DDE7DC"); text(d, (865, 155), "Admin moderation", 30, bold=True)
    entries = (("buyer@example.com", "buyer | active"), ("farmer.one@example.com", "farmer | active"), ("Tomatoes - lot_demo_tomatoes", "60 kg | active"))
    for i, (name, state) in enumerate(entries):
        y = 245 + i * 145; d.line((865, y - 15, 1490, y - 15), fill="#DDE7DC", width=2); text(d, (875, y), name, 21, bold=True); text(d, (875, y + 42), state, 18, "#66736A"); rounded(d, (1270, y + 10, 1460, y + 65), "#EDF3EE", "#BFD3C0", 10); text(d, (1315, y + 23), "Change", 18, "#19764A", True)
    path = TMP / "farmer-admin.png"; im.save(path); images["farmer"] = path

    im = PILImage.new("RGB", (1600, 780), "white"); d = ImageDraw.Draw(im); text(d, (70, 30), "Production deployment architecture", 40, "#5733A5", True)
    boxes = [(70, 280, 360, 475, "Git repository", "One monorepo", "#5733A5"), (505, 100, 855, 295, "Vercel frontend", "Next.js - apps/web", "#19764A"), (505, 480, 855, 675, "Vercel backend", "FastAPI - api", "#5733A5"), (1030, 480, 1460, 675, "Managed Postgres", "Neon + PostGIS", "#B45F06")]
    for x1, y1, x2, y2, title, sub, color in boxes:
        rounded(d, (x1, y1, x2, y2), "#F8FAF5", color, 18, 4); text(d, (x1 + 30, y1 + 45), title, 28, color, True); text(d, (x1 + 30, y1 + 100), sub, 22, "#66736A")
    for points in (((360, 350), (505, 195)), ((360, 400), (505, 575)), ((855, 575), (1030, 575)), ((680, 295), (680, 480))):
        d.line(points, fill="#66736A", width=6); x, y = points[1]; d.polygon([(x, y), (x - 18, y - 10), (x - 18, y + 10)], fill="#66736A")
    text(d, (880, 355), "HTTPS API", 20, "#66736A", True); text(d, (1080, 700), "Pooled DATABASE_URL", 18, "#66736A")
    path = TMP / "architecture.png"; im.save(path); images["architecture"] = path
    return images


def img(path, width=174 * mm):
    pic = Image(str(path)); pic.drawWidth = width; pic.drawHeight = width * 9 / 16; return pic


def build_quick(images):
    path = OUT / "farmer-marketplace-quick-start.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm, topMargin=20 * mm, bottomMargin=18 * mm, title="Farmer Marketplace Quick Start")
    story = []
    cover(story, "Farmer Marketplace Quick Start", "A visual guide to the demo data, local startup, and the buyer, farmer, and admin journeys.", "Simplified guide")
    story += [P("1. What is ready", "H1X"), callout("Application", "The FastAPI and Next.js code compiles. The PostGIS migration, Compose configuration, and four database integration tests are present.", "ok"), Spacer(1, 4 * mm), callout("Database today", "Not running on this computer. Start Docker with administrator access, apply the migration, and load the seed before expecting the app to show records.", "warn"), Spacer(1, 6 * mm), img(images["roles"]), Spacer(1, 3 * mm), P("These are illustrated screens based on the current UI and seed values. They are not evidence of a live database connection.", "SmallX"), PageBreak()]
    story += [P("2. Dummy data included", "H1X"), P("Running the seed command resets marketplace tables and inserts the following demo records."), P("Users", "H2X"), data_table(["Email", "Role", "Purpose"], [("buyer@example.com", "Buyer", "Creates requests and orders"), ("farmer.one@example.com", "Farmer", "Green Valley Farm"), ("farmer.two@example.com", "Farmer", "Sunrise Fields"), ("admin@example.com", "Admin", "Moderates users and listings")], [58 * mm, 28 * mm, 86 * mm]), Spacer(1, 5 * mm), P("Farms and available produce", "H2X"), data_table(["Farm", "Location", "Product", "Available after sample orders", "Price/kg"], [("Green Valley", "1.2921, 36.8219", "Tomatoes", "60 kg", "0.70"), ("Sunrise Fields", "1.3102, 36.8127", "Tomatoes", "50 kg", "0.75"), ("Green Valley", "1.2921, 36.8219", "Onions", "150 kg", "0.45"), ("Sunrise Fields", "1.3102, 36.8127", "Cabbage", "60 kg", "0.55")], [37 * mm, 35 * mm, 28 * mm, 48 * mm, 24 * mm]), Spacer(1, 5 * mm), callout("Expected match", "The 100 kg tomato request is filled by 60 kg from Green Valley plus 40 kg from Sunrise Fields. Inventory is rechecked when the grouped order is created.", "info"), PageBreak()]
    story += [P("3. Start the application locally", "H1X"), P("Run these commands from the repository root."), code("sudo docker compose up -d database\n.venv/bin/alembic upgrade head\n.venv/bin/python -m api.scripts.seed_demo --yes-reset"), P("Start the backend in terminal 1:", "H2X"), code(".venv/bin/uvicorn app.main:app --app-dir api --reload"), P("Start the frontend in terminal 2:", "H2X"), code("cd apps/web\nnpm install\nnpm run dev"), P("Open the application:", "H2X"), bullet("Frontend: http://localhost:3000"), bullet("API documentation: http://127.0.0.1:8000/docs"), bullet("Database health: http://127.0.0.1:8000/health"), callout("Healthy result", 'The health endpoint should return: {"status":"ok","database":"connected"}', "ok"), PageBreak()]
    story += [P("4. Buyer journey", "H1X"), img(images["buyer"]), Spacer(1, 4 * mm), P("Steps", "H2X"), bullet("Choose Buyer demo."), bullet("Confirm Tomatoes, 100 kg, maximum 0.80/kg, 50 km radius, and pickup coordinates."), bullet("Select Find nearby supply. Review distance, price, score, and quantities."), bullet("Select Create grouped order. The backend locks inventory, creates linked farmer orders, and marks the request ORDERED."), callout("Do not reuse the request", "A completed request cannot create a second grouped order. The API returns conflict status 409.", "info"), PageBreak()]
    story += [P("5. Farmer and admin journeys", "H1X"), img(images["farmer"]), Spacer(1, 4 * mm), P("Farmer", "H2X"), Spacer(1, 2 * mm), bullet("Choose Farmer demo to see orders assigned to that farmer's lots."), bullet("Accept a PENDING order. Only the owning farmer can accept it."), bullet("Use the map panel to confirm the farm location."), P("Administrator", "H2X"), Spacer(1, 2 * mm), bullet("Choose Admin demo to view all users, listings, and orders."), bullet("Disable or enable buyer/farmer accounts."), bullet("Deactivate or reactivate listings. Admin accounts cannot be disabled here."), PageBreak()]
    story += [P("6. Verify dummy data", "H1X"), code("curl http://127.0.0.1:8000/health\n.venv/bin/pytest api/tests"), P("Optional SQL checks", "H2X"), code("SELECT count(*) FROM users;             -- expected 4\nSELECT count(*) FROM farms;             -- expected 2\nSELECT count(*) FROM lots;              -- expected 4\nSELECT count(*) FROM buyer_requests;    -- expected 1\nSELECT count(*) FROM orders;            -- expected 2 before new UI actions\nSELECT PostGIS_Full_Version();"), P("If it does not work", "H2X"), data_table(["Symptom", "Action"], [("Connection refused on 5432", "Start Docker/PostGIS and wait for its health check."), ("Docker permission denied", "Use sudo or add your user to the Docker group, then sign out and back in."), ("Missing tables", "Run .venv/bin/alembic upgrade head."), ("No products", "Run the controlled seed command once."), ("Browser CORS error", "Confirm the frontend URL is present in CORS_ORIGINS.")], [58 * mm, 114 * mm]), PageBreak()]
    story += [P("7. Safety notes", "H1X"), callout("Seed command deletes data", "The --yes-reset option clears existing marketplace rows. Use it only for a demo or an empty development database.", "bad"), Spacer(1, 5 * mm), bullet("Set ENABLE_DEMO_SEED=0 for online deployments."), bullet("Never commit DATABASE_URL, passwords, or Vercel tokens."), bullet("Use a separate preview database or branch for preview deployments."), bullet("Run migrations before sending production traffic to a new backend version."), bullet("Back up production data before destructive migrations."), Spacer(1, 10 * mm), P("You are ready when the health endpoint reports a connected database, the four integration tests pass, and all three demo roles load without errors.", "H2X")]
    doc.build(story, onFirstPage=page_decor, onLaterPages=page_decor)
    return path


def build_full(images):
    path = OUT / "farmer-marketplace-full-deployment-guide.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm, topMargin=20 * mm, bottomMargin=18 * mm, title="Farmer Marketplace Full Deployment and Implementation Guide")
    story = []
    cover(story, "Full Deployment and Implementation Guide", "PostgreSQL/PostGIS operations, Git workflow, two-project Vercel deployment, migration strategy, security, testing, and the implementation plan.", "Technical documentation")
    story += [P("1. Executive status", "H1X"), data_table(["Area", "Status", "Evidence or action"], [("PostgreSQL connection", "BLOCKED", "No service is listening on local port 5432."), ("Docker service", "BLOCKED", "Daemon access requires an administrator password."), ("Schema", "READY", "Alembic emits valid PostgreSQL/PostGIS DDL."), ("Spatial model", "READY", "Geography points and GiST indexes are defined."), ("Application build", "READY", "Python compilation and Next.js production build pass."), ("Database tests", "READY TO RUN", "Four integration tests are collected; they need a live PostGIS database.")], [46 * mm, 28 * mm, 98 * mm]), Spacer(1, 6 * mm), callout("Truthful interpretation", "The database integration is implemented but not proven against a live database on this host. Do not call the deployment production-ready until migrations, seed, spatial matching, and grouped-order tests pass on a running PostGIS instance.", "warn"), PageBreak()]
    story += [P("2. Target architecture", "H1X"), img(images["architecture"], 174 * mm), Spacer(1, 4 * mm), bullet("One Git repository drives two Vercel projects."), bullet("Frontend project root: apps/web. It builds Next.js and calls NEXT_PUBLIC_API_URL."), bullet("Backend project root: api. Vercel discovers index.py and runs FastAPI as a Python Function."), bullet("The backend connects to managed PostgreSQL with PostGIS through a pooled DATABASE_URL."), bullet("Alembic migrations run as an explicit release step, never during every function startup."), bullet("Production, preview, and development use separate credentials and preferably separate database branches."), PageBreak()]
    story += [P("3. Persistent domain model", "H1X"), data_table(["Table", "Purpose", "Critical constraints"], [("users", "Buyer, farmer, admin identities", "Unique email; role check; active flag"), ("auth_tokens", "Persistent bearer sessions", "Token primary key; delete with user"), ("farmer_profiles", "Public farmer details", "One profile per farmer"), ("farms", "Farm identity and geographic point", "Geography POINT(4326); GiST index"), ("lots", "Available produce inventory", "Quantity >= 0; price > 0; active flag"), ("buyer_requests", "Demand, radius, pickup point", "Quantity/radius > 0; status state machine"), ("match_plans", "Persisted matching decision", "One current plan per request"), ("allocations", "Per-farmer quantity and score", "References request, lot, farmer"), ("orders", "Reserved inventory and fulfilment state", "Quantity > 0; status check; group ID")], [34 * mm, 65 * mm, 73 * mm]), Spacer(1, 6 * mm), P("Geospatial query", "H2X"), code("ST_DWithin(farms.location, buyer_request.location, radius_km * 1000)\nST_Distance(farms.location, buyer_request.location)"), P("PostGIS geography calculations use metres. Coordinates are written as POINT(longitude latitude), not latitude first."), PageBreak()]
    story += [P("4. Dummy dataset and expected behavior", "H1X"), P("The controlled seed command creates four users, two farms, four lots, two sample orders, three tokens, and one buyer request."), data_table(["Object", "Identifier", "Key values"], [("Buyer", "usr_demo_buyer", "buyer@example.com"), ("Farmer 1", "usr_demo_farmer_1", "Green Valley Farm"), ("Farmer 2", "usr_demo_farmer_2", "Sunrise Fields"), ("Admin", "usr_demo_admin", "admin@example.com"), ("Buyer request", "req_demo_tomatoes", "100 kg tomatoes; max 0.80; 50 km"), ("Sample order", "ord_demo_1", "20 kg; ACCEPTED"), ("Pending order", "ord_demo_pending", "10 kg; PENDING")], [40 * mm, 58 * mm, 74 * mm]), Spacer(1, 5 * mm), data_table(["Allocation", "Quantity", "Distance", "Price", "Approx. score"], [("Green Valley tomatoes", "60 kg", "0.90 km", "0.70/kg", "0.352"), ("Sunrise tomatoes", "40 kg", "1.39 km", "0.75/kg", "0.395")], [66 * mm, 26 * mm, 26 * mm, 26 * mm, 28 * mm]), Spacer(1, 5 * mm), callout("Atomic confirmation", "The finalization route locks the buyer request and eligible lots, recalculates the plan, reserves quantities, creates linked orders, and updates the request in one transaction.", "ok"), PageBreak()]
    story += [P("5. Local database operations", "H1X"), P("Initial setup", "H2X"), code("sudo docker compose up -d database\npython -m venv .venv\n.venv/bin/pip install -r api/requirements.txt\n.venv/bin/alembic upgrade head\n.venv/bin/python -m api.scripts.seed_demo --yes-reset"), P("Verification", "H2X"), code(".venv/bin/pytest api/tests\n.venv/bin/uvicorn app.main:app --app-dir api --reload\ncurl http://127.0.0.1:8000/health"), P("Migration rules", "H2X"), bullet("Generate a new migration for every schema change."), bullet("Review generated SQL before applying it."), bullet("Test upgrade from an empty database and from a copy of the previous schema."), bullet("Do not automatically downgrade production after writes have used a new schema."), bullet("Back up before destructive changes and use expand-migrate-contract for incompatible releases."), PageBreak()]
    story += [P("6. Push the repository", "H1X"), P("The repository currently has no Git remote. Create an empty GitHub, GitLab, or Bitbucket repository first."), code("git status\ngit add .\ngit commit -m \"Add PostgreSQL PostGIS persistence and deployment guides\"\ngit remote add origin https://github.com/YOUR_ACCOUNT/farmer-marketplace.git\ngit push -u origin main"), P("Before pushing", "H2X"), bullet("Confirm .env and .venv are ignored."), bullet("Confirm DATABASE_URL and tokens do not appear in git diff or history."), bullet("Run the backend tests against PostGIS and npm run build in apps/web."), bullet("Review the large untracked directories and commit only intended project assets."), callout("Current repository condition", "Most project files are untracked. The first commit should be reviewed carefully because git add . will include every non-ignored file.", "warn"), PageBreak()]
    story += [P("7. Provision managed Postgres with PostGIS", "H1X"), bullet("In Vercel Marketplace, install a managed Postgres integration such as Neon."), bullet("Create a production database and a separate preview/development branch."), bullet("Use the provider's pooled connection string for DATABASE_URL in the backend function."), bullet("Confirm PostGIS is available, then run CREATE EXTENSION IF NOT EXISTS postgis; through Alembic."), bullet("Keep a direct or migration connection available for Alembic if the pooler rejects DDL or transaction settings."), P("Apply the schema", "H2X"), code("DATABASE_URL='postgresql+psycopg://...' .venv/bin/alembic upgrade head\nDATABASE_URL='postgresql+psycopg://...' .venv/bin/python -m api.scripts.seed_demo --yes-reset"), callout("Production warning", "The seed command deletes marketplace rows. Run it only once on a new demo database. Disable the public seed route with ENABLE_DEMO_SEED=0.", "bad"), PageBreak()]
    story += [P("8. Deploy the FastAPI backend to Vercel", "H1X"), bullet("Import the Git repository as a new Vercel project."), bullet("Set Root Directory to api."), bullet("Leave framework detection and build command at their defaults. api/index.py exports the FastAPI app."), bullet("Add environment variables for Production and Preview."), data_table(["Variable", "Production value", "Purpose"], [("DATABASE_URL", "Pooled managed Postgres URL", "Application database"), ("ENABLE_DEMO_SEED", "0", "Disable destructive public seed"), ("CORS_ORIGINS", "https://YOUR-FRONTEND.vercel.app", "Exact browser origin"), ("CORS_ORIGIN_REGEX", "Optional preview-domain regex", "Preview deployments"), ("DB_POOL_SIZE", "2", "Small per-instance pool"), ("DB_MAX_OVERFLOW", "1", "Bound connection growth")], [42 * mm, 64 * mm, 66 * mm]), Spacer(1, 5 * mm), bullet("Deploy and open /health. It must report database connected."), bullet("Open /docs and test product listing with no browser CORS dependency."), bullet("Inspect Vercel Function logs for connection, import, or bundle errors."), PageBreak()]
    story += [P("9. Deploy the Next.js frontend to Vercel", "H1X"), bullet("Import the same Git repository as a second Vercel project."), bullet("Set Root Directory to apps/web."), bullet("Confirm Framework Preset is Next.js."), bullet("Set NEXT_PUBLIC_API_URL to the production backend URL without a trailing slash."), bullet("Deploy, then copy the final frontend URL into the backend CORS_ORIGINS variable."), bullet("Redeploy the backend because Vercel environment-variable changes do not affect older deployments."), P("End-to-end smoke test", "H2X"), data_table(["Step", "Expected result"], [("Open frontend", "Products load without API connection error"), ("Open buyer demo", "Buyer session and request ID appear"), ("Find supply", "Two tomato allocations total 100 kg"), ("Create grouped order", "One group ID and two farmer orders"), ("Open farmer demo", "Assigned order appears and can be accepted"), ("Open admin demo", "Users, listings, and orders are visible")], [54 * mm, 118 * mm]), PageBreak()]
    story += [P("10. Vercel monorepo release flow", "H1X"), P("Vercel supports connecting multiple projects to one repository. Each project uses its own Root Directory and URL."), data_table(["Project", "Root", "Build/runtime", "Primary environment"], [("harvest-hub-web", "apps/web", "Next.js", "NEXT_PUBLIC_API_URL"), ("harvest-hub-api", "api", "Python / FastAPI Function", "DATABASE_URL, CORS, pool limits")], [42 * mm, 34 * mm, 44 * mm, 52 * mm]), P("Safe release order", "H2X"), bullet("1. Create and review a backward-compatible Alembic migration."), bullet("2. Apply the migration to preview database."), bullet("3. Deploy preview backend and frontend; run smoke tests."), bullet("4. Apply the migration to production."), bullet("5. Deploy production backend, then frontend."), bullet("6. Monitor errors, latency, and database connections."), bullet("7. Remove old columns only in a later release after all code stops using them."), PageBreak()]
    story += [P("11. Testing and acceptance gates", "H1X"), data_table(["Gate", "Required check"], [("Schema", "alembic upgrade head succeeds on an empty PostGIS database"), ("Persistence", "Rows remain after backend restart"), ("Spatial", "Radius excludes remote farms and distances are plausible"), ("Concurrency", "Two confirmations cannot oversell one lot"), ("Atomicity", "Failure rolls back request, orders, and all quantities"), ("Authorization", "Buyer, farmer, and admin boundaries return 403 when crossed"), ("Idempotency", "Repeated confirmation cannot create duplicate grouped orders"), ("Frontend", "Buyer, farmer, and admin journeys pass in production"), ("Operations", "Backups, logs, alerts, and rollback procedure are verified")], [45 * mm, 127 * mm]), Spacer(1, 6 * mm), P("Current automated coverage", "H2X"), bullet("Marketplace order state transitions."), bullet("Seed persistence across sessions."), bullet("PostGIS radius matching and multi-farmer allocation."), bullet("Grouped-order creation and duplicate prevention."), callout("Next test priority", "Add HTTP integration tests and a concurrent reservation test using two independent database sessions.", "info"), PageBreak()]
    story += [P("12. Security and operations", "H1X"), bullet("Replace long-lived bearer tokens with expiring sessions or signed access/refresh tokens."), bullet("Rate-limit authentication, demo, and order-confirmation endpoints."), bullet("Store secrets only in Vercel environment variables or the database provider's integration."), bullet("Set ENABLE_DEMO_SEED=0 and remove/reset known demo credentials for a real marketplace."), bullet("Restrict database roles: runtime should not own schema migrations."), bullet("Use TLS database connections and provider connection pooling."), bullet("Record immutable order/status events for disputes and reputation."), bullet("Set backup retention and practice point-in-time recovery."), bullet("Add error monitoring and alerts for failed transactions, connection saturation, and 5xx rates."), bullet("Keep the API and database in nearby regions to reduce latency."), PageBreak()]
    story += [P("13. Implementation plan", "H1X"), data_table(["Milestone", "Deliverable", "Exit condition"], [("A. Database activation", "Start PostGIS, migrate, seed, run tests", "All four integration tests pass"), ("B. Repository boundaries", "Move SQL queries out of routes", "Route -> service -> repository -> DB"), ("C. Reservation model", "AVAILABLE/RESERVED/SOLD/RELEASED", "Cancellation safely releases stock"), ("D. Idempotency and audit", "Request keys and domain events", "Retries cannot duplicate effects"), ("E. Routing", "OSRM/GraphHopper adapter", "Road time shown separately from radius"), ("F. Transport pooling", "Shipments, stops, vehicle capacity", "Compatible orders share a route"), ("G. Fulfilment", "Delivery proof and disputes", "Verified completion updates reputation"), ("H. Payments", "Mock provider, then fiat/Solana adapter", "Settlement reconciles with database"), ("I. Analytics", "Historical events and dashboards", "Reliable dataset supports forecasting")], [38 * mm, 68 * mm, 66 * mm]), Spacer(1, 5 * mm), callout("Most important engineering rule", "Protect the order and inventory lifecycle. Every reservation, cancellation, fulfilment, and payment transition must be authorized, idempotent, auditable, and atomic where one database transaction can cover it.", "ok"), PageBreak()]
    story += [P("14. Rollback and incident checklist", "H1X"), bullet("Stop new confirmations if inventory consistency is uncertain."), bullet("Preserve logs, request IDs, group IDs, and external payment references."), bullet("Compare order quantities with lot reservations inside one read-only report."), bullet("Roll back application code only when the schema remains backward-compatible."), bullet("Use a forward migration to repair schema mistakes; avoid destructive downgrades after new writes."), bullet("Restore from backup only after identifying the exact recovery point and expected data loss window."), bullet("Re-run health, migration version, PostGIS version, matching, and grouped-order checks before reopening traffic."), P("Definition of successful deployment", "H2X"), callout("Ready", "Frontend and backend production URLs are live; /health confirms the database; Alembic is at head; PostGIS responds; seed or real records persist; buyer, farmer, and admin flows pass; secrets are not in Git; monitoring and recovery are configured.", "ok"), PageBreak()]
    story += [P("15. Official references", "H1X"), P("Vercel Python runtime and FastAPI", "H2X"), bullet("https://vercel.com/docs/functions/runtimes/python"), bullet("https://vercel.com/kb/guide/ship-a-fastapi-app-on-vercel"), P("Vercel monorepos and projects", "H2X"), bullet("https://vercel.com/docs/monorepos"), bullet("https://vercel.com/docs/projects"), P("Environment variables and database operations", "H2X"), bullet("https://vercel.com/docs/environment-variables"), bullet("https://vercel.com/docs/postgres"), bullet("https://vercel.com/kb/guide/connection-pooling-with-functions"), P("Managed Postgres and PostGIS", "H2X"), bullet("https://vercel.com/marketplace/neon"), bullet("https://neon.com/blog/ten-most-popular-postgres-extensions"), P("Repository sources", "H2X"), bullet("FARMER_MARKETPLACE_BUILD_GUIDE.md"), bullet("api/migrations/versions/0001_marketplace.py"), bullet("api/app/shared/store.py"), bullet("api/app/matching/engine.py"), bullet("api/app/orders/service.py"), bullet("apps/web/app/page.tsx")]
    doc.build(story, onFirstPage=page_decor, onLaterPages=page_decor)
    return path


if __name__ == "__main__":
    pictures = save_ui_images()
    for result in (build_quick(pictures), build_full(pictures)):
        print(result)
