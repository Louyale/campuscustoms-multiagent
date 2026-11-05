"""Draw the five agent avatars as SVG (assets/agents/*.svg) plus a one-page overview.

- Boss: a suit and a Yale-blue tie
- Inventory: an apron, carrying a box
- Accounting: a cardigan and glasses, with a calculator
- Facilities: Yale gear (a Yale-blue hoodie with a block Y, and a Yale cap)
- Customer Service: Campus Customs gear (a white "CC" shop tee and a headset)

Run: python scripts/make_avatars.py
"""

from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets" / "agents"

YALE_BLUE = "#00356b"
ACCENT = "#286dc0"  # lighter Yale blue (no pink: Lou's Yale blue-and-white rule)
SKIN = "#f1c8a5"
HAIR = "#3b2a20"
CARD = "#eaf1fb"   # near-white Yale-blue tint

TORSO = "M26,120 C26,90 40,76 60,76 C80,76 94,90 94,120 Z"


def frame(inner: str, title: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" role="img" aria-label="{title}">
  <title>{title}</title>
  <circle cx="60" cy="60" r="58" fill="{CARD}" stroke="{YALE_BLUE}" stroke-width="3"/>
  <clipPath id="c"><circle cx="60" cy="60" r="56"/></clipPath>
  <g clip-path="url(#c)">
{inner}
  </g>
</svg>
'''


def head(hair: bool = True, extra: str = "") -> str:
    h = f'<path d="M42,50 C38,24 82,24 78,50 C77,40 72,37 64,38 C58,34 48,37 42,50 Z" fill="{HAIR}"/>' if hair else ""
    return f'''    <rect x="54" y="60" width="12" height="18" fill="{SKIN}"/>
    <circle cx="60" cy="47" r="17" fill="{SKIN}"/>
    {h}
    <circle cx="54" cy="48" r="1.8" fill="#222"/><circle cx="66" cy="48" r="1.8" fill="#222"/>
    <path d="M54,55 Q60,59 66,55" stroke="#8a4b3a" stroke-width="1.8" fill="none" stroke-linecap="round"/>
    {extra}'''


def boss() -> str:
    body = f'''    <path d="{TORSO}" fill="#2b2f3a"/>
    <path d="M50,77 L60,100 L70,77 Z" fill="#ffffff"/>
    <path d="M57,79 L63,79 L61.5,84 L64,100 L60,104 L56,100 L58.5,84 Z" fill="{ACCENT}"/>
    <path d="M50,77 L44,84 L56,104 Z M70,77 L76,84 L64,104 Z" fill="#20232c"/>
    <rect x="72" y="96" width="9" height="3" rx="1" fill="#ffffff" opacity=".85"/>'''
    return frame(body + "\n" + head(), "Boss: in a suit with a Yale-blue tie")


def inventory() -> str:
    body = f'''    <path d="{TORSO}" fill="#6b7280"/>
    <path d="M44,84 L76,84 L80,120 L40,120 Z" fill="#8a5a2b"/>
    <path d="M48,84 L48,78 M72,84 L72,78" stroke="#8a5a2b" stroke-width="3"/>
    <rect x="44" y="94" width="32" height="22" rx="2" fill="#c8955a" stroke="#8a5a2b" stroke-width="1.5"/>
    <path d="M44,101 L76,101 M60,94 L60,101" stroke="#8a5a2b" stroke-width="1.5"/>'''
    return frame(body + "\n" + head(), "Inventory: in an apron, carrying a box")


def accounting() -> str:
    glasses = ('<circle cx="54" cy="48" r="5" fill="none" stroke="#222" stroke-width="1.5"/>'
               '<circle cx="66" cy="48" r="5" fill="none" stroke="#222" stroke-width="1.5"/>'
               '<path d="M59,48 L61,48" stroke="#222" stroke-width="1.5"/>')
    body = f'''    <path d="{TORSO}" fill="#5a6b7d"/>
    <path d="M52,77 L60,92 L68,77 Z" fill="#e5e7eb"/>
    <path d="M60,92 L60,120" stroke="#46566a" stroke-width="2"/>
    <rect x="66" y="92" width="20" height="26" rx="3" fill="#1f2937" stroke="#e5e7eb" stroke-width="1"/>
    <rect x="69" y="95" width="14" height="6" rx="1" fill="#a7f3d0"/>
    <g fill="#e5e7eb"><rect x="69" y="104" width="4" height="4"/><rect x="75" y="104" width="4" height="4"/><rect x="69" y="110" width="4" height="4"/><rect x="75" y="110" width="4" height="4"/></g>
    <rect x="81" y="104" width="2" height="10" fill="{ACCENT}"/>'''
    return frame(body + "\n" + head(extra=glasses), "Accounting: in a cardigan and glasses, with a calculator")


def facilities() -> str:
    cap = (f'<path d="M42,42 C42,26 78,26 78,42 Z" fill="{YALE_BLUE}"/>'
           f'<path d="M40,42 L86,42 C86,46 80,47 74,46 L40,46 Z" fill="{YALE_BLUE}"/>'
           '<text x="60" y="40" font-family="Georgia, serif" font-size="11" font-weight="700" fill="#ffffff" text-anchor="middle">Y</text>')
    body = f'''    <path d="{TORSO}" fill="{YALE_BLUE}"/>
    <path d="M44,80 C48,90 72,90 76,80" stroke="#00264d" stroke-width="3" fill="none"/>
    <path d="M56,86 L55,98 M64,86 L65,98" stroke="#ffffff" stroke-width="1.5"/>
    <polygon points="50,100 55,100 60,107 65,100 70,100 62,111 62,118 58,118 58,111" fill="#ffffff"/>'''
    return frame(body + "\n" + head(hair=False, extra=cap), "Facilities: in Yale gear, a Yale-blue hoodie and cap")


def customer_service() -> str:
    headset = (f'<path d="M42,47 C42,26 78,26 78,47" stroke="#222" stroke-width="3" fill="none"/>'
               f'<rect x="38" y="43" width="7" height="11" rx="3" fill="#222"/><rect x="75" y="43" width="7" height="11" rx="3" fill="#222"/>'
               f'<path d="M41,54 C41,62 48,63 52,61" stroke="#222" stroke-width="2" fill="none"/><circle cx="53" cy="61" r="2" fill="{ACCENT}"/>')
    body = f'''    <path d="{TORSO}" fill="#f8fafc"/>
    <path d="M50,77 Q60,84 70,77" stroke="#cbd5e1" stroke-width="2" fill="none"/>
    <text x="60" y="108" font-family="Arial, Helvetica, sans-serif" font-size="17" font-weight="800" fill="{YALE_BLUE}" text-anchor="middle">CC</text>
    <path d="M48,112 L72,112" stroke="{ACCENT}" stroke-width="2"/>'''
    return frame(body + "\n" + head(extra=headset), "Customer Service: in Campus Customs gear, a CC shop tee and headset")


AVATARS = {
    "boss": ("Boss", boss),
    "inventory": ("Inventory", inventory),
    "accounting": ("Accounting", accounting),
    "facilities": ("Facilities", facilities),
    "customer_service": ("Customer Service", customer_service),
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tiles = []
    for i, (key, (label, draw)) in enumerate(AVATARS.items()):
        svg = draw()
        (OUT / f"{key}.svg").write_text(svg, encoding="utf-8")
        inner = svg.split("\n", 1)[1].rsplit("</svg>", 1)[0].replace('id="c"', f'id="c{i}"').replace("url(#c)", f"url(#c{i})")
        x = 20 + i * 150
        tiles.append(f'<g transform="translate({x},20)"><svg width="120" height="120" viewBox="0 0 120 120">{inner}</svg>'
                     f'<text x="60" y="146" font-family="Arial, Helvetica, sans-serif" font-size="13" font-weight="600" fill="#00356b" text-anchor="middle">{label}</text></g>')
    sheet = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 770 170" width="770" height="170">'
             '<rect width="770" height="170" fill="#ffffff"/>' + "".join(tiles) + "</svg>\n")
    (OUT / "all_agents.svg").write_text(sheet, encoding="utf-8")
    print("wrote", ", ".join(f"{k}.svg" for k in AVATARS), "and all_agents.svg")


if __name__ == "__main__":
    main()
