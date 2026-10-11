"""Decorations for each journey: passport stamp, line motif, ambient animation.

Everything is inline SVG drawn here (no external images), so it stays sharp
and light. Motifs use a 48×48 grid, drawn with round strokes.
"""
import html

MOTIFS = {
    # Korea: tiled roof of a hanok
    "hanok": "M4 22 Q24 6 44 22 M6 21 Q4 25 1 25 M42 21 Q44 25 47 25 M12 23 V40 M36 23 V40 M8 40 H40 M20 40 V30 H28 V40 M12 28 H36",
    # Japan: torii gate
    "torii": "M5 12 Q24 7 43 12 M8 18 H40 M14 12 V43 M34 12 V43 M24 12 V18 M10 43 H18 M30 43 H38",
    # Snowy peaks
    "mountains": "M2 40 L16 18 L24 28 L32 14 L46 40 Z M12 24 L16 18 L19 23 L21 21 M28 20 L32 14 L35 19 L37 18",
    # Pine tree
    "pine": "M24 5 L14 21 H20 L11 33 H37 L28 21 H34 Z M24 33 V43 M18 43 H30",
    # Maple leaf
    "maple": "M24 4 L27 14 L33 10 L32 18 L40 16 L36 24 L42 28 L32 30 L34 36 L26 32 L24 44 L22 32 L14 36 L16 30 L6 28 L12 24 L8 16 L16 18 L15 10 L21 14 Z",
    # Silver fern frond (koru)
    "koru": "M24 44 V28 C24 16 38 15 38 24 C38 31 29 31 29 25.5 C29 22 33.5 22 33.5 25 M24 36 L17 31 M24 31 L18 26 M24 40 L18 37",
    # Saguaro cactus in the desert
    "cactus": "M20 43 V13 a4 4 0 0 1 8 0 V43 M20 29 H15 a3 3 0 0 1 -3 -3 V19 M28 25 H33 a3 3 0 0 0 3 -3 V15 M6 43 H42",
    # Sun over the outback road
    "sun": "M4 32 H44 M14 32 a10 10 0 0 1 20 0 M24 15 V10 M13 20 L10 17 M35 20 L38 17 M8 27 H4 M40 27 H44 M21 44 L23 32 M27 44 L25 32",
    # Rice terraces
    "terraces": "M4 14 Q14 10 24 14 T44 14 M4 22 Q14 18 24 22 T44 22 M4 30 Q14 26 24 30 T44 30 M4 38 Q14 34 24 38 T44 38",
    # Tuscan cypress on hills
    "cypress": "M18 4 C24 13 24 30 18 40 C12 30 12 13 18 4 Z M32 16 C36 22 36 33 32 40 C28 33 28 22 32 16 Z M2 42 Q14 36 24 42 T46 41",
    # Lavender stems
    "lavender": "M16 44 V22 M24 44 V14 M32 44 V22 M16 22 L13 18 M16 22 L19 18 M16 28 L13 24 M16 28 L19 24 M24 14 L21 10 M24 14 L27 10 M24 20 L21 16 M24 20 L27 16 M24 26 L21 22 M24 26 L27 22 M32 22 L29 18 M32 22 L35 18 M32 28 L29 24 M32 28 L35 24 M10 44 H38",
    # Canal bridge
    "canal": "M3 28 H45 M9 28 a15 12 0 0 1 30 0 M3 36 q5 -4 10 0 t10 0 t10 0 t10 0 M3 43 q5 -4 10 0 t10 0 t10 0 t10 0",
    # Coffee cup
    "coffee": "M9 21 H33 V29 a10 10 0 0 1 -10 10 H19 a10 10 0 0 1 -10 -10 Z M33 23 h4 a4 4 0 0 1 0 8 h-4 M17 8 q-3 4 0 8 M25 8 q-3 4 0 8 M6 44 H36",
    # Compass rose
    "compass": "M24 4 a20 20 0 1 0 0.01 0 M24 10 L28 24 L24 38 L20 24 Z M10 24 H14 M34 24 H38",
}

MODE_ICONS = {
    "velo": "M10 34 a7 7 0 1 0 0.01 0 M38 34 a7 7 0 1 0 0.01 0 M10 34 L18 20 H30 L38 34 M18 20 L15 14 H11 M30 20 L26 34 H17 M27 14 H33",
    "train": "M12 8 H36 a4 4 0 0 1 4 4 V32 a4 4 0 0 1 -4 4 H12 a4 4 0 0 1 -4 -4 V12 a4 4 0 0 1 4 -4 Z M8 22 H40 M16 29 h0.01 M32 29 h0.01 M14 36 L10 42 M34 36 L38 42",
    "roadtrip": "M4 30 V20 a3 3 0 0 1 3 -3 H30 L38 23 H42 a2 2 0 0 1 2 2 V30 Z M8 17 L11 11 H27 L30 17 M13 34 a4 4 0 1 0 0.01 0 M35 34 a4 4 0 1 0 0.01 0",
    "expat": "M4 26 L44 14 L40 22 L18 28 L22 38 L17 38 L12 30 L6 32 Z",
}

# slug -> motif, ambient particles, stamp text
DECOR = {
    "coree-a-velo": ("hanok", "petals", {"fr": "CORÉE DU SUD", "en": "SOUTH KOREA"}),
    "kyushu-a-velo": ("torii", "petals", {"fr": "JAPON · KYUSHU", "en": "JAPAN · KYUSHU"}),
    "retour-en-europe-a-velo": ("cypress", "butterflies", {"fr": "SLOVÉNIE · ITALIE", "en": "SLOVENIA · ITALY"}),
    "suisse-en-train": ("mountains", "snow", {"fr": "SUISSE", "en": "SWITZERLAND"}),
    "belle-via-et-vercors": ("mountains", "leaves", {"fr": "ISÈRE · VERCORS", "en": "ISÈRE · VERCORS"}),
    "gorges-du-tarn-a-velo": ("mountains", "butterflies", {"fr": "TARN · LOZÈRE", "en": "TARN · LOZÈRE"}),
    "passa-pais": ("pine", "leaves", {"fr": "HAUT-LANGUEDOC", "en": "HAUT-LANGUEDOC"}),
    "toulouse-bordeaux-a-velo": ("canal", "butterflies", {"fr": "CANAL DE GARONNE", "en": "GARONNE CANAL"}),
    "echappees-a-velo-en-france": ("lavender", "butterflies", {"fr": "FRANCE", "en": "FRANCE"}),
    "australie": ("sun", "heat", {"fr": "AUSTRALIE", "en": "AUSTRALIA"}),
    "bali": ("terraces", "frangipani", {"fr": "BALI · INDONÉSIE", "en": "BALI · INDONESIA"}),
    "nouvelle-zelande": ("koru", "snow", {"fr": "NOUVELLE-ZÉLANDE", "en": "NEW ZEALAND"}),
    "ouest-americain": ("cactus", "heat", {"fr": "ÉTATS-UNIS", "en": "UNITED STATES"}),
    "japon-2018": ("torii", "petals", {"fr": "JAPON", "en": "JAPAN"}),
    "quebec": ("maple", "maple", {"fr": "QUÉBEC", "en": "QUÉBEC"}),
    "canada-2020": ("pine", "leaves", {"fr": "CANADA", "en": "CANADA"}),
    "colombie": ("coffee", "butterflies", {"fr": "COLOMBIE", "en": "COLOMBIA"}),
    "escapades": ("compass", None, {"fr": "ESCAPADES", "en": "SHORT TRIPS"}),
}

PARTICLES = {
    # shape path (in a 20×20 box), fill colours
    "petals": ("M10 2 C15 6 15 13 10 18 C5 13 5 6 10 2 Z", ["#F2B8C6", "#EBA0B4", "#F7D3DC"]),
    "maple": ("M10 1 L11.5 6 L14.5 4 L14 8 L18 7 L16 11 L19 13 L14 14 L15 17 L11 15 L10 20 L9 15 L5 17 L6 14 L1 13 L4 11 L2 7 L6 8 L5.5 4 L8.5 6 Z", ["#C8452B", "#D9772E", "#B5332A"]),
    "leaves": ("M3 17 C3 8 9 3 17 3 C17 11 12 17 3 17 Z M3 17 L12 8", ["#C9772E", "#B5893A", "#9B5B2A"]),
    "frangipani": ("M10 10 C6 2 12 1 10 10 C18 6 19 12 10 10 C14 18 8 19 10 10 C2 14 1 8 10 10 Z", ["#FFF6E0", "#FBE7B5"]),
    "snow": ("M10 4 a6 6 0 1 0 0.01 0", ["#FFFFFF", "#F2F5F7"]),
    "butterflies": ("M10 10 C6 3 1 5 3 10 C1 15 6 17 10 10 C14 17 19 15 17 10 C19 5 14 3 10 10 Z", ["#F2C14E", "#E8A33D", "#FFFDF8"]),
    "heat": None,
}

esc = lambda s: html.escape(s or "", quote=True)


def motif_svg(name, size=40, color="currentColor", width=2.2, cls=""):
    d = MOTIFS.get(name) or MODE_ICONS.get(name) or ""
    return (f'<svg class="{cls}" width="{size}" height="{size}" viewBox="0 0 48 48" fill="none" stroke="{color}" '
            f'stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="{d}"/></svg>')


def stamp_svg(trip, lang, size=132, cls="stamp-svg"):
    """A round passport-style stamp with the place name and the year."""
    motif, _, label = DECOR.get(trip["slug"], ("compass", None, {"fr": "", "en": ""}))
    color = trip.get("color", "#A8641F")
    year = str(trip["end"].year) if trip.get("end") else ""
    text = f"{label[lang]} · {year} · " if year else f"{label[lang]} · "
    text = text * max(1, round(44 / len(text)))
    uid = f"s-{trip['slug']}-{size}"
    return f"""<svg class="{cls}" width="{size}" height="{size}" viewBox="0 0 132 132" aria-hidden="true">
<defs><path id="{uid}" d="M66 66 m-49 0 a49 49 0 1 1 98 0 a49 49 0 1 1 -98 0"/></defs>
<g fill="none" stroke="{color}" stroke-width="2.6"><circle cx="66" cy="66" r="62"/><circle cx="66" cy="66" r="38" stroke-width="1.6" stroke-dasharray="2 3"/></g>
<text font-family="Karla, sans-serif" font-size="11.5" font-weight="700" letter-spacing="2.2" fill="{color}"><textPath href="#{uid}" textLength="300">{esc(text)}</textPath></text>
<g transform="translate(46 46) scale(0.833)" fill="none" stroke="{color}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="{MOTIFS[motif]}"/></g>
</svg>"""


def hero_decor(trip, lang):
    """Stamp, a traveller crossing the bottom of the hero, and ambient particles."""
    motif, particles, _ = DECOR.get(trip["slug"], ("compass", None, {}))
    mode = trip.get("mode", "velo")
    codes = TRIP_FLAGS.get(trip["slug"], [])
    out = ""
    if codes:
        n = 14
        items = "".join(
            f'<li style="--i:{i};--y:{round(18 * (1 - ((i - (n - 1) / 2) / ((n - 1) / 2)) ** 2))}px">'
            f'<img src="{FLAG_CDN}{codes[i % len(codes)]}.svg" alt=""></li>' for i in range(n))
        out += f'<ul class="bunting" aria-hidden="true">{items}</ul>'
    out += f'<div class="hero-stamp">{stamp_svg(trip, lang, 150)}</div>'
    out += (f'<div class="hero-route" aria-hidden="true"><span class="traveller">'
            f'{motif_svg(mode, 34, "#FFFDF8", 2.4)}</span></div>')
    if particles == "heat":
        out += '<div class="hero-heat" aria-hidden="true"></div>'
    elif particles and PARTICLES.get(particles):
        path, colors = PARTICLES[particles]
        out += (f'<div class="hero-particles" aria-hidden="true" data-kind="{particles}" '
                f'data-path="{esc(path)}" data-colors="{esc(",".join(colors))}"></div>')
    return out


def post_decor(trip, lang):
    """Ambient particles over the story's cover photo, and the reading-progress traveller."""
    motif, particles, _ = DECOR.get(trip["slug"], ("compass", None, {})) if trip else ("compass", None, {})
    mode = trip.get("mode", "velo") if trip else "velo"
    cover = ""
    if particles == "heat":
        cover = '<div class="hero-heat" aria-hidden="true"></div>'
    elif particles and PARTICLES.get(particles):
        path, colors = PARTICLES[particles]
        cover = (f'<div class="hero-particles" aria-hidden="true" data-kind="{particles}" '
                 f'data-path="{esc(path)}" data-colors="{esc(",".join(colors))}"></div>')
    color = trip.get("color", "#A8641F") if trip else "#A8641F"
    progress = (f'<div class="read-route" aria-hidden="true" style="--trip:{color}"><span class="read-done"></span>'
                f'<span class="rider">{motif_svg(mode, 30, color, 2.6)}</span>'
                f'<span class="read-goal">{motif_svg(motif, 26, color, 2.4)}</span></div>')
    return cover, progress


TRIP_FLAGS = {
    "coree-a-velo": ["kr"], "kyushu-a-velo": ["jp"], "retour-en-europe-a-velo": ["hr", "si", "it"],
    "suisse-en-train": ["ch"], "belle-via-et-vercors": ["fr"], "gorges-du-tarn-a-velo": ["fr"], "passa-pais": ["fr"],
    "toulouse-bordeaux-a-velo": ["fr"], "echappees-a-velo-en-france": ["fr"], "australie": ["au"], "bali": ["id"],
    "nouvelle-zelande": ["nz"], "ouest-americain": ["us"], "japon-2018": ["jp"], "quebec": ["ca"], "canada-2020": ["ca"],
    "colombie": ["co"], "escapades": ["lk", "ph", "me"],
}
CAT_FLAGS = {
    "south-korea": "kr", "japan": "jp", "croatie": "hr", "slovenie": "si", "italie": "it", "suisse": "ch", "france": "fr",
    "australia": "au", "china": "cn", "indonesie": "id", "new-zealand": "nz", "usa": "us", "canada": "ca",
    "colombia": "co", "sri-lanka": "lk", "philippines": "ph", "montenegro": "me",
}
FLAG_CDN = "/assets/img/flags/"


def flags_html(codes, h=16):
    w = round(h * 4 / 3)
    return "".join(f'<img class="flag" src="{FLAG_CDN}{c}.svg" width="{w}" height="{h}" alt="" loading="lazy">' for c in codes)


def trip_flags(trip, h=16):
    return flags_html(TRIP_FLAGS.get(trip["slug"], []), h)


def post_flags(post, h=16):
    codes = []
    for c in post.get("categories", []):
        f = CAT_FLAGS.get(c)
        if f and f not in codes:
            codes.append(f)
    return flags_html(codes, h)
