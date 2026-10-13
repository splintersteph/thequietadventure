"""Mise en page des récits et pages de découverte.

- les mosaïques : les photos qui se suivent dans un récit sont regroupées en blocs variés
  (une grande et des petites) au lieu de lignes de trois puis de deux ;
- des ancres sur les intertitres datés (#jour-2019-03-21), pour la frise ;
- la frise d'un voyage : un point par jour raconté, cliquable ;
- « Ce jour-là » sur l'accueil : un récit écrit à la même date une autre année ;
- une page par pays.

Appelé par build.py.
"""
import html as _html
import json
import os
import re
import sys
from datetime import date

B = sys.modules['__main__'] if hasattr(sys.modules.get('__main__'), 'layout') else __import__('build')
import extras as X
from decor import flags_html

esc = B.esc

# ------------------------------------------------------------------ 1. les mosaïques
_SIZE = {}


def _dims(tag):
    """(largeur, hauteur) d'une photo : attributs width/height, sinon le fichier local."""
    w = re.search(r'\swidth="(\d+)"', tag)
    h = re.search(r'\sheight="(\d+)"', tag)
    if w and h:
        return int(w.group(1)), int(h.group(1))
    m = re.search(r'\ssrc="(/media/[^"?]+)', tag)
    if not m:
        return 4, 3
    src = m.group(1)
    if src not in _SIZE:
        path = os.path.join(B.ROOT, src.lstrip("/"))
        try:
            from PIL import Image, ImageOps
            with Image.open(path) as im:
                o = im.getexif().get(0x0112, 1)
                w_, h_ = im.size
                _SIZE[src] = (h_, w_) if o in (5, 6, 7, 8) else (w_, h_)
        except Exception:
            _SIZE[src] = (4, 3)
    return _SIZE[src]


_FIG = re.compile(r'^<figure(?: class="[^"]*")?>\s*(<img\b[^>]*>)\s*(?:<figcaption>(.*?)</figcaption>)?\s*</figure>$', re.S)
_GAL = re.compile(r'^<div class="gallery g\d">((?:\s*<img\b[^>]*>)+)\s*</div>$', re.S)
_IMG = re.compile(r'^<img\b[^>]*>$')


def _items(line):
    """Les photos d'une ligne du récit, ou None si la ligne n'est pas faite que de photos."""
    s = line.strip()
    m = _FIG.match(s)
    if m:
        cap = m.group(2)
        cap = re.sub(r"</?strong>", "", cap).strip() if cap else ""
        return [(m.group(1), cap)]
    m = _GAL.match(s)
    if m:
        return [(t, "") for t in re.findall(r"<img\b[^>]*>", m.group(1))]
    if _IMG.match(s):
        return [(s, "")]
    return None


def _chunks(n):
    out = []
    while n > 5:
        take = 5 if n - 5 != 1 else 3
        out.append(take)
        n -= take
    out.append(n)
    return out


def _tile(tag, cap, extra=""):
    tag = re.sub(r'\s(width|height)="\d+"', "", tag)
    c = f"<figcaption>{cap}</figcaption>" if cap else ""
    return f'<figure class="mz-i{extra}">{tag}{c}</figure>'


def _block(items, flip):
    n = len(items)
    land = [w >= h for w, h in (_dims(t) for t, _ in items)]
    if n == 1:
        t, c = items[0]
        return f'<figure>{t}{f"<figcaption>{c}</figcaption>" if c else ""}</figure>'
    if n == 2:
        kind = "p2e" if land[0] == land[1] and not land[0] else "p2"
    elif n == 3:
        kind = "p3w" if land[0] else "p3t"
    else:
        kind = f"p{n}"
        if n in (4, 5) and land[0] and not any(land[1:]):  # une grande paysage, des portraits : on garde
            pass
    cls = f"mz mz-{kind}" + (" flip" if flip else "")
    return f'<div class="{cls}">' + "".join(_tile(t, c, " big" if i == 0 else "") for i, (t, c) in enumerate(items)) + "</div>"


def mosaic(body):
    """Regroupe les photos consécutives d'un récit en mosaïques."""
    lines = body.split("\n")
    out, run = [], []
    count = [0]

    def flush():
        if not run:
            return
        items = [x for r in run for x in r[1]]
        if len(items) == 1:
            out.append(run[0][0])
        else:
            parts, i = [], 0
            for k in _chunks(len(items)):
                parts.append(_block(items[i:i + k], count[0] % 2 == 1))
                count[0] += 1
                i += k
            out.append('<div class="mosaic">' + "".join(parts) + "</div>")
        run.clear()
    for line in lines:
        if not line.strip() and run:
            continue
        it = _items(line)
        if it:
            run.append((line, it))
        else:
            flush()
            out.append(line)
    flush()
    return "\n".join(out)


# ------------------------------------------------------------------ 2. les ancres de jour
def day_ids(p, body, lang):
    """Ajoute id="jour-AAAA-MM-JJ" aux intertitres datés ; renvoie (body, [(date, ancre, titre)])."""
    days, seen = [], set()
    year = p["dt"].year
    month0 = p["dt"].month

    def mark(m):
        attrs, inner = m.group(1), m.group(2)
        txt = _html.unescape(re.sub(r"<[^>]+>", "", inner))
        key = X.h4_date(txt, lang)
        if not key:
            return m.group(0)
        mo, d = key
        y = re.search(r"\b(20\d\d)\b", txt)
        y = int(y.group(1)) if y else (year - 1 if mo > month0 + 6 else year)  # un récit de janvier qui raconte décembre
        try:
            dd = date(y, mo, d)
        except ValueError:
            return m.group(0)
        aid = f"jour-{dd.isoformat()}"
        if aid in seen or "id=" in attrs:
            return m.group(0)
        seen.add(aid)
        days.append((dd, aid, txt.strip()))
        return f'<h4{attrs} id="{aid}">{inner}</h4>'
    body = re.sub(r"<h4([^>]*)>(.*?)</h4>", mark, body, flags=re.S)
    return body, days


DAYS = {}  # (slug, lang) -> jours racontés, rempli au moment des pages récits


def collect_days(posts):
    for p in posts:
        for lang in ("fr", "en"):
            v = B.V(p, lang) if (lang == "fr" or p.get("en")) else None
            if v is None:
                continue
            _, days = day_ids(p, v["body"], lang)
            DAYS[(p["slug"], lang)] = days


# ------------------------------------------------------------------ 3. la frise d'un voyage
S = {
    "fr": {"frise": "Le voyage, jour après jour", "frise_n": "jours racontés", "frise_hint": "Chaque point est un jour raconté : cliquez pour le lire.",
           "otd_kicker": "Ce jour-là", "otd_years": ["Il y a un an", "Il y a {n} ans"], "otd_near": "À quelques jours près, il y a {n} ans",
           "otd_read": "Relire ce jour →", "country_kicker": "Pays", "country_trips": "Les voyages", "country_stories": "Tous les récits",
           "country_map": "Les récits sur la carte", "countries": "Les pays", "first_visit": "Première visite",
           "country_lead": "{n} récits, de {a} à {b}.", "country_lead_y": "{n} récits, en {a}.", "country_lead1": "Un récit, en {a}."},
    "en": {"frise": "The journey, day by day", "frise_n": "days told", "frise_hint": "Each dot is a day we wrote about: click to read it.",
           "otd_kicker": "On this day", "otd_years": ["One year ago", "{n} years ago"], "otd_near": "Give or take a few days, {n} years ago",
           "otd_read": "Read that day again →", "country_kicker": "Country", "country_trips": "Journeys", "country_stories": "All the stories",
           "country_map": "The stories on the map", "countries": "Countries", "first_visit": "First visit",
           "country_lead": "{n} stories, from {a} to {b}.", "country_lead_y": "{n} stories, in {a}.", "country_lead1": "One story, in {a}."},
}


def trip_frise(trip, lang):
    """Une ligne de points : un par jour raconté, posés à leur date entre le début et la fin du voyage."""
    pts = []
    for p in trip["posts"]:
        if lang == "en" and not p.get("en"):
            v = B.V(p, "fr")
        else:
            v = B.V(p, lang)
        days = DAYS.get((p["slug"], lang)) or DAYS.get((p["slug"], "fr")) or []
        if days:
            for d, aid, txt in days:
                pts.append((d, f"{v['url']}#{aid}", v["title"], p["step"]))
        else:
            pts.append((p["dt"].date(), v["url"], v["title"], p["step"]))
    if len(pts) < 3:
        return ""
    pts.sort(key=lambda x: x[0])
    a, b = pts[0][0], pts[-1][0]
    span = max(1, (b - a).days)
    if span > 400:  # les années d'expatriation : la frise n'apporterait rien
        return ""
    dots, months, seen_m = "", "", set()
    for d, url, title, step in pts:
        x = (d - a).days / span * 100
        label = f"{B.fdate(d, lang)} · {title}"
        dots += (f'<a class="fz-dot" href="{url}" style="--x:{x:.2f}%" data-step="{step % 2}" aria-label="{esc(label)}">'
                 f'<span class="fz-tip">{esc(B.fdate(d, lang))}<b>{esc(title)}</b></span></a>')
    cur = date(a.year, a.month, 1)
    while cur <= b:
        if cur >= a or not months:
            x = max(0, (cur - a).days) / span * 100
            months += f'<span class="fz-m" style="--x:{x:.2f}%">{esc(B.fdate(cur, lang, False))}</span>'
        cur = date(cur.year + (cur.month == 12), cur.month % 12 + 1, 1)
    s = S[lang]
    n = len({d for d, *_ in pts})
    return f"""<section class="frise-sec" style="--trip:{trip['color']}"><div class="wrap">
<div class="fz-head"><p class="kicker">{s['frise']}</p><span class="fz-n"><b>{n}</b> {s['frise_n']}</span></div>
<div class="fz-scroll"><div class="fz" style="--w:{max(100, span * 1.6):.0f}">
<div class="fz-line"></div>{dots}<div class="fz-months">{months}</div></div></div>
<p class="fz-hint">{s['frise_hint']}</p></div></section>"""


# ------------------------------------------------------------------ 4. « Ce jour-là »
def on_this_day(posts, lang):
    """Les jours racontés de tous les récits (embarqués dans l'accueil ; le navigateur choisit selon la date du jour)."""
    rows = []
    for p in posts:
        if lang == "en" and not p.get("en"):
            continue
        v = B.V(p, lang)
        days = DAYS.get((p["slug"], lang)) or []
        trip = p.get("trip") or {}
        base = {"t": v["title"], "c": B.media(p.get("cover"), 900) if p.get("cover") else "",
                "v": trip.get("title", {}).get(lang, ""), "k": trip.get("color", "#2F5D50"), "e": v["excerpt"][:180]}
        if days:
            for d, aid, txt in days:
                rows.append(dict(base, d=d.isoformat(), u=f"{v['url']}#{aid}"))
        else:
            rows.append(dict(base, d=p["dt"].date().isoformat(), u=v["url"]))
    s = S[lang]
    data = json.dumps({"rows": rows, "t": {"years": s["otd_years"], "near": s["otd_near"], "read": s["otd_read"]},
                       "lang": lang}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return f"""<section class="otd" hidden><div class="wrap"><a class="otd-card" href="#">
<span class="otd-img"></span><span class="otd-txt"><span class="kicker">{s['otd_kicker']}</span><span class="otd-when"></span>
<b class="otd-title"></b><span class="otd-ex"></span><span class="otd-go"></span></span></a></div>
<script type="application/json" id="otd-data">{data}</script></section>"""


# ------------------------------------------------------------------ 5. les pages pays
CPATH = {"fr": "/pays/", "en": "/en/countries/"}


def country_slug(code, lang):
    name = X.COUNTRY_NAMES[code][0 if lang == "fr" else 1]
    import unicodedata
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def country_url(code, lang):
    return f"{CPATH[lang]}{country_slug(code, lang)}/"


def pages_countries(posts, lang):
    per = {}
    for p in posts:
        for c in X.countries_of(p):
            per.setdefault(c, []).append(p)
    s = S[lang]
    for c, ps in per.items():
        ps.sort(key=lambda p: p["dt"])
        name = X.COUNTRY_NAMES[c][0 if lang == "fr" else 1]
        url = country_url(c, lang)
        other = country_url(c, "en" if lang == "fr" else "fr")
        trips = []
        for p in ps:
            if p.get("trip") and p["trip"] not in trips:
                trips.append(p["trip"])
        a, b = ps[0]["dt"].year, ps[-1]["dt"].year
        lead = (s["country_lead1"].format(a=a) if len(ps) == 1 else
                s["country_lead_y"].format(n=len(ps), a=a) if a == b else s["country_lead"].format(n=len(ps), a=a, b=b))
        cover = next((p["cover"] for p in reversed(ps) if p.get("cover")), None)
        trip_cards = "".join(B.trip_card(t, lang) for t in trips)
        groups = ""
        for t in trips + [None]:
            grp = [p for p in ps if (p.get("trip") is t)]
            if not grp:
                continue
            head = (f'<h3 class="cty-trip"><a href="{B.trip_url(t, lang)}" style="--trip:{t["color"]}">{esc(t["title"][lang])}</a>'
                    f'<span>{esc(t["period"][lang])}</span></h3>') if t else ""
            groups += head + f'<div class="grid3">{"".join(B.story_card(p, lang) for p in grp)}</div>'
        pts = [{"lat": p["geo"][0], "lng": p["geo"][1], "title": B.V(p, lang)["title"], "url": B.V(p, lang)["url"],
                "color": (p.get("trip") or {}).get("color", "#2F5D50")} for p in ps if p.get("geo")]
        map_sec = ""
        if pts:
            map_sec = f"""<section class="section band" style="padding:56px 0"><div class="wrap"><p class="kicker">{s['country_map']}</p>
{B.map_div({"points": pts, "fit": "points"}, "map", s['country_map'])}</div></section>"""
        body = f"""<section class="trip-hero cty-hero">{B.img(cover, name, cls='', width=1800, extra=' fetchpriority="high"')}
<div class="wrap"><a class="crumbs" href="{X.PASSPORT[lang]}">← {'Le passeport' if lang == 'fr' else 'The passport'}</a>
<p class="kicker" style="margin-top:18px">{s['country_kicker']}</p><h1><span class="cty-flag">{flags_html([c], 34)}</span>{esc(name)}</h1><p>{esc(lead)}</p></div></section>
{map_sec}
<section class="section"><div class="wrap"><div class="sec-head"><div><p class="kicker">{s['country_trips']}</p></div></div>
<div class="grid3">{trip_cards}</div></div></section>
<section class="section" style="padding-top:0"><div class="wrap"><div class="sec-head"><div><p class="kicker">{s['country_stories']}</p></div></div>
{groups}</div></section>"""
        B.write(url, B.layout(lang, url, name, lead, body, other, image=cover, active="passport"))


# ------------------------------------------------------------------ 6. les tracés du jour, en dessin
def day_sketches(body, acts, color, lang):
    """À côté de chaque intertitre daté, la trace GPS du jour dessinée à la plume."""
    if not acts:
        return body
    acts = sorted(acts, key=lambda a: a["date"])

    def svg(i, j):
        pts = []
        for a in acts[i:j + 1]:
            pts += X.rdp(B.decode_polyline(a["poly"]), 0.0004)
        if len(pts) < 2:
            return ""
        import math
        lat0 = sum(p[0] for p in pts) / len(pts)
        k = math.cos(math.radians(lat0))
        xs = [p[1] * k for p in pts]
        ys = [-p[0] for p in pts]
        w, h, pad = 150, 96, 8
        sx = (w - 2 * pad) / max(1e-9, max(xs) - min(xs))
        sy = (h - 2 * pad) / max(1e-9, max(ys) - min(ys))
        sc = min(sx, sy)
        ox = (w - (max(xs) - min(xs)) * sc) / 2
        oy = (h - (max(ys) - min(ys)) * sc) / 2
        c = [((x - min(xs)) * sc + ox, (y - min(ys)) * sc + oy) for x, y in zip(xs, ys)]
        d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in c)
        km = sum(a["dist"] for a in acts[i:j + 1]) / 1000
        (x0, y0), (x1, y1) = c[0], c[-1]
        return (f'<span class="h-sketch" aria-hidden="true"><svg viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
                f'<path class="hs-under" d="{d}"/><path class="hs-line" d="{d}" stroke="{color}" pathLength="1"/>'
                f'<circle cx="{x0:.1f}" cy="{y0:.1f}" r="3" class="hs-a"/><circle cx="{x1:.1f}" cy="{y1:.1f}" r="3.6" fill="{color}"/></svg>'
                f'<span class="hs-km">{B.fkm(km, lang)} km</span></span>')

    def mark(m):
        i, j = (int(x) for x in m.group(2).split(","))
        return f'{m.group(1)}{m.group(3)}{svg(i, j)}</h4>'
    return re.sub(r'(<h4[^>]*data-acts="(\d+,\d+)"[^>]*>)(.*?)</h4>', mark, body, flags=re.S)
