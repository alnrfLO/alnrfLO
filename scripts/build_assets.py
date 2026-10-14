"""Génère les SVG du profil : cartes projets, badges de compétences et bandeau alternance.

Usage : python scripts/build_assets.py
Modifie PROJECTS / SKILLS / CTA ci-dessous puis relance le script.
"""
from pathlib import Path
import re
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
FONT = "Segoe UI, Helvetica, Arial, sans-serif"
MONO = "Fira Code, Consolas, monospace"

# Palette (identité bleu nuit / cyan)
BG1, BG2 = "#0b0f19", "#101a2c"
BORDER = "#1f2d40"
CYAN = "#61DAFB"
ICE = "#c8f2ff"
TEXT = "#e6edf3"
MUTED = "#9aa7b4"

# --------------------------------------------------------------------------
# Mesure du texte (Pillow si dispo, sinon estimation)
# --------------------------------------------------------------------------
try:
    from PIL import ImageFont

    _FONTS = {}

    def text_w(s, size, bold=False):
        key = (size, bold)
        if key not in _FONTS:
            name = "Inter-SemiBold.otf" if bold else "Inter-Regular.otf"
            _FONTS[key] = ImageFont.truetype(f"/usr/share/fonts/opentype/inter/{name}", size)
        return _FONTS[key].getlength(s)
except Exception:  # pragma: no cover
    def text_w(s, size, bold=False):
        return len(s) * size * (0.58 if bold else 0.54)


def wrap(text, size, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = f"{cur} {w}".strip()
        if text_w(test, size) <= max_w:
            cur = test
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def icon_inner(name, prefix):
    """Contenu d'une icône 56x56, avec des id préfixés pour éviter les collisions."""
    svg = (ASSETS / f"icon-{name}.svg").read_text(encoding="utf-8")
    inner = re.search(r"<svg[^>]*>(.*)</svg>", svg, re.S).group(1)
    ids = re.findall(r'id="([^"]+)"', inner)
    for i in ids:
        inner = inner.replace(f'id="{i}"', f'id="{prefix}{i}"').replace(f"url(#{i})", f"url(#{prefix}{i})")
    return inner


# --------------------------------------------------------------------------
# Cartes projets
# --------------------------------------------------------------------------
PROJECTS = [
    {
        "slug": "mathdle", "icon": "mathdle", "title": "Mathdle",
        "sub": "mathdlee.vercel.app", "pill": "LIVE",
        "desc": "Jeu de déduction façon Wordle / Nerdle autour des maths et des sciences : énigme du jour, "
                "mode série, système de vies, équations chimiques vérifiées par comptage d'atomes.",
        "tags": ["React", "TypeScript", "Vite", "Vercel"],
    },
    {
        "slug": "portfolio", "icon": "portfolio", "title": "Portfolio",
        "sub": "rafatns.vercel.app", "pill": "LIVE",
        "desc": "Refait de zéro : identité bleu nuit / cyan, rose bleue SVG animée, 4 langues "
                "(FR · EN · PT · ES), thème clair / sombre, carrousels de projets filtrables.",
        "tags": ["React", "Tailwind", "Framer Motion", "Vite"],
    },
    {
        "slug": "poker", "icon": "poker", "title": "Poker Texas Hold'em",
        "sub": "poker-murex-seven.vercel.app", "pill": "LIVE",
        "desc": "Multijoueur en temps réel : salles avec ID partageable, toutes les phases de jeu, "
                "évaluation automatique des mains et chat intégré.",
        "tags": ["React", "Firebase", "Tailwind"],
    },
    {
        "slug": "chaos", "icon": "chaos", "title": "chaos_mode",
        "sub": "mod Minecraft 1.21 · Fabric", "pill": "EN COURS",
        "desc": "Mon premier projet en Java : outils et blocs custom, onglet créatif dédié, "
                "dimension custom avec portail de téléportation aller-retour.",
        "tags": ["Java 21", "Fabric", "IntelliJ IDEA"],
    },
    {
        "slug": "yofukashi", "icon": "yofukashi", "title": "Yofukashi no Uta",
        "sub": "wiki non officiel · Call of the Night", "pill": "PERSO",
        "desc": "Fait pour apprendre TypeScript en conditions réelles : fiches personnages, "
                "ciel étoilé animé en Canvas, navigation multi-pages avec React Router.",
        "tags": ["React", "TypeScript", "Canvas API"],
    },
    {
        "slug": "sae303", "icon": "sae303", "title": "SAÉ 303 · Baromètre climat",
        "sub": "dataviz · open data data.gouv.fr", "pill": "SAÉ",
        "desc": "Carte interactive des départements français : clic ou recherche, puis "
                "graphiques D3.js générés à la volée depuis un CSV open data de 5,7 Mo.",
        "tags": ["D3.js", "JavaScript", "SVG"],
    },
]

PILL = {
    "LIVE": ("#39D1FF", "#0b2a43"),
    "EN COURS": ("#ff8a5c", "#2a1710"),
    "PERSO": (ICE, "#132235"),
    "SAÉ": (ICE, "#132235"),
}


def card(p):
    W, H = 450, 196
    pre = p["slug"] + "_"
    out = [f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">',
           "<defs>",
           f'<linearGradient id="{pre}bg" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="{BG1}"/><stop offset="100%" stop-color="{BG2}"/></linearGradient>',
           f'<linearGradient id="{pre}top" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stop-color="{CYAN}" stop-opacity="0"/><stop offset="50%" stop-color="{CYAN}" stop-opacity="0.8"/><stop offset="100%" stop-color="{CYAN}" stop-opacity="0"/></linearGradient>',
           "</defs>",
           f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="16" fill="url(#{pre}bg)" stroke="{BORDER}"/>',
           f'<line x1="40" y1="1.5" x2="{W-40}" y2="1.5" stroke="url(#{pre}top)" stroke-width="1.5"/>']
    # icône
    out.append(f'<svg x="20" y="20" width="46" height="46" viewBox="0 0 56 56">{icon_inner(p["icon"], pre)}</svg>')
    # titre + sous-titre
    out.append(f'<text x="80" y="40" fill="{TEXT}" font-family="{FONT}" font-size="18" font-weight="700">{escape(p["title"])}</text>')
    out.append(f'<text x="80" y="60" fill="{CYAN}" font-family="{MONO}" font-size="11.5" opacity="0.9">{escape(p["sub"])}</text>')
    # pastille
    fg, bg = PILL[p["pill"]]
    pw = text_w(p["pill"], 10, True) + (30 if p["pill"] == "LIVE" else 20)
    px = W - 20 - pw
    out.append(f'<rect x="{px:.1f}" y="22" width="{pw:.1f}" height="20" rx="10" fill="{bg}" stroke="{fg}" stroke-opacity="0.5"/>')
    tx = px + 10
    if p["pill"] == "LIVE":
        out.append(f'<circle cx="{px+11:.1f}" cy="32" r="3" fill="{fg}"><animate attributeName="opacity" values="1;0.25;1" dur="1.8s" repeatCount="indefinite"/></circle>')
        tx = px + 19
    out.append(f'<text x="{tx:.1f}" y="35.5" fill="{fg}" font-family="{FONT}" font-size="10" font-weight="700" letter-spacing="0.8">{escape(p["pill"])}</text>')
    # description
    lines = wrap(p["desc"], 13, W - 44 - 8)
    assert len(lines) <= 3, (p["slug"], lines)
    for i, ln in enumerate(lines):
        out.append(f'<text x="22" y="{96 + i*19}" fill="{MUTED}" font-family="{FONT}" font-size="13">{escape(ln)}</text>')
    # tags
    x = 22
    for t in p["tags"]:
        w = text_w(t, 11, True) + 18
        out.append(f'<rect x="{x:.1f}" y="157" width="{w:.1f}" height="22" rx="6" fill="#0f1c2e" stroke="{BORDER}"/>')
        out.append(f'<text x="{x + w/2:.1f}" y="172" fill="{ICE}" font-family="{FONT}" font-size="11" font-weight="600" text-anchor="middle">{escape(t)}</text>')
        x += w + 8
    out.append("</svg>")
    return "\n".join(out)


# --------------------------------------------------------------------------
# Badges de compétences
# --------------------------------------------------------------------------
SKILLS = [
    ("Langages", [("JS", "JavaScript"), ("TS", "TypeScript"), ("PY", "Python"), ("JV", "Java"),
                  ("PHP", "PHP"), ("LU", "Luau"), ("C", "C"), ("C++", "C++"), ("C#", "C#")]),
    ("Frontend", [("</>", "HTML5"), ("{ }", "CSS3"), ("⚛", "React"), ("NG", "Angular"),
                  ("TW", "Tailwind CSS"), ("D3", "D3.js"), ("⚡", "Vite")]),
    ("Backend", [("ND", "Node.js"), ("NJ", "NestJS"), ("Z", "Zod"), ("FL", "Flask")]),
    ("Données & outils", [("SQL", "MySQL"), ("FB", "Firebase"), ("GIT", "Git"),
                          ("GHA", "GitHub Actions"), ("▲", "Vercel")]),
]


def skills_svg():
    W = 900
    out, y = [], 0
    chip_h, gap = 40, 8
    for cat, items in SKILLS:
        y += 30
        out.append(f'<text x="16" y="{y}" fill="{TEXT}" font-family="{FONT}" font-size="14" font-weight="700" letter-spacing="0.5">{escape(cat)}</text>')
        out.append(f'<line x1="{24 + text_w(cat, 14, True):.0f}" y1="{y-5}" x2="{W-16}" y2="{y-5}" stroke="{BORDER}"/>')
        y += 14
        x = 16
        for short, label in items:
            w = 42 + text_w(label, 13, True) + 10
            if x + w > W - 16:
                x, y = 16, y + chip_h + gap
            fs = 13 if len(short) <= 2 else 10.5
            out.append(f'<g transform="translate({x:.1f},{y})">'
                       f'<rect width="{w:.1f}" height="{chip_h}" rx="10" fill="{BG1}" stroke="{BORDER}"/>'
                       f'<rect x="5" y="5" width="30" height="30" rx="7" fill="url(#chipGrad)"/>'
                       f'<text x="20" y="{24.5 if fs == 13 else 23.5}" fill="#ffffff" font-family="{FONT}" font-size="{fs}" font-weight="800" text-anchor="middle">{escape(short)}</text>'
                       f'<text x="44" y="25" fill="#c9d1d9" font-family="{FONT}" font-size="13" font-weight="600">{escape(label)}</text>'
                       f'</g>')
            x += w + gap
        y += chip_h + 4
    H = y + 8
    head = [f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">',
            '<defs><linearGradient id="chipGrad" x1="0%" y1="100%" x2="100%" y2="0%">'
            '<stop offset="0%" stop-color="#0b2a43"/><stop offset="100%" stop-color="#1c4b73"/></linearGradient></defs>']
    return "\n".join(head + out + ["</svg>"])


# --------------------------------------------------------------------------
# Bandeau "recherche alternance"
# --------------------------------------------------------------------------
CTA_TITLE = "Recherche alternance d'un an · Développeur Full-Stack"
CTA_SUB = "DISPONIBLE DÈS MAINTENANT · RYTHME 1 SEMAINE ÉCOLE / 1 SEMAINE ENTREPRISE"


def cta_svg():
    return f'''<svg width="700" height="110" viewBox="0 0 700 110" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="{BG1}"/><stop offset="100%" stop-color="{BG2}"/></linearGradient>
    <filter id="softGlow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="6" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>
  <rect x="10" y="10" width="680" height="90" rx="18" fill="none" stroke="{CYAN}" stroke-width="2" opacity="0.35" filter="url(#softGlow)">
    <animate attributeName="opacity" values="0.15;0.55;0.15" dur="2.6s" repeatCount="indefinite"/>
  </rect>
  <rect x="4" y="4" width="692" height="102" rx="16" fill="url(#bg)" stroke="{BORDER}" stroke-width="1"/>
  <circle cx="40" cy="55" r="5" fill="#39D1FF"/>
  <circle cx="40" cy="55" r="5" fill="none" stroke="#39D1FF" stroke-width="1.5">
    <animate attributeName="r" values="5;16;5" dur="2.2s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0.8;0;0.8" dur="2.2s" repeatCount="indefinite"/>
  </circle>
  <text x="66" y="47" fill="{TEXT}" font-family="{FONT}" font-size="19" font-weight="700">{escape(CTA_TITLE)}</text>
  <text x="66" y="73" fill="{CYAN}" font-family="{FONT}" font-size="12.5" font-weight="600" letter-spacing="0.6">{escape(CTA_SUB)}</text>
</svg>
'''


if __name__ == "__main__":
    (ASSETS / "cards").mkdir(exist_ok=True)
    for p in PROJECTS:
        (ASSETS / "cards" / f"{p['slug']}.svg").write_text(card(p) + "\n", encoding="utf-8")
    (ASSETS / "skills.svg").write_text(skills_svg() + "\n", encoding="utf-8")
    (ASSETS / "cta.svg").write_text(cta_svg(), encoding="utf-8")
    print("ok :", len(PROJECTS), "cartes, skills.svg, cta.svg")
