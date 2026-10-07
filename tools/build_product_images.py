"""Generate flat SVG illustrations of produce into apps/web/public/products/ (run from anywhere)."""
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "apps/web/public/products"
LEAF = "#2f8f4e"

def svg(bg, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400"><rect width="400" height="400" fill="{bg}"/>'
            f'<ellipse cx="200" cy="350" rx="120" ry="18" fill="#00000014"/>{body}</svg>')

def round_(c, dark, n=1):
    xs = [200] if n == 1 else [140, 260]
    b = "".join(f'<circle cx="{x}" cy="{250 if n == 1 else 270}" r="{95 if n == 1 else 70}" fill="{c}"/>'
                f'<path d="M{x-35} {(250 if n == 1 else 270)-(95 if n == 1 else 70)+8}q35 25 70 0q-20 -25 -35 -10q-15 -15 -35 10z" fill="{LEAF}"/>'
                f'<ellipse cx="{x-35}" cy="{(250 if n == 1 else 270)-25}" rx="14" ry="26" fill="#ffffff55"/>' for x in xs)
    return b

def onion(c):
    return (f'<path d="M200 80q10 40 8 55q80 30 80 110q0 80-88 80t-88-80q0-80 80-110q-2-15 8-55z" fill="{c}"/>'
            f'<path d="M200 135q-45 40-45 110t45 80M200 135q45 40 45 110t-45 80" stroke="#ffffff66" stroke-width="6" fill="none"/>'
            f'<path d="M200 80q-6-30 6-48" stroke="{LEAF}" stroke-width="8" fill="none"/>')

def cabbage(c):
    return (f'<circle cx="200" cy="230" r="115" fill="{c}"/><circle cx="200" cy="230" r="85" fill="#ffffff2e"/>'
            f'<path d="M200 115q-20 70 0 230M120 160q50 60 30 160M280 160q-50 60-30 160" stroke="#ffffff88" stroke-width="6" fill="none"/>')

def carrot(c):
    return (f'<path d="M130 150q70-40 140 0l-60 190q-10 20-20 0z" fill="{c}" transform="rotate(-18 200 240)"/>'
            f'<path d="M200 140q-40-60-70-70M200 140q0-70 10-90M200 140q40-60 70-70" stroke="{LEAF}" stroke-width="12" stroke-linecap="round" fill="none"/>')

def banana(c):
    return (f'<path d="M90 130q20 190 220 190q-10 -40-70-50q-80-20-100-150z" fill="{c}"/>'
            f'<path d="M90 130l-8-30" stroke="#7a5b17" stroke-width="12" stroke-linecap="round"/>')

def maize(c):
    kernels = "".join(f'<circle cx="{x}" cy="{y}" r="9" fill="#ffd54a"/>' for x in range(170, 240, 22) for y in range(130, 320, 24))
    return (f'<ellipse cx="200" cy="225" rx="52" ry="110" fill="{c}"/>{kernels}'
            f'<path d="M200 345q-120-40-110-200q70 60 110 200zM200 345q120-40 110-200q-70 60-110 200z" fill="{LEAF}"/>')

def leafy(c):
    return "".join(f'<path d="M200 340q-{w} -120 0 -250q{w} 130 0 250z" fill="{c}" transform="rotate({r} 200 340)"/>' for w, r in [(70, -40), (70, 40), (60, 0)])

PRODUCTS = {
    "tomatoes": ("#fdebe6", round_("#e5392b", 0)), "apples": ("#fdf0e6", round_("#d63c3c", 0)),
    "oranges": ("#fff3e0", round_("#f59a1b", 0)), "mangoes": ("#fff6dc", round_("#f2b01e", 0)),
    "peppers": ("#e8f5e9", round_("#3da33d", 0)), "potatoes": ("#f5eee4", round_("#c49a62", 0, 2)),
    "onions": ("#f6ecf5", onion("#b4569e")), "cabbage": ("#e9f4e9", cabbage("#7cc47c")),
    "carrots": ("#fff0e3", carrot("#f08a24")), "bananas": ("#fffbe0", banana("#f7d23e")),
    "maize": ("#fff8e1", maize("#fbe38e")), "lettuce": ("#eef8e6", leafy("#69b84f")),
    "spinach": ("#e6f3e8", leafy("#2f8f4e")),
}
DEFAULT = ("#e9f4e9", leafy("#4aa86a"))

OUT.mkdir(parents=True, exist_ok=True)
for name, (bg, body) in {**PRODUCTS, "default": DEFAULT}.items():
    (OUT / f"{name}.svg").write_text(svg(bg, body))
print(len(PRODUCTS) + 1, "images ->", OUT)
