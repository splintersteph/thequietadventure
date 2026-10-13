"""Les grands éléments du site au-delà des pages de base.

- le globe de l'accueil (traces GPS + trains, cars, voitures, bateaux et avions racontés dans les récits) ;
- le récit « au fil de la route » : carte et profil d'altitude qui suivent la lecture ;
- le passeport ;
- l'index de la recherche instantanée ;
- les images d'aperçu (Open Graph) générées pour chaque récit ;
- les aperçus flous des photos (quelques octets dans la page).

Appelé par build.py.
"""
import base64
import hashlib
import io
import json
import math
import os
import re
import sys
from datetime import date

B = sys.modules['__main__'] if hasattr(sys.modules.get('__main__'), 'layout') else __import__('build')
from decor import CAT_FLAGS, DECOR, flags_html, motif_svg, trip_flags

esc = B.esc
MOIS = {"fr": ['JANV.', 'FÉVR.', 'MARS', 'AVR.', 'MAI', 'JUIN', 'JUIL.', 'AOÛT', 'SEPT.', 'OCT.', 'NOV.', 'DÉC.'],
        "en": ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']}
COUNTRY_NAMES = {
    "kr": ("Corée du Sud", "South Korea"), "jp": ("Japon", "Japan"), "hr": ("Croatie", "Croatia"), "si": ("Slovénie", "Slovenia"),
    "it": ("Italie", "Italy"), "ch": ("Suisse", "Switzerland"), "fr": ("France", "France"), "au": ("Australie", "Australia"),
    "cn": ("Chine", "China"), "id": ("Indonésie", "Indonesia"), "nz": ("Nouvelle-Zélande", "New Zealand"),
    "us": ("États-Unis", "United States"), "ca": ("Canada", "Canada"), "co": ("Colombie", "Colombia"),
    "lk": ("Sri Lanka", "Sri Lanka"), "ph": ("Philippines", "Philippines"), "me": ("Monténégro", "Montenegro"),
}
CAPITAL_CITY = {  # ville du tampon : là où le premier récit commence
    "kr": "Séoul", "jp": "Fukuoka", "hr": "Zagreb", "si": "Ljubljana", "it": "Udine", "ch": "Lucerne", "fr": "Marseille",
    "au": "Sydney", "cn": "Xi'an", "id": "Denpasar", "nz": "Auckland", "us": "Los Angeles", "ca": "Montréal",
    "co": "Bogotá", "lk": "Colombo", "ph": "Palawan", "me": "Kotor",
}
PASSPORT = {"fr": "/passeport/", "en": "/en/passport/"}

S = {
    "fr": {
        "gl_label": "Dix ans de voyages sur un globe", "gl_hint": "Faites tourner le globe",
        "gl_title": "Dix ans de voyages, trace après trace.", "gl_km": "km à vélo et à pied", "gl_countries": "pays", "gl_stories": "récits",
        "gl_legend": "Moyens de transport du voyage", "gl_line": "Les voyages, dans l'ordre",
        "gl_after": "Les traits pleins sont nos traces GPS à vélo et à pied. Entre elles, les trains, cars, voitures, bateaux et avions racontés dans les récits relient les étapes. Cliquez sur un point de la frise pour revenir à un voyage.",
        "gl_js": {"pause": "Pause", "play": "Lecture", "replay": "Rejouer depuis 2015", "all": "Tous les voyages",
                  "all_period": "{n} carnets, du Sri Lanka au Piémont", "locale": "fr-FR",
                  "modes": {"velo": "à vélo", "pied": "à pied", "train": "en train", "bus": "en car et en bus", "voiture": "en voiture",
                            "bateau": "en bateau", "avion": "en avion"}},
        "rt_map": "La carte", "rt_close": "Fermer", "rt_where": "Où nous en sommes", "rt_km": "km {a} sur {b}", "rt_alt": "{a} m d'altitude",
        "ps_title": "Le passeport", "ps_lead": "Un tampon par pays traversé, à la date du premier récit écrit là-bas. Cliquez sur un tampon pour ouvrir le voyage.",
        "ps_label": "Le passeport des voyages", "ps_open": "Ouvrir le passeport", "ps_top": "Carnet de voyage", "ps_open_txt": "Ouvrir",
        "ps_holders": "Titulaires", "ps_holders_v": "Stéphane, Cassandre et Clémence", "ps_transport": "Moyen de transport",
        "ps_transport_v": "Deux vélos, une remorque, des trains", "ps_first": "Premier départ", "ps_first_v": "Sri Lanka, août 2015",
        "ps_countries": "Pays visités", "ps_stories": "Récits", "ps_visas": "Visas", "ps_story": "récit", "ps_story_pl": "récits",
        "nav_passport": "Passeport",
    },
    "en": {
        "gl_label": "Ten years of travels on a globe", "gl_hint": "Spin the globe",
        "gl_title": "Ten years of travels, one trace after another.", "gl_km": "km by bike and on foot", "gl_countries": "countries", "gl_stories": "stories",
        "gl_legend": "How we travelled on this journey", "gl_line": "The journeys, in order",
        "gl_after": "Solid lines are our GPS traces by bike and on foot. In between, the trains, coaches, cars, boats and planes described in the stories link the stages. Click a dot on the timeline to go back to a journey.",
        "gl_js": {"pause": "Pause", "play": "Play", "replay": "Replay from 2015", "all": "All journeys",
                  "all_period": "{n} journals, from Sri Lanka to Piedmont", "locale": "en-GB",
                  "modes": {"velo": "by bike", "pied": "on foot", "train": "by train", "bus": "by coach and bus", "voiture": "by car",
                            "bateau": "by boat", "avion": "by plane"}},
        "rt_map": "The map", "rt_close": "Close", "rt_where": "Where we are", "rt_km": "km {a} of {b}", "rt_alt": "{a} m above sea level",
        "ps_title": "The passport", "ps_lead": "One stamp per country we travelled through, dated from the first story written there. Click a stamp to open the journey.",
        "ps_label": "The travel passport", "ps_open": "Open the passport", "ps_top": "Travel journal", "ps_open_txt": "Open",
        "ps_holders": "Holders", "ps_holders_v": "Stéphane, Cassandre and Clémence", "ps_transport": "Means of transport",
        "ps_transport_v": "Two bikes, a trailer, trains", "ps_first": "First departure", "ps_first_v": "Sri Lanka, August 2015",
        "ps_countries": "Countries visited", "ps_stories": "Stories", "ps_visas": "Visas", "ps_story": "story", "ps_story_pl": "stories",
        "nav_passport": "Passport",
    },
}


# ------------------------------------------------------------------ helpers
def rdp(pts, eps):
    """Douglas-Peucker sur des [lat, lng] (itératif : les longues traces ne font pas déborder la pile)."""
    if len(pts) < 3:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        i0, i1 = stack.pop()
        a, b = pts[i0], pts[i1]
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dy)
        dmax, idx = 0, 0
        for i in range(i0 + 1, i1):
            p = pts[i]
            d = abs(dy * (p[0] - a[0]) - dx * (p[1] - a[1])) / n if n > 1e-12 else math.hypot(p[0] - a[0], p[1] - a[1])
            if d > dmax:
                dmax, idx = d, i
        if dmax > eps:
            keep[idx] = True
            stack += [(i0, idx), (idx, i1)]
    return [p for p, k in zip(pts, keep) if k]


def write_json(rel, data):
    full = os.path.join(B.OUT, rel.lstrip("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))


def countries_of(post):
    out = []
    for c in post.get("categories", []):
        f = CAT_FLAGS.get(c)
        if f and f not in out:
            out.append(f)
    return out


def vt_post(p):
    """Nom de transition partagé entre la vignette d'un récit et sa photo de couverture."""
    return "p" + hashlib.md5(p["slug"].encode()).hexdigest()[:10]


def vt_trip(t):
    return "t-" + re.sub(r"[^a-z0-9-]", "", t["slug"])


# ------------------------------------------------------------------ aperçus flous
LQ_PATH = os.path.join(B.ROOT, "data", "lqip.json")
_LQ = None
_LQ_DIRTY = False


def _lq_cache():
    global _LQ
    if _LQ is None:
        _LQ = json.load(open(LQ_PATH, encoding="utf-8")) if os.path.exists(LQ_PATH) else {}
    return _LQ


def lqip(src):
    """Une miniature de 16 px, floutée par un filtre SVG : l'aperçu s'affiche sans aucune requête."""
    global _LQ_DIRTY
    if not src or not src.startswith("/media/") or not src.lower().endswith((".jpg", ".jpeg", ".webp")):
        return ""
    cache = _lq_cache()
    if src in cache:
        return cache[src]
    local = os.path.join(B.ROOT, src.lstrip("/"))
    if not os.path.exists(local):
        return ""
    try:
        from PIL import Image, ImageOps
        im = Image.open(local)
        im.draft("RGB", (64, 64))
        im = ImageOps.exif_transpose(im).convert("RGB")
        im.thumbnail((16, 16))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=55)
        w, h = im.size
        jpg = base64.b64encode(buf.getvalue()).decode()
        svg = (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {w} {h}' preserveAspectRatio='none'>"
               f"<filter id='b' color-interpolation-filters='sRGB'><feGaussianBlur stdDeviation='.9'/>"
               f"<feComponentTransfer><feFuncA type='discrete' tableValues='1 1'/></feComponentTransfer></filter>"
               f"<image width='{w}' height='{h}' preserveAspectRatio='none' filter='url(#b)' href='data:image/jpeg;base64,{jpg}'/></svg>")
        out = "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()
    except Exception:
        out = ""
    cache[src] = out
    _LQ_DIRTY = True
    return out


def lq_style(src):
    u = lqip(src)
    return f' data-lq style="background-image:url({u})"' if u else ""


def save_lqip():
    if _LQ_DIRTY:
        with open(LQ_PATH, "w", encoding="utf-8") as f:
            json.dump(_lq_cache(), f, separators=(",", ":"), sort_keys=True)


def lq_body(body):
    """Ajoute l'aperçu flou à toutes les photos d'un récit."""
    def rep(m):
        tag = m.group(0)
        if "data-lq" in tag:
            return tag
        src = re.search(r'\ssrc="(/media/[^"]+)"', tag)
        if not src:
            return tag
        return tag[:-1].rstrip("/").rstrip() + lq_style(src.group(1)) + ">"
    return re.sub(r"<img\b[^>]*>", rep, body)


# ------------------------------------------------------------------ 1. le globe
def hav(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * math.asin(min(1, math.sqrt(h)))


def gc_interp(a, b, f):
    """Point à la fraction f du grand cercle entre a et b ([lat, lng])."""
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    d = hav(a, b) / 6371
    if d < 1e-9:
        return a
    A, Bc = math.sin((1 - f) * d) / math.sin(d), math.sin(f * d) / math.sin(d)
    x = A * math.cos(la1) * math.cos(lo1) + Bc * math.cos(la2) * math.cos(lo2)
    y = A * math.cos(la1) * math.sin(lo1) + Bc * math.cos(la2) * math.sin(lo2)
    z = A * math.sin(la1) + Bc * math.sin(la2)
    return [math.degrees(math.atan2(z, math.hypot(x, y))), math.degrees(math.atan2(y, x))]


def densify(pts, step_km=25, plane=False):
    out = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        n = 48 if plane else max(1, min(40, int(hav(a, b) / step_km)))
        out += [gc_interp(a, b, k / n) for k in range(1, n + 1)]
    return out


def line_km(pts):
    return sum(hav(a, b) for a, b in zip(pts, pts[1:]))


ROUTES = None
_SEGS = {}


def trip_segments(t, warn=True):
    """Traces GPS et liaisons des récits, dans l'ordre où elles ont été parcourues."""
    global ROUTES
    if t["slug"] in _SEGS:
        return _SEGS[t["slug"]]
    if ROUTES is None:
        ROUTES = json.load(open(os.path.join(B.ROOT, "data", "routes.json"), encoding="utf-8"))
    ev = []
    for a in t["acts"]:
        pts = rdp(B.decode_polyline(a["poly"]), 0.0012)
        ev.append((a["date"][:10], 1, {"m": "velo" if "Ride" in a["type"] else "pied", "pts": pts, "n": a["name"], "gps": True,
                                        "km": a["dist"] / 1000}))
    for leg in ROUTES.get(t["slug"], []):
        ev.append((leg["d"], 2 if leg.get("after") else 0, dict(leg)))
    ev.sort(key=lambda e: (e[0], e[1]))
    segs = [dict(e[2], d=e[0]) for e in ev]
    for i, sg in enumerate(segs):
        if sg.get("gps"):
            continue
        pts = list(sg["pts"])
        if pts and pts[0] == "prev":
            pts = ([segs[i - 1]["pts"][-1]] if i > 0 else []) + pts[1:]
        if sg.get("to") == "next" and i + 1 < len(segs):
            nxt = segs[i + 1]["pts"][0]
            if nxt != "prev":
                pts = pts + [nxt]
        sg["pts"] = densify(pts, plane=sg["m"] == "avion")
        sg["km"] = line_km(sg["pts"])
    if warn:
        for a, b in zip(segs, segs[1:]):  # trous qui restent : on les signale à la construction
            gap = hav(a["pts"][-1], b["pts"][0])
            if gap > 12 and b["m"] != "avion" and a["m"] != "avion":
                da, db = date.fromisoformat(a["d"]), date.fromisoformat(b["d"])
                if (db - da).days <= 4:
                    print(f"  [globe] trou de {gap:.0f} km dans {t['slug']} le {b['d']} avant « {b.get('n', '')} »")
    _SEGS[t["slug"]] = segs
    return segs


LEG_DASH = {"train": "1 6", "bus": "9 6", "voiture": "4 5", "bateau": "1 7", "avion": "1 9"}


def leg_lines(t):
    """Les liaisons (train, car, voiture, bateau) à ajouter sur la carte Leaflet d'un voyage."""
    out = []
    for sg in trip_segments(t, warn=False):
        if sg.get("gps") or sg["m"] in ("velo", "pied", "avion"):
            continue
        out.append({"points": [[round(p[0], 4), round(p[1], 4)] for p in sg["pts"]], "color": t["color"], "weight": 3,
                    "dash": LEG_DASH.get(sg["m"], "4 6"), "mode": sg["m"]})
    return out


def _chapters(trips):
    """Découpe un voyage quand un autre commence pendant qu'il dure (Bali au milieu de l'Australie,
    Kyushu au milieu de la Corée), pour que le globe déroule tout dans l'ordre chronologique."""
    out = []
    for t in trips:
        cuts = sorted(o["start"] for o in trips if o is not t and t["start"] < o["start"] < t["end"])
        segs = trip_segments(t, warn=False)
        bounds = [None] + cuts + [None]
        for i in range(len(bounds) - 1):
            lo, hi = bounds[i], bounds[i + 1]
            ps = [p for p in t["posts"] if (lo is None or p["dt"] >= lo) and (hi is None or p["dt"] < hi)]
            sg = [x for x in segs if (lo is None or x["d"] >= lo.date().isoformat()) and (hi is None or x["d"] < hi.date().isoformat())]
            if not ps and not sg:
                continue
            start = min([p["dt"] for p in ps] or [lo or t["start"]])
            out.append({"trip": t, "posts": ps, "segs": sg, "start": start, "part": i})
    for c in out:
        c["n_parts"] = sum(1 for x in out if x["trip"] is c["trip"])
    return sorted(out, key=lambda c: c["start"])


def globe_data(trips, lang):
    for t in trips:
        trip_segments(t, warn=lang == "fr")
    seen_c, n_posts, km_self, out = set(), 0, 0.0, []
    for ch in _chapters(trips):
        t, segs = ch["trip"], ch["segs"]
        by_mode = {}
        for sg in segs:
            by_mode[sg["m"]] = by_mode.get(sg["m"], 0) + sg["km"]
            if sg["m"] in ("velo", "pied"):
                km_self += sg["km"]
        for p in ch["posts"]:
            seen_c.update(countries_of(p))
        n_posts += len(ch["posts"])
        title = t["title"][lang]
        if ch["part"] > 0 and ch["n_parts"] > 1:
            title += " (suite)" if lang == "fr" else " (continued)"
        out.append({
            "slug": t["slug"], "title": title, "period": t["period"][lang], "color": t["color"],
            "mode": t.get("mode", "roadtrip"), "url": B.trip_url(t, lang), "year": ch["start"].year,
            "flags": trip_flags(t, 18),
            "segs": [{"m": sg["m"], "c": [[round(p[1], 3), round(p[0], 3)] for p in sg["pts"]]} for sg in segs],
            "modes": {k: round(v) for k, v in by_mode.items()},
            "pins": [[round(p["geo"][1], 3), round(p["geo"][0], 3)] for p in ch["posts"] if p.get("geo")],
            "km": round(km_self), "countries": len(seen_c), "stories": n_posts,
        })
    return out


def globe_section(lang, trips):
    s = S[lang]
    write_json(f"/data/globe-{lang}.json", globe_data(trips, lang))
    i18n = dict(s["gl_js"], trips=B.PATHS[lang]["trips"], data=f"/data/globe-{lang}.json?v={B.VERSION}")
    return f"""<section class="gl-sec" id="globe" aria-label="{esc(s['gl_label'])}"><div class="gl" data-i18n="{esc(json.dumps(i18n, ensure_ascii=False))}">
<div class="gl-stage"><canvas class="gl-canvas" aria-hidden="true"></canvas><p class="gl-hint">{s['gl_hint']}</p></div>
<div class="gl-side">
<p class="gl-year" aria-live="polite">2015</p>
<h2 class="gl-title">{s['gl_title']}</h2>
<p class="gl-trip"><span class="gl-flags"></span><a class="gl-name" href="{B.PATHS[lang]['trips']}">&nbsp;</a><span class="gl-period"></span></p>
<dl class="gl-count">
<div><dt>{s['gl_km']}</dt><dd data-k="km">0</dd></div>
<div><dt>{s['gl_countries']}</dt><dd data-k="countries">0</dd></div>
<div><dt>{s['gl_stories']}</dt><dd data-k="stories">0</dd></div>
</dl>
<ul class="gl-legend" aria-label="{esc(s['gl_legend'])}"></ul>
<ol class="gl-line" aria-label="{esc(s['gl_line'])}"></ol>
<div class="gl-ctrl"><button type="button" class="gl-play" aria-pressed="false">{s['gl_js']['play']}</button><button type="button" class="gl-replay">{s['gl_js']['replay']}</button></div>
</div></div>
<p class="wrap gl-after">{s['gl_after']}</p></section>"""


GLOBE_SCRIPTS = ('<script src="/assets/vendor/d3-array.min.js" defer></script>\n<script src="/assets/vendor/d3-geo.min.js" defer></script>\n'
                 '<script src="/assets/vendor/topojson-client.min.js" defer></script>\n<script src="/assets/js/globe.js?v={v}" defer></script>')


# ------------------------------------------------------------------ 2. le récit au fil de la route
ALT = None
MONTH_RE = {
    "fr": re.compile(r"(\d{1,2})(?:er)?\s+(janvier|f[ée]vrier|mars|avril|mai|juin|juillet|ao[ûu]t|septembre|octobre|novembre|d[ée]cembre)", re.I),
    "en": re.compile(r"(?:(\d{1,2})(?:st|nd|rd|th)?\s+(january|february|march|april|may|june|july|august|september|october|november|december))"
                     r"|(?:(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2}))", re.I),
}
MONTH_IDX = {m: i + 1 for i, m in enumerate(["janvier", "fevrier", "mars", "avril", "mai", "juin", "juillet", "aout", "septembre", "octobre", "novembre", "decembre"])}
MONTH_IDX.update({m: i + 1 for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"])})


def _month(name):
    n = name.lower().replace("é", "e").replace("û", "u")
    return MONTH_IDX.get(n)


def h4_date(text, lang):
    m = MONTH_RE[lang].search(text) or MONTH_RE["fr" if lang == "en" else "en"].search(text)
    if not m:
        return None
    g = [x for x in m.groups() if x]
    day = next(int(x) for x in g if x.isdigit())
    mon = next(_month(x) for x in g if not x.isdigit())
    return (mon, day)


def route_body(p, body, lang):
    """Marque les intertitres datés du récit avec l'activité Strava du même jour, et prépare les données de la carte."""
    global ALT
    acts = sorted(p.get("acts") or [], key=lambda a: a["date"])
    if not acts:
        return body, ""
    if ALT is None:
        path = os.path.join(B.ROOT, "data", "altitude", "altitude.json")
        ALT = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    by_day = {}
    for i, a in enumerate(acts):
        d = date.fromisoformat(a["date"][:10])
        by_day.setdefault((d.month, d.day), []).append(i)
    used = set()

    def mark(m):
        key = h4_date(re.sub(r"<[^>]+>", "", m.group(2)), lang)
        idx = by_day.get(key) if key else None
        if not idx or idx[0] in used:
            return m.group(0)
        used.update(idx)
        return f'<h4{m.group(1)} data-acts="{idx[0]},{idx[-1]}">{m.group(2)}</h4>'
    body = re.sub(r"<h4([^>]*)>(.*?)</h4>", mark, body, flags=re.S)
    start, data = 0.0, []
    for a in acts:
        pts = rdp(B.decode_polyline(a["poly"]), 0.00015)
        al = ALT.get(a["id"])
        if al:  # médiane glissante : enlève les pics GPS
            al = [round(sorted(al[max(0, i - 1):i + 2])[len(al[max(0, i - 1):i + 2]) // 2]) for i in range(len(al))]
        d = date.fromisoformat(a["date"][:10])
        name = re.sub(r"\s*(->|➡️|➡|→)\s*", " → ", a["name"]).strip()
        data.append({"line": [[round(q[0], 5), round(q[1], 5)] for q in pts], "km": round(a["dist"] / 1000, 2), "start": round(start, 2),
                     "alt": al or None, "day": B.fdate(d, lang), "name": name, "kind": "velo" if "Ride" in a["type"] else "pied"})
        start += a["dist"] / 1000
    trip = p.get("trip") or {}
    s = S[lang]
    payload = {"color": trip.get("color", "#2F5D50"), "acts": data,
               "t": {"km": s["rt_km"], "alt": s["rt_alt"], "map": s["rt_map"], "close": s["rt_close"]}}
    return body, json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def route_panel(lang, mode):
    s = S[lang]
    return f"""<div class="rt" aria-label="{esc(s['rt_where'])}" role="region">
<div class="rt-map"></div>
<div class="rt-now"><b class="rt-day"></b><span class="rt-km"></span><span class="rt-alt"></span></div>
<svg class="rt-prof" viewBox="0 0 600 110" preserveAspectRatio="none" aria-hidden="true"></svg></div>"""


def route_extras(lang, mode, color):
    """La barre du haut (silhouette de l'étape) et le bouton « La carte » sur mobile."""
    s = S[lang]
    return (f'<div class="rt-top" aria-hidden="true" style="--trip:{color}"><svg class="rt-top-svg" preserveAspectRatio="none"></svg>'
            f'<span class="rt-top-bike">{motif_svg(mode if mode in ("velo", "pied") else "velo", 20, "currentColor", 2.6)}</span></div>'
            f'<button class="rt-btn" type="button" aria-expanded="false" style="--trip:{color}">{motif_svg("velo", 24, "currentColor", 2.4)}<span>{s["rt_map"]}</span></button>')


# ------------------------------------------------------------------ 3. le passeport
def page_passport(lang, posts):
    s = S[lang]
    per = {}
    for p in posts:
        for c in countries_of(p):
            e = per.setdefault(c, {"first": p["dt"], "n": 0, "trips": []})
            e["n"] += 1
            e["first"] = min(e["first"], p["dt"])
            if p.get("trip") and p["trip"] not in e["trips"]:
                e["trips"].append(p["trip"])
    order = sorted(per, key=lambda c: per[c]["first"])
    shapes = ["round", "rect", "oval", "hex", "round", "rect", "oval"]
    stamps = ""
    for i, c in enumerate(order):
        e = per[c]
        t = e["trips"][0] if e["trips"] else None
        color = t["color"] if t else "#6B6157"
        mode = t.get("mode", "roadtrip") if t else "roadtrip"
        rot = ((i * 37) % 21) - 10
        import design
        url = design.country_url(c, lang)
        d = e["first"]
        stamps += f"""<a class="ps-stamp {shapes[i % len(shapes)]}" href="{url}" style="--c:{color};--r:{rot}deg;--i:{i}">
<span class="ps-in">{motif_svg(mode, 30, "currentColor", 2.4)}<b>{esc(COUNTRY_NAMES[c][0 if lang == 'fr' else 1])}</b><span class="ps-city">{esc(CAPITAL_CITY.get(c, ''))}</span>
<span class="ps-date">{d.day} {MOIS[lang][d.month - 1]} {d.year}</span><span class="ps-n">{e['n']} {s['ps_story'] if e['n'] == 1 else s['ps_story_pl']}</span></span></a>"""
    n = len(posts)
    body = f"""<section class="ps" aria-label="{esc(s['ps_label'])}">
<div class="ps-intro wrap"><h1>{s['ps_title']}</h1><p>{s['ps_lead']}</p></div>
<div class="ps-book" data-open="false">
<button class="ps-cover" type="button" aria-label="{esc(s['ps_open'])}" aria-expanded="false">
<span class="ps-cv-top">{s['ps_top']}</span>
<svg class="ps-emblem" viewBox="0 0 120 120" width="120" height="120" aria-hidden="true"><g fill="none" stroke="currentColor" stroke-width="2"><circle cx="60" cy="60" r="44"/><ellipse cx="60" cy="60" rx="18" ry="44"/><path d="M16 60h88M22 38h76M22 82h76"/></g></svg>
<span class="ps-cv-title">The Quiet Adventure</span><span class="ps-cv-sub">{'Passeport' if lang == 'fr' else 'Passport'} · 2015 – {max(p['dt'].year for p in posts)}</span><span class="ps-cv-open">{s['ps_open_txt']}</span></button>
<div class="ps-pages">
<div class="ps-id"><div class="ps-photo">{motif_svg("velo", 64, "currentColor", 2)}</div>
<dl><div><dt>{s['ps_holders']}</dt><dd>{s['ps_holders_v']}</dd></div><div><dt>{s['ps_transport']}</dt><dd>{s['ps_transport_v']}</dd></div>
<div><dt>{s['ps_first']}</dt><dd>{s['ps_first_v']}</dd></div><div><dt>{s['ps_countries']}</dt><dd>{len(order)}</dd></div><div><dt>{s['ps_stories']}</dt><dd>{n}</dd></div></dl>
<p class="ps-mrz" aria-hidden="true">P&lt;FRATHE&lt;QUIET&lt;ADVENTURE&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;<br>2015&lt;&lt;{len(order):02d}{'PAYS' if lang == 'fr' else 'CTRY'}&lt;&lt;{n}{'RECITS' if lang == 'fr' else 'STORIES'}&lt;&lt;{'A&lt;VELO' if lang == 'fr' else 'BY&lt;BIKE'}&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;</p></div>
<div class="ps-visas"><h2>{s['ps_visas']}</h2><div class="ps-grid">{stamps}</div></div>
</div></div></section>"""
    other = PASSPORT["en" if lang == "fr" else "fr"]
    B.write(PASSPORT[lang], B.layout(lang, PASSPORT[lang], s["ps_title"], s["ps_lead"], body, other, active="passport", body_class="page-passport"))


# ------------------------------------------------------------------ 4. la recherche
def search_index(posts, lang):
    out = []
    for p in sorted(posts, key=lambda q: q["dt"], reverse=True):
        v = B.V(p, lang)
        t = p.get("trip")
        out.append({"t": v["title"], "u": v["url"], "d": B.fdate(p["dt"], lang), "y": p["dt"].year,
                    "j": t["title"][lang] if t else "", "c": B.media(p.get("cover"), 240) if p.get("cover") else "",
                    "f": flags_html(countries_of(p), 13), "x": B.text_of(v["body"])})
    write_json(f"/data/search-{lang}.json", out)


# ------------------------------------------------------------------ 5. les aperçus de partage
FONTS = os.path.join(B.ROOT, "tools", "fonts")
_FONT = {}


def font(name, size, weight=None, opsz=None):
    from PIL import ImageFont
    key = (name, size, weight, opsz)
    if key not in _FONT:
        f = ImageFont.truetype(os.path.join(FONTS, name + ".ttf"), size)
        try:
            axes = f.get_variation_axes()
            vals = []
            for ax in axes:
                nm = ax["name"].decode() if isinstance(ax["name"], bytes) else ax["name"]
                if nm == "Weight":
                    vals.append(weight or ax["default"])
                elif nm == "Optical Size":
                    vals.append(opsz or min(ax["maximum"], size))
                else:
                    vals.append(ax["default"])
            f.set_variation_by_axes(vals)
        except Exception:
            pass
        _FONT[key] = f
    return _FONT[key]


def _hex(c, a=255):
    c = c.lstrip("#")
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), a)


def _wrap(draw, text, fnt, width, max_lines):
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textlength(test, font=fnt) <= width or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        while draw.textlength(lines[-1] + "…", font=fnt) > width and " " in lines[-1]:
            lines[-1] = lines[-1].rsplit(" ", 1)[0]
        lines[-1] += "…"
    return lines


def og_image(p, lang):
    """Une image 1200 × 630 par récit : la photo, le tampon du voyage, la trace de l'étape, ses kilomètres."""
    cover = p.get("cover")
    if not cover or not cover.startswith("/media/"):
        return None
    local = os.path.join(B.ROOT, cover.lstrip("/"))
    if not os.path.exists(local):
        return None
    try:
        from PIL import Image, ImageDraw, ImageOps
    except ImportError:
        return None
    v = B.V(p, lang)
    t = p.get("trip")
    color = t["color"] if t else "#A8641F"
    W, H, PW = 1200, 630, 696
    img = Image.new("RGB", (W, H), "#F3ECDF")
    ph = Image.open(local)
    ph.draft("RGB", (PW * 2, H * 2))
    ph = ImageOps.exif_transpose(ph).convert("RGB")
    img.paste(ImageOps.fit(ph, (PW, H), Image.LANCZOS), (0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([PW, 0, PW + 7, H], fill=color)
    x0, xw = PW + 46, W - PW - 46 - 44
    # le tampon du voyage, légèrement penché
    if t:
        S2 = 2
        st = Image.new("RGBA", (180 * S2, 180 * S2), (0, 0, 0, 0))
        sd = ImageDraw.Draw(st)
        c = _hex(color, 230)
        cx = 90 * S2
        sd.ellipse([6 * S2, 6 * S2, 174 * S2, 174 * S2], outline=c, width=3 * S2)
        sd.ellipse([22 * S2, 22 * S2, 158 * S2, 158 * S2], outline=c, width=1 * S2)
        label = DECOR.get(t["slug"], (None, None, {"fr": "", "en": ""}))[2][lang]
        f1 = font("Karla", 15 * S2, 700)
        f2 = font("Newsreader", 40 * S2, 500)
        lines = _wrap(sd, label, f1, 120 * S2, 2)
        y = cx - (len(lines) * 19 * S2 + 46 * S2) / 2
        for ln in lines:
            sd.text((cx, y), ln, font=f1, fill=c, anchor="mt")
            y += 19 * S2
        sd.text((cx, y + 4 * S2), str(p["dt"].year), font=f2, fill=c, anchor="mt")
        st = st.resize((180, 180), Image.LANCZOS).rotate(-11, resample=Image.BICUBIC, expand=True)
        img.paste(st, (W - st.width - 18, 16), st)
    # la trace de l'étape
    pts = [q for a in (p.get("acts") or []) for q in B.decode_polyline(a["poly"])]
    if len(pts) > 1:
        S2, box = 3, 150
        la = [q[0] for q in pts]
        ln = [q[1] for q in pts]
        k = math.cos(math.radians(sum(la) / len(la)))
        w, h = (max(ln) - min(ln)) * k or 1e-6, (max(la) - min(la)) or 1e-6
        sc = (box - 20) / max(w, h)
        ox, oy = (box - w * sc) / 2, (box - h * sc) / 2
        tr = Image.new("RGBA", (box * S2, box * S2), (0, 0, 0, 0))
        td = ImageDraw.Draw(tr)
        xy = [((ox + (q[1] - min(ln)) * k * sc) * S2, (oy + (max(la) - q[0]) * sc) * S2) for q in rdp(pts, 0.0004)]
        td.line(xy, fill=_hex(color), width=4 * S2, joint="curve")
        r = 6 * S2
        td.ellipse([xy[-1][0] - r, xy[-1][1] - r, xy[-1][0] + r, xy[-1][1] + r], fill=_hex(color))
        tr = tr.resize((box, box), Image.LANCZOS)
        img.paste(tr, (x0 - 10, 86), tr)
    # textes
    fk = font("Caveat", 34, 600)
    kicker = t["title"][lang] if t else ""
    if t and p.get("step"):
        kicker += f" · {'étape' if lang == 'fr' else 'stage'} {p['step']}"
    ft = font("Newsreader", 52, 400, 48)
    title_lines = _wrap(d, v["title"], ft, xw, 4)
    y = H - 64 - len(title_lines) * 56 - 50
    for ln_ in _wrap(d, kicker, fk, xw, 1):
        d.text((x0, y), ln_, font=fk, fill="#A8641F")
    y += 46
    for ln_ in title_lines:
        d.text((x0, y), ln_, font=ft, fill="#2A2521")
        y += 56
    ff = font("Karla", 21, 700)
    fy = H - 52
    fx = x0
    km = B.act_totals(p.get("acts") or [])[0] if p.get("acts") else 0
    if km:
        lbl = f"{B.fkm(km, lang)} km"
        tw = d.textlength(lbl, font=ff)
        d.rounded_rectangle([fx, fy - 6, fx + tw + 28, fy + 28], radius=17, outline="#2A2521", width=2)
        d.text((fx + 14, fy + 11), lbl, font=ff, fill="#2A2521", anchor="lm")
        fx += tw + 44
    d.text((fx, fy + 11), B.fdate(p["dt"], lang), font=font("Karla", 21, 500), fill="#6B6157", anchor="lm")
    d.text((x0, 40), "The Quiet Adventure", font=font("Newsreader", 24, 600, 24), fill="#2A2521")
    d.text((x0, 72), "carnet de route" if lang == "fr" else "travel journal", font=font("Caveat", 24, 500), fill="#A8641F")
    rel = f"/og/{'en/' if lang == 'en' else ''}{p['slug']}.jpg"
    full = os.path.join(B.OUT, rel.lstrip("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    img.save(full, "JPEG", quality=84, optimize=True, progressive=True)
    return rel
