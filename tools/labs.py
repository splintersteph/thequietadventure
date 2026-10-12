"""Prototypes de design (« labs ») : pages cachées sous /labs/, non indexées.

Appelé par build.py à la fin de la construction. Rien ici n'est relié au reste du site.
"""
import json
import math
import os
import re

import sys

B = sys.modules['__main__'] if hasattr(sys.modules.get('__main__'), 'layout') else __import__('build')
from decor import CAT_FLAGS, flags_html, motif_svg, stamp_svg, trip_flags

esc = B.esc
LAB_SLUG = "de-la-slovenie-a-litalie-par-les-alpes"
LAB_DAYS = ["15828413341", "15842768797", "15853553871"]   # 16, 17, 18 septembre 2025
MOIS = ['JANV.', 'FÉVR.', 'MARS', 'AVR.', 'MAI', 'JUIN', 'JUIL.', 'AOÛT', 'SEPT.', 'OCT.', 'NOV.', 'DÉC.']
COUNTRY_NAMES = {
    "kr": ("Corée du Sud", "South Korea"), "jp": ("Japon", "Japan"), "hr": ("Croatie", "Croatia"), "si": ("Slovénie", "Slovenia"),
    "it": ("Italie", "Italy"), "ch": ("Suisse", "Switzerland"), "fr": ("France", "France"), "au": ("Australie", "Australia"),
    "cn": ("Chine", "China"), "id": ("Indonésie", "Indonesia"), "nz": ("Nouvelle-Zélande", "New Zealand"),
    "us": ("États-Unis", "United States"), "ca": ("Canada", "Canada"), "co": ("Colombie", "Colombia"),
    "lk": ("Sri Lanka", "Sri Lanka"), "ph": ("Philippines", "Philippines"), "me": ("Monténégro", "Montenegro"),
}
CAPITAL_CITY = {  # ville du tampon : là où le récit commence
    "kr": "Séoul", "jp": "Fukuoka", "hr": "Zagreb", "si": "Ljubljana", "it": "Udine", "ch": "Lucerne", "fr": "Marseille",
    "au": "Sydney", "cn": "Xi'an", "id": "Denpasar", "nz": "Auckland", "us": "Los Angeles", "ca": "Montréal",
    "co": "Bogotá", "lk": "Colombo", "ph": "Palawan", "me": "Kotor",
}


# ------------------------------------------------------------------ helpers
def rdp(pts, eps):
    """Douglas-Peucker sur des [lat, lng]."""
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy) or 1e-12
    dmax, idx = 0, 0
    for i in range(1, len(pts) - 1):
        p = pts[i]
        d = abs(dy * (p[0] - a[0]) - dx * (p[1] - a[1])) / n if n > 1e-12 else math.hypot(p[0] - a[0], p[1] - a[1])
        if d > dmax:
            dmax, idx = d, i
    if dmax > eps:
        return rdp(pts[:idx + 1], eps)[:-1] + rdp(pts[idx:], eps)
    return [a, b]


def lab_layout(path, title, content, head="", scripts="", body_class="", desc="Prototype de design"):
    page = B.layout("fr", path, title, desc, content, alt_path="/labs/", body_class=("labs " + body_class).strip())
    extra = (f'<meta name="robots" content="noindex,nofollow">\n<script>window.TQA_BASE="{B.BASE}";'
             f'try{{var th=localStorage.getItem("tqa-theme");if(th)document.documentElement.dataset.theme=th}}catch(e){{}}</script>\n'
             f'<link rel="stylesheet" href="/assets/labs/labs.css?v={B.VERSION}">\n{head}\n</head>')
    page = page.replace("</head>", extra, 1)
    page = page.replace("</body>", f'<script src="/assets/labs/labs.js?v={B.VERSION}" defer></script>\n{scripts}\n</body>', 1)
    B.write(path, page)


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


_TINY = {}


def tiny_uri(src):
    """Miniature de 24 px encodée dans la page : l'aperçu flou s'affiche sans aucune requête."""
    if src in _TINY:
        return _TINY[src]
    out = None
    local = os.path.join(B.ROOT, src.lstrip("/"))
    if src.startswith("/media/") and os.path.exists(local):
        try:
            import base64
            import io
            from PIL import Image
            im = Image.open(local).convert("RGB")
            im.thumbnail((24, 24))
            buf = io.BytesIO()
            im.save(buf, "JPEG", quality=60)
            out = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
        except Exception:
            out = None
    _TINY[src] = out
    return out


def lq_img(src, alt="", cls="", width=1400, caption="", extra=""):
    """Image avec aperçu flou (une miniature de 40 px) qui se révèle au chargement."""
    tiny = tiny_uri(src) or B.media(src, 40)
    full = B.media(src, width)
    big = B.media(src, 2200)
    cap = f' data-caption="{esc(caption)}"' if caption else ""
    return (f'<span class="lq {cls}" style="--lq:url(\'{esc(tiny)}\')"{extra}>'
            f'<img src="{esc(full)}" data-full="{esc(big)}" alt="{esc(alt)}" loading="lazy" decoding="async" data-lb{cap}></span>')


# ------------------------------------------------------------------ 1. accueil : le globe
def globe_data(trips, posts):
    chrono = sorted(trips, key=lambda t: t["start"])
    seen_c, n_posts, km_bike, out = set(), 0, 0.0, []
    for t in chrono:
        lines, dashed = [], False
        for a in t["acts"]:
            pts = rdp(B.decode_polyline(a["poly"]), 0.0012)
            lines.append([[round(p[1], 3), round(p[0], 3)] for p in pts])
            km_bike += a["dist"] / 1000
        if not lines:
            geo = [[round(p["geo"][1], 3), round(p["geo"][0], 3)] for p in t["posts"] if p.get("geo")]
            geo = [g for i, g in enumerate(geo) if i == 0 or g != geo[i - 1]]
            segs, cur = [], []
            for g in geo:
                if cur and math.hypot(g[0] - cur[-1][0], (g[1] - cur[-1][1])) > 9:
                    segs.append(cur)
                    cur = []
                cur.append(g)
            if cur:
                segs.append(cur)
            lines, dashed = [sg for sg in segs if len(sg) > 1], True
        for p in t["posts"]:
            seen_c.update(countries_of(p))
        n_posts += len(t["posts"])
        out.append({
            "slug": t["slug"], "title": t["title"]["fr"], "period": t["period"]["fr"], "color": t["color"],
            "mode": t.get("mode", "roadtrip"), "url": B.trip_url(t, "fr"), "year": t["start"].year,
            "flags": trip_flags(t, 18), "lines": lines, "dashed": dashed,
            "pins": [[round(p["geo"][1], 3), round(p["geo"][0], 3)] for p in t["posts"] if p.get("geo")],
            "km": round(km_bike), "countries": len(seen_c), "stories": n_posts,
        })
    return out


def page_globe(trips, posts):
    write_json("/labs/data/globe.json", globe_data(trips, posts))
    body = """<section class="gl" aria-label="Dix ans de voyages sur un globe">
<div class="gl-stage"><canvas class="gl-canvas" aria-hidden="true"></canvas>
<p class="gl-hint">Faites tourner le globe</p></div>
<div class="gl-side">
<p class="gl-year" aria-live="polite">2015</p>
<h1 class="gl-title">Dix ans de voyages, trace après trace.</h1>
<p class="gl-trip"><span class="gl-flags"></span><a class="gl-name" href="/voyages/">&nbsp;</a><span class="gl-period"></span></p>
<dl class="gl-count">
<div><dt>km à vélo et à pied</dt><dd data-k="km">0</dd></div>
<div><dt>pays</dt><dd data-k="countries">0</dd></div>
<div><dt>récits</dt><dd data-k="stories">0</dd></div>
</dl>
<ol class="gl-line" aria-label="Les voyages, dans l'ordre"></ol>
<div class="gl-ctrl"><button type="button" class="gl-play" aria-pressed="true">Pause</button><button type="button" class="gl-replay">Rejouer depuis 2015</button></div>
</div>
</section>
<section class="wrap gl-after"><p>Les voyages sans trace GPS (avant 2020) sont dessinés en pointillés, d'un récit à l'autre. Cliquez sur une année pour y revenir.</p></section>"""
    scripts = ('<script src="/assets/labs/vendor/d3-array.min.js"></script>\n<script src="/assets/labs/vendor/d3-geo.min.js"></script>\n'
               '<script src="/assets/labs/vendor/topojson-client.min.js"></script>\n<script src="/assets/labs/globe.js?v=' + B.VERSION + '" defer></script>')
    lab_layout("/labs/accueil/", "Prototype · accueil", body, scripts=scripts, body_class="labs-globe")


# ------------------------------------------------------------------ 2. le récit au fil de la route
CAPTIONS = {
    "e1e1d": "Kranjska Gora sous la pluie",
    "16864": "Au chaud, au chalet",
    "c0e14": "Les lacs de Kranjska Gora",
    "0992a": "La frontière italienne",
    "17d12": "La vallée après Tarvisio",
    "cc5b4": "Le gîte de Pontebba",
    "24337": "Sur l'Alpe-Adria",
    "38233": "La gare de Chiusaforte",
    "66a67": "Focaccias à Venzone",
}


def page_recit(posts):
    p = next(q for q in posts if q["slug"] == LAB_SLUG)
    trip = p["trip"]
    alt = json.load(open(os.path.join(B.ROOT, "data", "labs", "alpes-altitude.json")))
    days, start = [], 0.0
    for aid in LAB_DAYS:
        a = B.STRAVA[aid]
        pts = rdp(B.decode_polyline(a["poly"]), 0.00012)
        al = alt[aid]
        al = [sorted(al[max(0, i - 1):i + 2])[len(al[max(0, i - 1):i + 2]) // 2] for i in range(len(al))]  # médiane : enlève les pics GPS
        name = re.sub(r"[^\w\s\->'’]", "", a["name"]).replace("Kranksja", "Kranjska")
        frm, to = [s.strip() for s in name.split("->")]
        days.append({"id": aid, "line": pts, "alt": al, "km": a["dist"] / 1000, "start": start, "from": frm, "to": to,
                     "up": a["elev"], "down": round(max(0, al[0] - al[-1] + a["elev"]))})
        start += a["dist"] / 1000
    body = p["body"]
    intro_m = re.match(r"\s*<p><strong>(.*?)</strong></p>", body, re.S)
    intro = intro_m.group(1) if intro_m else ""
    body = body[intro_m.end():] if intro_m else body
    parts = re.split(r"<h4>(.*?)</h4>", body)
    openers = ["/media/2025/12/7f9b9-img-20250919-wa0022.jpg", "/media/2025/12/f3d8e-img-20250918-wa0001.jpg", "/media/2025/12/aa2ba-20250917_133439.jpg"]
    hand = ["Sous la pluie, 12 km de forêt", "On passe en Italie !", "La grande descente du Frioul"]
    sections = ""
    for i in range(1, len(parts), 2):
        d = (i - 1) // 2
        if d >= len(days):
            break
        day = days[d]
        blocks = ""
        for m in re.finditer(r"<p>.*?</p>|<div class=\"gallery[^\"]*\">.*?</div>|<figure>.*?</figure>", parts[i + 1], re.S):
            chunk = m.group(0)
            if chunk.startswith("<p"):
                blocks += f'<div class="lr-block">{chunk}</div>'
                continue
            srcs = re.findall(r'src="(/media/[^"]+)"', chunk)
            figs = ""
            for k, s in enumerate(srcs):
                key = s.split("/")[-1][:5]
                cap = CAPTIONS.get(key, "")
                note = f'<span class="lr-note" aria-hidden="true">{esc(cap)}<svg viewBox="0 0 60 40" width="60" height="40"><path d="M4 6 C 22 4, 40 12, 50 32 M42 26 L50 33 L54 23" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg></span>' if cap else ""
                figs += f'<figure class="lr-ph{" lead" if k == 0 else ""}">{lq_img(s, cap, width=1200 if k == 0 else 700, caption=cap)}{note}</figure>'
            blocks += f'<div class="lr-block lr-sheet n{min(len(srcs), 6)}">{figs}</div>'
        sections += f"""<section class="lr-open" data-day="{d}" style="--i:{d}">
<div class="lr-open-img">{lq_img(openers[d], "", width=2000)}</div>
<div class="lr-open-txt"><span class="lr-day">{esc(parts[i])}</span><h2>{esc(day['from'])} <span>→</span> {esc(day['to'])}</h2>
<p class="lr-hand">{esc(hand[d])}</p>
<dl><div><dt>distance</dt><dd>{B.fkm(day['km'])} km</dd></div><div><dt>montée</dt><dd>{round(day['up'])} m</dd></div><div><dt>descente</dt><dd>{day['down']} m</dd></div></dl></div>
</section>
<section class="lr-body" data-day="{d}">{blocks}</section>"""
    data = {"color": trip["color"], "days": days}
    total = days[-1]["start"] + days[-1]["km"]
    head = '<link rel="preconnect" href="https://unpkg.com">'
    html_ = f"""<div class="lr-top" aria-hidden="true"><svg class="lr-top-svg" preserveAspectRatio="none"></svg><span class="lr-top-bike">{motif_svg("velo", 22, "currentColor", 2.6)}</span></div>
<header class="lr-hero">
<div class="lr-hero-img" style="view-transition-name: cover-alpes">{lq_img(p["cover"], "", width=2200)}</div>
<div class="lr-hero-txt"><a class="lr-crumb" href="/labs/">← Les prototypes</a>
<p class="lr-kicker">{esc(trip['title']['fr'])} · étape {p['step']} sur {len(trip['posts'])}</p>
<h1>{esc(p['title'])}</h1>
<p class="lr-intro">{intro}</p>
<p class="lr-meta">{trip_flags(trip, 16)} <span>3 jours</span><span>{B.fkm(total)} km</span><span>16 – 18 septembre 2025</span></p>
<p class="lr-scroll">Faites défiler : la carte suit le récit</p></div>
</header>
<div class="lr-main">{sections}</div>
<aside class="lr-panel" aria-label="Où nous en sommes">
<div class="lr-map" id="lr-map"></div>
<div class="lr-now"><b class="lr-now-day">16 septembre</b><span class="lr-now-km">km 0</span><span class="lr-now-alt">639 m</span></div>
<svg class="lr-prof" viewBox="0 0 600 120" preserveAspectRatio="none" aria-hidden="true"></svg>
</aside>
<button class="lr-mapbtn" type="button" aria-expanded="false">{motif_svg("velo", 26, "currentColor", 2.4)}<span>La carte</span></button>
<section class="wrap lr-end"><a class="btn solid" href="/labs/">Revenir aux prototypes</a></section>
<script type="application/json" id="lr-data">{json.dumps(data, separators=(",", ":"))}</script>"""
    scripts = f'<script src="/assets/labs/recit.js?v={B.VERSION}" defer></script>'
    lab_layout("/labs/recit/", "Prototype · récit", html_, head=head, scripts=scripts, body_class="labs-recit")


# ------------------------------------------------------------------ 3. le passeport
def page_passport(trips, posts):
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
        url = B.trip_url(t, "fr") if t else "/voyages/"
        stamps += f"""<a class="ps-stamp {shapes[i % len(shapes)]}" href="{url}" style="--c:{color};--r:{rot}deg;--i:{i}">
<span class="ps-in">{motif_svg(mode, 30, "currentColor", 2.4)}<b>{esc(COUNTRY_NAMES[c][0])}</b><span class="ps-city">{esc(CAPITAL_CITY.get(c, ''))}</span>
<span class="ps-date">{e['first'].day} {MOIS[e['first'].month - 1]} {e['first'].year}</span><span class="ps-n">{e['n']} récit{'s' if e['n'] > 1 else ''}</span></span></a>"""
    total_stories = len(posts)
    body = f"""<section class="ps" aria-label="Le passeport des voyages">
<div class="ps-intro wrap"><h1>Le passeport</h1><p>Un tampon par pays traversé, à la date du premier récit écrit là-bas. Cliquez sur un tampon pour ouvrir le voyage.</p></div>
<div class="ps-book" data-open="false">
<button class="ps-cover" type="button" aria-label="Ouvrir le passeport">
<span class="ps-cv-top">Carnet de voyage</span>
<svg class="ps-emblem" viewBox="0 0 120 120" width="120" height="120" aria-hidden="true"><g fill="none" stroke="currentColor" stroke-width="2"><circle cx="60" cy="60" r="44"/><ellipse cx="60" cy="60" rx="18" ry="44"/><path d="M16 60h88M22 38h76M22 82h76"/></g></svg>
<span class="ps-cv-title">The Quiet Adventure</span><span class="ps-cv-sub">Passeport · 2015 – 2025</span><span class="ps-cv-open">Ouvrir</span></button>
<div class="ps-pages">
<div class="ps-id"><div class="ps-photo">{motif_svg("velo", 64, "currentColor", 2)}</div>
<dl><div><dt>Titulaires</dt><dd>Stéphane, Cassandre et Clémence</dd></div><div><dt>Moyen de transport</dt><dd>Deux vélos, une remorque, des trains</dd></div>
<div><dt>Premier départ</dt><dd>Sri Lanka, août 2015</dd></div><div><dt>Pays visités</dt><dd>{len(order)}</dd></div><div><dt>Récits</dt><dd>{total_stories}</dd></div></dl>
<p class="ps-mrz" aria-hidden="true">P&lt;FRATHE&lt;QUIET&lt;ADVENTURE&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;<br>2015&lt;&lt;{len(order):02d}PAYS&lt;&lt;{total_stories}RECITS&lt;&lt;A&lt;VELO&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;</p></div>
<div class="ps-visas"><h2>Visas</h2><div class="ps-grid">{stamps}</div></div>
</div></div></section>"""
    lab_layout("/labs/passeport/", "Prototype · passeport", body, scripts=f'<script src="/assets/labs/passeport.js?v={B.VERSION}" defer></script>', body_class="labs-passport")


# ------------------------------------------------------------------ 4. la recherche
def search_index(posts, lang):
    out = []
    for p in sorted(posts, key=lambda q: q["dt"], reverse=True):
        v = B.V(p, lang)
        t = p.get("trip")
        out.append({"t": v["title"], "u": v["url"], "d": B.fdate(p["dt"], lang), "y": p["dt"].year,
                    "j": t["title"][lang] if t else "", "c": B.media(p.get("cover"), 240) if p.get("cover") else "",
                    "f": flags_html(countries_of(p), 13), "x": B.text_of(v["body"])})
    return out


def page_search(posts):
    write_json("/labs/data/search-fr.json", search_index(posts, "fr"))
    write_json("/labs/data/search-en.json", search_index(posts, "en"))
    body = """<section class="wrap sr-page"><h1>Chercher dans dix ans de récits</h1>
<p class="sr-lead">Tapez un lieu, un mot, un souvenir. Les résultats s'affichent pendant la frappe, en français ou en anglais. Ailleurs dans les prototypes, la touche <kbd>/</kbd> ouvre la même recherche.</p>
<div class="sr-box" data-inline><label class="sr-field"><svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M15.5 15.5 21 21" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
<input type="search" placeholder="baleines, Lozère, crevaison, Kumamon…" aria-label="Rechercher un récit" autocomplete="off"></label>
<div class="sr-tags"><button type="button">baleines</button><button type="button">crevaison</button><button type="button">aire de jeux</button><button type="button">kangourou</button><button type="button">tunnel</button><button type="button">focaccia</button></div>
<ol class="sr-results" aria-live="polite"></ol></div></section>"""
    lab_layout("/labs/recherche/", "Prototype · recherche", body, body_class="labs-search")


# ------------------------------------------------------------------ 5. les cartes de partage
def page_share(posts):
    picks = [q for q in posts if q["slug"] in (LAB_SLUG, "les-derniers-kilometres-jusqua-sokcho", "la-via-allier-de-langogne-a-clermont-un-itineraire-loin-des-touristes")]
    cards = ""
    for p in picks:
        t = p["trip"]
        pts = [pt for a in p.get("acts", []) for pt in B.decode_polyline(a["poly"])]
        path = ""
        if pts:
            la = [q[0] for q in pts]
            ln = [q[1] for q in pts]
            k = math.cos(math.radians(sum(la) / len(la)))
            w, h = (max(ln) - min(ln)) * k or 1e-6, (max(la) - min(la)) or 1e-6
            s = 150 / max(w, h)
            ox, oy = (180 - w * s) / 2, (180 - h * s) / 2
            pp = rdp(pts, 0.0005)
            path = "M" + " L".join(f"{ox + (q[1] - min(ln)) * k * s:.1f} {oy + (max(la) - q[0]) * s:.1f}" for q in pp)
        km = B.act_totals(p.get("acts", []))[0]
        card = f"""<div class="og" style="--trip:{t['color']}">
<div class="og-img" style="background-image:url('{esc(B.media(p['cover'], 1200))}')"></div>
<div class="og-side"><span class="og-stamp">{stamp_svg(t, 'fr', 110)}</span>
<span class="og-kicker">{esc(t['title']['fr'])} · étape {p['step']}</span>
<span class="og-title">{esc(p['title'])}</span>
<span class="og-foot">{trip_flags(t, 18)}{f'<b>{B.fkm(km)} km</b>' if km else ''}<span>The Quiet Adventure</span></span>
{f'<svg class="og-trace" viewBox="0 0 180 180"><path d="{path}"/></svg>' if path else ''}</div></div>"""
        cards += f"""<figure class="sh-item"><div class="sh-chat"><div class="sh-msg me"><p>Regarde ce qu'on a fait en septembre !</p>
<a class="sh-link" href="{p['url']}"><span class="sh-scale">{card}</span><span class="sh-meta"><b>{esc(p['title'])}</b><span>thequietadventure.com</span></span></a></div></div>
<figcaption>Taille réelle (1200 × 630) : <button type="button" class="sh-zoom">agrandir</button></figcaption></figure>"""
    body = f"""<section class="wrap sh-page"><h1>Les aperçus de partage</h1>
<p class="sh-lead">Quand un récit est envoyé sur une messagerie ou un réseau social, c'est cette image qui s'affiche. Aujourd'hui, c'est la photo de couverture seule. Ici, chaque récit a sa carte : la photo, le tampon du voyage, la trace de l'étape et ses kilomètres. En production, elles seraient générées automatiquement à chaque publication.</p>
<div class="sh-grid">{cards}</div></section>"""
    lab_layout("/labs/partage/", "Prototype · partage", body, scripts=f'<script>document.addEventListener("click",function(e){{var b=e.target.closest(".sh-zoom");if(b)b.closest(".sh-item").classList.toggle("big")}})</script>', body_class="labs-share")


# ------------------------------------------------------------------ index
def page_index(posts):
    p = next(q for q in posts if q["slug"] == LAB_SLUG)
    items = [
        ("/labs/accueil/", "accueil", "Un globe pour la page d'accueil", "Dix ans de traces se dessinent dans l'ordre, voyage après voyage, pendant que les compteurs montent. On peut faire tourner le globe et revenir à une année."),
        ("/labs/recit/", "recit", "Un récit au fil de la route", "La carte suit la lecture : le vélo avance quand on fait défiler, le profil d'altitude montre la montée et la descente des Alpes. Photos en grand, notes manuscrites, visionneuse au doigt."),
        ("/labs/passeport/", "passeport", "Le passeport", "Un tampon par pays, à la date du premier récit. Le passeport s'ouvre et les visas se posent un par un."),
        ("/labs/recherche/", "recherche", "La recherche instantanée", "Les résultats arrivent pendant la frappe, dans les deux langues, avec le passage où le mot apparaît. Touche / sur toutes ces pages."),
        ("/labs/partage/", "partage", "Les aperçus de partage", "La vignette qui s'affiche quand on envoie un récit : photo, tampon, trace de l'étape."),
    ]
    cards = ""
    for i, (url, key, title, txt) in enumerate(items):
        vis = ""
        if key == "recit":
            vis = f'<span class="lx-img" style="view-transition-name: cover-alpes">{lq_img(p["cover"], "", width=900)}</span>'
        else:
            vis = f'<span class="lx-vis lx-{key}" aria-hidden="true"></span>'
        cards += f'<a class="lx-card" href="{url}">{vis}<span class="lx-n">{i + 1}</span><b>{esc(title)}</b><span>{esc(txt)}</span></a>'
    body = f"""<section class="wrap lx"><h1>Les prototypes</h1>
<p class="lx-lead">Des pistes pour le site, construites avec les vrais récits et les vraies traces. Ces pages ne sont reliées à rien et ne sont pas indexées. Deux réglages s'appliquent à toutes : le mode nuit (bouton en haut à droite) et les transitions entre pages (cliquez sur le récit des Alpes et regardez la photo).</p>
<div class="lx-grid">{cards}
<button class="lx-card lx-theme" type="button"><span class="lx-vis lx-nuit" aria-hidden="true"></span><span class="lx-n">6</span><b>Le mode nuit</b><span>Papier sombre, cartes nocturnes, photos légèrement adoucies. Cliquez pour basculer.</span></button>
<div class="lx-card lx-static"><span class="lx-vis lx-flou" aria-hidden="true"></span><span class="lx-n">7</span><b>Le chargement en douceur</b><span>Chaque photo apparaît d'abord floue (une miniature de quelques octets), puis nette, sans que la page saute. Visible sur le récit des Alpes, surtout en connexion lente.</span></div>
</div></section>"""
    lab_layout("/labs/", "Prototypes", body, body_class="labs-index")


def build(posts, trips, books):
    page_index(posts)
    page_globe(trips, posts)
    page_recit(posts)
    page_passport(trips, posts)
    page_search(posts)
    page_share(posts)
