#!/usr/bin/env python3
"""Build The Quiet Adventure into _site/ (pure Python, no dependencies).

    python3 tools/build.py            # build into _site/
    python3 tools/build.py --serve    # build, then serve on http://localhost:8000

Content lives in content/posts/*.html (JSON header + article HTML),
trips in data/trips.json, books in data/books.json.
"""
import datetime as dt
import glob
import html
import json
import math
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from decor import hero_decor, stamp_svg  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "_site")
SITE_URL = "https://thequietadventure.com"
BASE = os.environ.get("BASE_PATH", "").rstrip("/")  # "/thequietadventure" when served from github.io
WP_CDN = "https://i0.wp.com/thequietadventure.com/wp-content/uploads/"
WP_ORIGIN = "https://thequietadventure.com/wp-content/uploads/"
PALETTE = ["#A8641F", "#2F5D50", "#B5483B", "#3E6D8E", "#7A5C99", "#5E7F2E", "#C08A2E", "#8C4F6B", "#2E7F7A", "#6B6157"]

T = {
    "fr": {
        "tagline": "carnet de route",
        "nav_trips": "Voyages", "nav_map": "Carte", "nav_books": "Livres", "nav_about": "Qui sommes-nous", "nav_archive": "Archives",
        "menu": "Menu", "skip": "Aller au contenu",
        "hero_title": "Voyager lentement, en famille, au rythme des pédales.",
        "hero_lead": "Les récits de nos voyages, jour après jour : les routes à vélo, les trains attrapés de justesse, les aires de jeux trouvées pour Clémence et les gens rencontrés en chemin.",
        "read_latest": "Lire le dernier récit", "explore_map": "Explorer la carte",
        "latest_kicker": "Le dernier voyage", "whole_trip": "Tout le voyage →",
        "trips_kicker": "Les grands carnets", "trips_title": "Un voyage, un carnet. Chacun se lit comme un livre.",
        "also": "Et aussi :", "all_trips": "Tous les voyages",
        "books_kicker": "Nos livres", "books_title": "Chaque voyage devient un livre photo.",
        "books_aside": "Les récits du blog, remis en page avec les plus belles photos de chaque voyage.",
        "map_kicker": "La carte", "map_title": "Tous nos récits, là où ils se sont passés.",
        "map_aside": "Chaque point est un récit. Cliquez dessus pour l'ouvrir.",
        "stat_stories": "récits", "stat_countries": "pays", "stat_trips": "voyages racontés", "stat_years": "ans de carnets",
        "about_kicker": "Qui sommes-nous", "about_title": "Trois voyageurs, deux vélos, une remorque.",
        "about_short": "Stéphane écrit, Cassandre court et pédale, Clémence choisit les aires de jeux. Depuis 2015, nous racontons ici nos voyages : une année d'expatriation en Australie, des road trips, l'automne au Québec, puis, depuis la naissance de Clémence, des voyages à vélo, lentement.",
        "about_more": "Notre histoire →",
        "footer_follow": "Suivre nos récits", "footer_follow_txt": "Un nouveau récit à chaque étape. Abonnez-vous au flux RSS pour ne rien manquer.",
        "rss": "Flux RSS", "since": "Carnets de voyage depuis 2015",
        "stories": "récits", "story": "récit", "step": "Étape", "of": "sur",
        "trip_stories": "Les récits du voyage", "trip_map": "L'itinéraire",
        "the_trip": "Le voyage", "prev": "← Récit précédent", "next": "Récit suivant →",
        "strava_title": "Trace du jour", "strava_go": "Voir sur Strava →",
        "read_min": "min de lecture", "back_trips": "← Tous les voyages",
        "book_of_trip": "Le livre du voyage", "book_cta": "Découvrir le livre",
        "books_page_lead": "Après chaque voyage, nous reprenons les récits et les plus belles photos pour en faire un livre. [Indiquer ici comment se procurer les livres : PDF, impression, Amazon…]",
        "archive_title": "Tous les récits", "archive_lead": "Dix ans de carnets, du plus récent au plus ancien.",
        "map_page_title": "La carte de nos voyages",
        "trips_page_title": "Nos voyages", "trips_page_lead": "Les grands voyages à vélo, les road trips et les années d'expatriation, rangés par voyage plutôt que par pays.",
        "notfound_title": "Cette page s'est perdue en route.", "notfound_txt": "Elle a peut-être changé d'adresse avec le nouveau site.", "home": "Retour à l'accueil",
        "modes": {"velo": "À vélo", "train": "En train", "roadtrip": "Road trip", "expat": "Expatriation"},
        "lang_name": "Français",
    },
    "en": {
        "tagline": "travel journal",
        "nav_trips": "Journeys", "nav_map": "Map", "nav_books": "Books", "nav_about": "About us", "nav_archive": "Archive",
        "menu": "Menu", "skip": "Skip to content",
        "hero_title": "Travelling slowly, as a family, at the pace of the pedals.",
        "hero_lead": "Our travel stories, day after day: cycling routes, trains caught at the last second, playgrounds found for Clémence and the people we met along the way. The stories are written in French; journeys and books are introduced in English.",
        "read_latest": "Latest journey", "explore_map": "Explore the map",
        "latest_kicker": "Our latest journey", "whole_trip": "The whole journey →",
        "trips_kicker": "The big journeys", "trips_title": "One journey, one journal. Each reads like a book.",
        "also": "Also:", "all_trips": "All journeys",
        "books_kicker": "Our books", "books_title": "Every journey becomes a photo book.",
        "books_aside": "The blog stories, laid out again with the best photos of each trip.",
        "map_kicker": "The map", "map_title": "All our stories, where they happened.",
        "map_aside": "Each dot is a story. Click it to open it (in French).",
        "stat_stories": "stories", "stat_countries": "countries", "stat_trips": "journeys", "stat_years": "years of journals",
        "about_kicker": "About us", "about_title": "Three travellers, two bikes, one trailer.",
        "about_short": "Stéphane writes, Cassandre runs and rides, Clémence picks the playgrounds. Since 2015 we have been telling our travels here: a year as expats in Australia, road trips, autumn in Québec and, since Clémence was born, slow journeys by bike.",
        "about_more": "Our story →",
        "footer_follow": "Follow our stories", "footer_follow_txt": "A new story at every stage. Subscribe to the RSS feed so you don't miss one.",
        "rss": "RSS feed", "since": "Travel journals since 2015",
        "stories": "stories", "story": "story", "step": "Stage", "of": "of",
        "trip_stories": "Stories from this journey", "trip_map": "The route",
        "the_trip": "The journey", "prev": "← Previous", "next": "Next →",
        "strava_title": "Route of the day", "strava_go": "View on Strava →",
        "read_min": "min read", "back_trips": "← All journeys",
        "book_of_trip": "The book of the journey", "book_cta": "See the book",
        "books_page_lead": "After each journey we gather the stories and the best photos into a book. [Explain here how to get the books: PDF, print, Amazon…]",
        "archive_title": "All stories", "archive_lead": "Ten years of journals, newest first. Stories are in French.",
        "map_page_title": "The map of our travels",
        "trips_page_title": "Our journeys", "trips_page_lead": "Long bike journeys, road trips and years abroad, organised by journey rather than by country.",
        "notfound_title": "This page got lost on the way.", "notfound_txt": "It may have moved with the new site.", "home": "Back to the homepage",
        "modes": {"velo": "By bike", "train": "By train", "roadtrip": "Road trip", "expat": "Living abroad"},
        "lang_name": "English",
    },
}
MONTHS = {"fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"],
          "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]}
COUNTRY_CATS = {"australia", "china", "new-zealand", "usa", "canada", "japan", "indonesie", "philippines", "sri-lanka", "colombia",
                "south-korea", "croatie", "slovenie", "italie", "montenegro", "suisse", "france"}
REGIONS = {
    "coree-a-velo": ["asie"], "kyushu-a-velo": ["asie"], "japon-2018": ["asie"], "bali": ["asie"],
    "retour-en-europe-a-velo": ["europe"], "suisse-en-train": ["europe"],
    "belle-via-et-vercors": ["france"], "gorges-du-tarn-a-velo": ["france"], "passa-pais": ["france"],
    "toulouse-bordeaux-a-velo": ["france"], "echappees-a-velo-en-france": ["france"],
    "australie": ["oceanie"], "nouvelle-zelande": ["oceanie"],
    "ouest-americain": ["amerique"], "quebec": ["amerique"], "canada-2020": ["amerique"], "colombie": ["amerique"],
    "escapades": ["asie", "europe"],
}
REGION_NAMES = {
    "fr": {"france": "France", "europe": "Europe", "asie": "Asie", "oceanie": "Océanie", "amerique": "Amériques"},
    "en": {"france": "France", "europe": "Europe", "asie": "Asia", "oceanie": "Oceania", "amerique": "Americas"},
}
MODE_ORDER = ["velo", "train", "roadtrip", "expat"]
REGION_ORDER = ["france", "europe", "asie", "oceanie", "amerique"]
FILTER_TXT = {
    "fr": {"all": "Tous", "how": "Façon de voyager", "where": "Région", "none": "Aucun voyage ne correspond à ce filtre.", "count": "voyages"},
    "en": {"all": "All", "how": "How we travelled", "where": "Region", "none": "No journey matches this filter.", "count": "journeys"},
}
PATHS = {
    "fr": {"home": "/", "trips": "/voyages/", "map": "/carte/", "books": "/livres/", "about": "/a-propos/", "archive": "/archives/"},
    "en": {"home": "/en/", "trips": "/en/journeys/", "map": "/en/map/", "books": "/en/books/", "about": "/en/about/", "archive": "/en/archive/"},
}

esc = lambda s: html.escape(s or "", quote=True)


# ------------------------------------------------------------------ data
def media(src, width=1400):
    """Local file if fetched into media/, otherwise the WordPress CDN copy."""
    if not src:
        return ""
    if src.startswith("/media/"):
        rel = src[len("/media/"):]
        if os.path.exists(os.path.join(ROOT, "media", rel)):
            return src
        if rel.lower().endswith((".mp4", ".mov", ".webm")):
            return WP_ORIGIN + rel
        return f"{WP_CDN}{rel}?w={width}&quality=80&strip=info"
    return src


def text_of(body):
    t = re.sub(r"<[^>]+>", " ", body)
    return html.unescape(re.sub(r"\s+", " ", t)).strip()


def excerpt(body, n=30):
    paras = re.findall(r"<p>(.*?)</p>", body, re.S)
    words = text_of(" ".join(paras) if paras else body).split(" ")
    return " ".join(words[:n]) + ("…" if len(words) > n else "")


def load_posts():
    posts = []
    for f in sorted(glob.glob(os.path.join(ROOT, "content", "posts", "*.html"))):
        raw = open(f, encoding="utf-8").read()
        m = re.match(r"\s*<!--\s*(\{.*?\})\s*-->\s*", raw, re.S)
        if not m:
            print("En-tête manquant :", f)
            continue
        h = json.loads(m.group(1))
        h["body"] = raw[m.end():]
        h["dt"] = dt.datetime.fromisoformat(h["date"])
        h["words"] = len(text_of(h["body"]).split())
        h["excerpt"] = excerpt(h["body"])
        posts.append(h)
    posts.sort(key=lambda p: p["dt"])
    return posts


def matches(post, rule):
    d = post["date"][:10]
    if rule.get("from") and d < rule["from"]:
        return False
    if rule.get("to") and d > rule["to"]:
        return False
    if any(c in post["categories"] for c in rule.get("notcategories", [])):
        return False
    return any(c in post["categories"] for c in rule.get("categories", []))


def assign_trips(posts, trips):
    for t in trips:
        t["posts"] = []
    leftovers = []
    for p in posts:
        for t in trips:
            if matches(p, t["match"]):
                t["posts"].append(p)
                p["trip"] = t
                break
        else:
            leftovers.append(p)
            p["trip"] = None
    for t in trips:
        for i, p in enumerate(t["posts"]):
            p["step"] = i + 1
        if not t.get("cover") and t["posts"]:
            covers = [p["cover"] for p in t["posts"] if p.get("cover")]
            t["cover"] = covers[len(covers) // 2] if covers else None
        t["start"] = t["posts"][0]["dt"] if t["posts"] else None
        t["end"] = t["posts"][-1]["dt"] if t["posts"] else None
    for i, t in enumerate(trips):
        t["color"] = PALETTE[i % len(PALETTE)]
    return [t for t in trips if t["posts"]], leftovers


def decode_polyline(s):
    pts, i, lat, lng = [], 0, 0, 0
    while i < len(s):
        for k in (0, 1):
            r = sh = 0
            while True:
                b = ord(s[i]) - 63
                i += 1
                r |= (b & 31) << sh
                sh += 5
                if b < 32:
                    break
            d = ~(r >> 1) if r & 1 else r >> 1
            if k == 0:
                lat += d
            else:
                lng += d
        pts.append([round(lat / 1e5, 5), round(lng / 1e5, 5)])
    return pts


def trip_lines(t):
    """Real GPS traces if data/traces/<name>.json exists, else a dashed line through the stories."""
    name = t.get("traces")
    path = os.path.join(ROOT, "data", "traces", f"{name}.json") if name else None
    if path and os.path.exists(path):
        lines = []
        for _a, _b, poly in json.load(open(path, encoding="utf-8")):
            pts = decode_polyline(poly)[::2]
            lines.append({"points": pts, "color": t["color"], "weight": 3.5})
        return lines
    pts = [p["geo"] for p in t["posts"] if p.get("geo")]
    if len(pts) > 1:
        return [{"points": pts, "color": t["color"], "weight": 2, "dash": "4 7"}]
    return []


# ------------------------------------------------------------------ helpers
def fdate(d, lang, day=True):
    m = MONTHS[lang][d.month - 1]
    if lang == "fr":
        return f"{d.day if d.day > 1 else '1er'} {m} {d.year}" if day else f"{m} {d.year}"
    return f"{m} {d.day}, {d.year}" if day else f"{m} {d.year}"


def trip_url(t, lang):
    return f"/voyages/{t['slug']}/" if lang == "fr" else f"/en/journeys/{t['en_slug']}/"


def img(src, alt, cls="ph", width=1000, extra=""):
    return f'<img class="{cls}" src="{esc(media(src, width))}" alt="{esc(alt)}" loading="lazy" decoding="async"{extra}>'


def map_div(data, cls="map", label=""):
    return f'<div class="{cls}" data-map="{esc(json.dumps(data, ensure_ascii=False, separators=(",", ":")))}" role="region" aria-label="{esc(label)}"></div>'


def layout(lang, path, title, desc, content, alt_path=None, image=None, active=None, body_class=""):
    t = T[lang]
    P = PATHS[lang]
    other = "en" if lang == "fr" else "fr"
    alt_path = alt_path or PATHS[other]["home"]
    full_title = f"{title} — The Quiet Adventure" if title else "The Quiet Adventure"
    og = SITE_URL + media(image or "/assets/img/home/hero.jpg", 1200) if (image or "/").startswith("/") else media(image, 1200)
    if og.startswith(SITE_URL + "http"):
        og = og[len(SITE_URL):]

    def nav_link(key, label):
        cur = ' aria-current="page"' if active == key else ""
        return f'<a href="{P[key]}"{cur}>{label}</a>'

    if lang == "fr":
        switch = f'<span class="on" aria-current="true">FR</span><a href="{alt_path}" hreflang="en" lang="en">EN</a>'
    else:
        switch = f'<a href="{alt_path}" hreflang="fr" lang="fr">FR</a><span class="on" aria-current="true">EN</span>'
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{SITE_URL}{path}">
<link rel="alternate" hreflang="{lang}" href="{SITE_URL}{path}">
<link rel="alternate" hreflang="{other}" href="{SITE_URL}{alt_path}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="The Quiet Adventure">
<meta property="og:title" content="{esc(title or 'The Quiet Adventure')}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{SITE_URL}{path}">
<meta property="og:image" content="{esc(og)}">
<meta property="og:locale" content="{'fr_FR' if lang == 'fr' else 'en_GB'}">
<meta name="twitter:card" content="summary_large_image">
<link rel="alternate" type="application/rss+xml" title="The Quiet Adventure" href="/feed.xml">
<link rel="icon" href="/assets/img/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Caveat:wght@500;700&family=Karla:wght@400;500;700&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,600;1,6..72,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/css/site.css?v={VERSION}">
</head>
<body class="{body_class}">
<a class="skip" href="#main">{t['skip']}</a>
<header class="site-header">
<div class="wrap">
<a class="brand" href="{P['home']}"><b>The Quiet Adventure</b><span>{t['tagline']}</span></a>
<button class="menu-btn" type="button" aria-expanded="false" aria-controls="nav">{t['menu']}</button>
<nav id="nav" class="nav" aria-label="Navigation principale">
<div class="dd">{nav_link('trips', t['nav_trips'])}<div class="dd-menu">
{''.join(f'<a href="{P["trips"]}#{m}">{t["modes"][m]}</a>' for m in MODE_ORDER)}<hr>
{''.join(f'<a href="{P["trips"]}#{r}">{REGION_NAMES[lang][r]}</a>' for r in REGION_ORDER)}</div></div>
{nav_link('map', t['nav_map'])}
{nav_link('books', t['nav_books'])}
{nav_link('about', t['nav_about'])}
<div class="lang" role="group" aria-label="Langue / Language">{switch}</div>
</nav>
</div>
</header>
<main id="main">
{content}
</main>
<footer class="site-footer">
<div class="wrap">
<div class="top">
<div><b>{t['footer_follow']}</b><p>{t['footer_follow_txt']}</p></div>
<div class="links"><a href="/feed.xml">{t['rss']}</a><a href="{P['archive']}">{t['nav_archive']}</a><a href="{P['trips']}">{t['nav_trips']}</a><a href="{P['books']}">{t['nav_books']}</a></div>
</div>
<div class="bottom"><span>The Quiet Adventure — {t['since']}</span><span><a href="{PATHS['fr']['home']}" lang="fr">Français</a> · <a href="{PATHS['en']['home']}" lang="en">English</a></span></div>
</div>
</footer>
<script src="/assets/js/site.js?v={VERSION}" defer></script>
</body>
</html>
"""


def asset_version():
    import hashlib
    h = hashlib.md5()
    for f in ("assets/css/site.css", "assets/js/site.js"):
        h.update(open(os.path.join(ROOT, f), "rb").read())
    return h.hexdigest()[:8]


VERSION = asset_version()


def with_base(content):
    if not BASE:
        return content
    content = re.sub(r'((?:href|src|action)=")/(?!/)', lambda m: m.group(1) + BASE + "/", content)
    return re.sub(r'(&quot;url&quot;:&quot;)/(?!/)', lambda m: m.group(1) + BASE + "/", content)


def write(path, content):
    content = with_base(content)
    p = path.lstrip("/")
    if p.endswith("/") or p == "":
        p = p + "index.html"
    full = os.path.join(OUT, p)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)


def redirect(path, target):
    write(path, f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>The Quiet Adventure</title>
<link rel="canonical" href="{SITE_URL}{target}"><meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0; url={BASE}{target}"></head>
<body><p><a href="{target}">{target}</a></p></body></html>""")


# ------------------------------------------------------------------ components
def trip_card(t, lang):
    n = len(t["posts"])
    lbl = f"{t['period'][lang]} · {T[lang]['modes'][t['mode']].lower()}"
    cats = " ".join([t["mode"]] + REGIONS.get(t["slug"], []))
    return f"""<a class="card" href="{trip_url(t, lang)}" data-cats="{cats}">
<div class="card-media">{img(t.get('cover'), t['title'][lang], width=900)}<span class="card-stamp">{stamp_svg(t, lang, 84)}</span></div>
<div class="body"><span class="label ochre">{esc(lbl)}</span><h3>{esc(t['title'][lang])}</h3>
<p>{esc(t['lead'][lang])}</p><span class="label">{n} {T[lang]['stories'] if n > 1 else T[lang]['story']}</span></div></a>"""


def story_card(p, lang="fr"):
    t = p.get("trip")
    lbl = fdate(p["dt"], lang)
    if t:
        lbl = f"{T[lang]['step']} {p['step']} · {lbl}"
    note = ' <span class="lang-note" lang="en">FR</span>' if lang == "en" else ""
    return f"""<a class="story" href="{p['url']}" lang="fr">
{img(p.get('cover'), p['title'], width=900)}
<span class="label">{esc(lbl)}</span><h3>{esc(p['title'])}{note}</h3><p>{esc(p['excerpt'])}</p></a>"""


def book_card(b, lang):
    href = f"{PATHS[lang]['books']}#{b['id']}"
    return f"""<a class="book" href="{href}">
<img src="{b['cover']}" alt="{esc(('Couverture du livre ' if lang == 'fr' else 'Cover of the book ') + b['title'][lang])}" loading="lazy">
<h3>{esc(b['title'][lang])} <small>· {esc(b['detail'][lang])}</small></h3></a>"""


def all_points(trips, lang):
    pts = []
    for t in trips:
        for p in t["posts"]:
            if p.get("geo"):
                pts.append({"lat": p["geo"][0], "lng": p["geo"][1], "title": p["title"], "url": p["url"],
                            "label": t["title"][lang], "color": t["color"], "r": 6})
    return pts


def stats(posts, trips):
    countries = set()
    for p in posts:
        countries |= COUNTRY_CATS & set(p["categories"])
    years = posts[-1]["dt"].year - posts[0]["dt"].year
    return {"stories": len(posts), "countries": len(countries), "trips": len(trips), "years": years}


# ------------------------------------------------------------------ pages
def page_home(lang, posts, trips, books):
    t = T[lang]
    P = PATHS[lang]
    latest_trip = max(trips, key=lambda x: x["end"])
    latest = latest_trip["posts"][-3:][::-1]
    featured = [x for x in trips if x.get("featured")]
    others = [x for x in trips if not x.get("featured")]
    st = stats(posts, trips)
    first_url = latest[0]["url"] if lang == "fr" else trip_url(latest_trip, lang)
    avignon = next((b for b in books if b["id"] == "avignon"), None)
    av_card = ""
    if avignon:
        av_card = f"""<a class="card" href="{P['books']}#avignon">
<img class="ph" src="/assets/img/trips/avignon.jpg" alt="{esc('Sentier dans la garrigue provençale' if lang == 'fr' else 'Trail through the Provençal scrubland')}" loading="lazy">
<div class="body"><span class="label ochre">2023 – 2025 · {'à la maison' if lang == 'fr' else 'at home'}</span><h3>{esc(avignon['title'][lang])}</h3>
<p>{esc(avignon['tagline'][lang])}</p><span class="label">{'Livre photo' if lang == 'fr' else 'Photo book'}</span></div></a>"""
    also = " · ".join(f'<a href="{trip_url(x, lang)}">{esc(x["title"][lang])}</a>' for x in others)
    body = f"""
<section class="hero"><div class="wrap grid2">
<div class="txt">
<p class="kicker">{esc(fdate(latest_trip['end'], lang, False).capitalize())} — {esc(latest_trip['title'][lang])}</p>
<h1>{t['hero_title']}</h1>
<p class="lead">{t['hero_lead']}</p>
<div class="actions"><a class="btn solid" href="{first_url}">{t['read_latest']}</a><a class="btn" href="{P['map']}">{t['explore_map']}</a></div>
</div>
<figure class="polaroid" style="margin:0"><div class="frame">
<img src="/assets/img/home/hero.jpg" alt="{esc('Clémence, chapeau orange et doudou, regarde par la fenêtre du train au retour de Venise' if lang == 'fr' else 'Clémence, in an orange hat with her cuddly toy, looks out of the train window on the way back from Venice')}">
<figcaption>{'Venise, 21 septembre 2025' if lang == 'fr' else 'Venice, 21 September 2025'}</figcaption></div>
<span class="tape" aria-hidden="true"></span>
<span class="stamp" aria-hidden="true"><b>{st['countries']}</b><span>{'pays' if lang == 'fr' else 'countries'}</span></span>
</figure>
</div></section>

<section class="section band"><div class="wrap">
<div class="sec-head"><div><p class="kicker">{t['latest_kicker']}</p><h2 class="h-sec">{esc(latest_trip['title'][lang])}</h2></div>
<a href="{trip_url(latest_trip, lang)}" style="font-weight:700">{t['whole_trip']}</a></div>
<div class="grid3">{''.join(story_card(p, lang) for p in latest)}</div>
</div></section>

<section class="section" id="voyages"><div class="wrap">
<div class="sec-head"><div><p class="kicker">{t['trips_kicker']}</p><h2 class="h-sec">{t['trips_title']}</h2></div>
<a href="{P['trips']}" style="font-weight:700">{t['all_trips']} →</a></div>
<div class="grid3">{''.join(trip_card(x, lang) for x in featured)}{av_card}</div>
<p class="also">{t['also']} {also}</p>
</div></section>

<section class="section band" id="livres"><div class="wrap">
<div class="sec-head"><div><p class="kicker">{t['books_kicker']}</p><h2 class="h-sec">{t['books_title']}</h2></div><p class="aside">{t['books_aside']}</p></div>
<div class="grid3">{''.join(book_card(b, lang) for b in books)}</div>
</div></section>

<section class="section forest" id="carte"><div class="wrap">
<div class="sec-head"><div><p class="kicker">{t['map_kicker']}</p><h2 class="h-sec">{t['map_title']}</h2></div><p class="aside" style="color:var(--on-forest-soft)">{t['map_aside']}</p></div>
{map_div({"points": all_points(trips, lang)}, "map", t['map_title'])}
<div class="stats">
<div><b>{st['stories']}</b><span>{t['stat_stories']}</span></div>
<div><b>{st['countries']}</b><span>{t['stat_countries']}</span></div>
<div><b>{st['trips']}</b><span>{t['stat_trips']}</span></div>
<div><b>{st['years']}</b><span>{t['stat_years']}</span></div>
</div>
</div></section>

<section class="section" id="nous"><div class="wrap grid2">
<figure class="polaroid tilt-r" style="margin:0"><div class="frame">
<img src="/assets/img/home/velos.jpg" alt="{esc('Nos deux vélos chargés et la remorque de Clémence, face aux montagnes' if lang == 'fr' else 'Our two loaded bikes and Clémence’s trailer, facing the mountains')}" loading="lazy">
<figcaption>{'Les deux vélos et la remorque' if lang == 'fr' else 'Two bikes and a trailer'}</figcaption></div></figure>
<div class="txt" style="display:flex;flex-direction:column;gap:18px">
<p class="kicker">{t['about_kicker']}</p><h2 class="h-sec">{t['about_title']}</h2>
<p style="margin:0;font-size:18px;color:var(--ink-soft)">{t['about_short']}</p>
<a href="{P['about']}" style="font-weight:700">{t['about_more']}</a>
</div>
</div></section>
"""
    desc = t["hero_lead"]
    write(P["home"], layout(lang, P["home"], "", desc, body, alt_path=PATHS["en" if lang == "fr" else "fr"]["home"]))


def page_trips(lang, trips):
    t = T[lang]
    P = PATHS[lang]
    ft = FILTER_TXT[lang]
    ordered = sorted(trips, key=lambda x: x["end"], reverse=True)
    modes = [m for m in MODE_ORDER if any(x["mode"] == m for x in trips)]

    def chip(key, label, n):
        return f'<button type="button" class="chip" data-filter="{key}" aria-pressed="false">{esc(label)} <small>{n}</small></button>'
    how = "".join(chip(m, t["modes"][m], sum(x["mode"] == m for x in trips)) for m in modes)
    where = "".join(chip(r, REGION_NAMES[lang][r], sum(r in REGIONS.get(x["slug"], []) for x in trips)) for r in REGION_ORDER)
    bar = f"""<div class="filters" role="group" aria-label="{esc(ft['how'])} / {esc(ft['where'])}">
<button type="button" class="chip" data-filter="" aria-pressed="true">{ft['all']} <small>{len(trips)}</small></button>
<span class="fgroup"><span class="label">{ft['how']}</span>{how}</span>
<span class="fgroup"><span class="label">{ft['where']}</span>{where}</span></div>"""
    body = f"""<section class="wrap post-head"><p class="kicker">{t['trips_kicker']}</p><h1>{t['trips_page_title']}</h1>
<p style="margin:0;font-size:19px;color:var(--ink-soft);max-width:680px">{t['trips_page_lead']}</p></section>
<section class="section" style="padding-top:8px"><div class="wrap">{bar}
<p class="filter-count label" aria-live="polite" data-word="{ft['count']}"></p>
<div class="grid3" id="trip-grid">{''.join(trip_card(x, lang) for x in ordered)}</div>
<p class="filter-empty" hidden>{ft['none']}</p></div></section>"""
    other = PATHS["en" if lang == "fr" else "fr"]["trips"]
    write(P["trips"], layout(lang, P["trips"], t["trips_page_title"], t["trips_page_lead"], body, other, active="trips"))


def page_trip(lang, trip, books):
    t = T[lang]
    url = trip_url(trip, lang)
    other_url = trip_url(trip, "en" if lang == "fr" else "fr")
    n = len(trip["posts"])
    items = ""
    month = None
    for p in trip["posts"]:
        note = ' <span class="lang-note">FR</span>' if lang == "en" else ""
        m = (p["dt"].year, p["dt"].month)
        if m != month:
            month = m
            items += f'<li class="route-month"><span>{esc(fdate(p["dt"], lang, False))}</span></li>'
        side = "l" if p["step"] % 2 else "r"
        items += f"""<li class="leg {side}"><span class="pin" aria-hidden="true">{p['step']}</span>
<a class="leg-card" href="{p['url']}" lang="fr"><figure class="snap">{img(p.get('cover'), p['title'], cls='', width=900)}
<figcaption>{esc(fdate(p['dt'], lang))}</figcaption></figure>
<div class="leg-txt"><span class="label ochre">{t['step']} {p['step']} {t['of']} {n}</span><h3>{esc(p['title'])}{note}</h3><p>{esc(p['excerpt'])}</p>
<span class="go">{'Lire le récit →' if lang == 'fr' else 'Read the story (in French) →'}</span></div></a></li>"""
    pts = [{"lat": p["geo"][0], "lng": p["geo"][1], "title": p["title"], "url": p["url"],
            "label": f"{t['step']} {p['step']}", "color": trip["color"]} for p in trip["posts"] if p.get("geo")]
    map_sec = ""
    if pts:
        map_sec = f"""<section class="section band" style="padding:64px 0"><div class="wrap">
<div class="sec-head"><div><p class="kicker">{t['trip_map']}</p></div></div>
{map_div({"points": pts, "lines": trip_lines(trip)}, "map", t['trip_map'])}</div></section>"""
    book = next((b for b in books if b["id"] == trip.get("book")), None)
    book_sec = ""
    if book:
        book_sec = f"""<section class="section"><div class="wrap book-strip">
<img src="{book['cover']}" alt="{esc(('Couverture du livre ' if lang == 'fr' else 'Cover of the book ') + book['title'][lang])}" loading="lazy">
<div style="display:flex;flex-direction:column;gap:16px"><p class="kicker">{t['book_of_trip']}</p><h2 class="h-sec">{esc(book['title'][lang])}</h2>
<p style="margin:0;color:var(--ink-soft);font-size:18px">{esc(book['tagline'][lang])} {esc(book['detail'][lang])}.</p>
<div class="actions"><a class="btn" href="{PATHS[lang]['books']}#{book['id']}">{t['book_cta']}</a></div></div></div></section>"""
    body = f"""<section class="trip-hero">{img(trip.get('cover'), trip['title'][lang], cls='', width=1800, extra=' fetchpriority="high"')}{hero_decor(trip, lang)}
<div class="wrap"><a class="crumbs" href="{PATHS[lang]['trips']}">{t['back_trips']}</a>
<p class="kicker" style="margin-top:18px">{esc(trip['period'][lang])}</p><h1>{esc(trip['title'][lang])}</h1><p>{esc(trip['lead'][lang])}</p>
<div class="chips"><span>{t['modes'][trip['mode']]}</span><span>{n} {t['stories'] if n > 1 else t['story']}</span></div></div></section>
{map_sec}
<section class="section"><div class="wrap"><div class="sec-head"><div><p class="kicker">{t['trip_stories']}</p></div></div>
<ol class="route" style="--trip:{trip['color']}">{items}<li class="route-end" aria-hidden="true"><span>{'Fin du voyage' if lang == 'fr' else 'The end'}</span></li></ol></div></section>
{book_sec}"""
    write(url, layout(lang, url, trip["title"][lang], trip["lead"][lang], body, other_url, image=trip.get("cover"), active="trips"))


STRAVA_ICON = '<svg class="ic" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#2F5D50" stroke-width="1.6" aria-hidden="true"><circle cx="6" cy="17" r="3.5"/><circle cx="18" cy="17" r="3.5"/><path d="M6 17l4-8h5l3 8M10 9l-1.5-3H6M15 9l-2 8"/></svg>'


URL_BY_SLUG = {}


def render_body(body, lang="fr"):
    t = T[lang]

    def fix_link(m):
        url = m.group(2)
        mm = re.match(r"^/\d{4}/\d{2}/\d{2}/([^/]+)/?$", url)
        if mm and mm.group(1) in URL_BY_SLUG:
            url = URL_BY_SLUG[mm.group(1)]
        return m.group(1) + url + m.group(3)
    body = re.sub(r'(<a[^>]*?\shref=")(/\d{4}/[^"]+)(")', fix_link, body)

    def strava(m):
        aid = m.group(1)
        return (f'<a class="strava-card" href="https://www.strava.com/activities/{aid}" rel="noopener">'
                f'<span class="t">{STRAVA_ICON}<b>{t["strava_title"]}</b></span><span class="go">{t["strava_go"]}</span></a>')
    body = re.sub(r'<div class="strava" data-activity="(\d+)"></div>', strava, body)
    body = re.sub(r'(<(?:img|video)[^>]*?\ssrc=")(/media/[^"]+)(")', lambda m: m.group(1) + esc(media(m.group(2))) + m.group(3), body)
    body = re.sub(r'(<a[^>]*?\shref=")(/media/[^"]+)(")', lambda m: m.group(1) + esc(media(m.group(2), 2000)) + m.group(3), body)
    return body


def page_post(p, posts_by_trip):
    lang = "fr"
    t = T[lang]
    trip = p.get("trip")
    mins = max(1, round(p["words"] / 230))
    chips = f"<span>{esc(fdate(p['dt'], lang))}</span><span>{mins} {t['read_min']}</span>"
    crumbs = ""
    aside = ""
    nav = ""
    if trip:
        tp = trip["posts"]
        i = p["step"] - 1
        crumbs = f'<a class="crumbs" href="{trip_url(trip, lang)}">← {esc(trip["title"][lang])} · {t["step"].lower()} {p["step"]} {t["of"]} {len(tp)}</a>'
        chips = f"<span>{esc(trip['title'][lang])}</span>" + chips
        lis = "".join(
            f'<a href="{q["url"]}"{" aria-current=\"page\" style=\"font-weight:700;color:var(--ink)\"" if q is p else ""}>{q["step"]}. {esc(q["title"])}</a>'
            for q in tp) if len(tp) <= 40 else ""
        mini = ""
        if p.get("geo"):
            pts = [{"lat": q["geo"][0], "lng": q["geo"][1], "title": q["title"], "url": q["url"], "color": trip["color"] if q is not p else "#B5483B",
                    "r": 5 if q is not p else 8} for q in tp if q.get("geo")]
            mini = map_div({"points": pts, "lines": trip_lines(trip)}, "map", t["trip_map"]).replace('class="map"', 'class="map" style="aspect-ratio:auto;height:240px;min-height:0"')
        aside = f"""<aside class="post-aside"><div class="aside-card"><span class="aside-stamp">{stamp_svg(trip, lang, 96)}</span><span class="kicker">{t['the_trip']}</span>
<a href="{trip_url(trip, lang)}" style="font-family:var(--serif);font-size:22px;text-decoration:none;color:var(--ink)">{esc(trip['title'][lang])}</a>
<span class="label">{esc(trip['period'][lang])}</span>{mini}<nav aria-label="{esc(t['trip_stories'])}">{lis}</nav></div></aside>"""
        prev_p = tp[i - 1] if i > 0 else None
        next_p = tp[i + 1] if i + 1 < len(tp) else None
        nav = '<nav class="post-nav" aria-label="Récits">'
        if prev_p:
            nav += f'<a class="prev" href="{prev_p["url"]}"><span class="label">{t["prev"]}</span><b>{esc(prev_p["title"])}</b></a>'
        if next_p:
            nav += f'<a class="next" href="{next_p["url"]}"><span class="label">{t["next"]}</span><b>{esc(next_p["title"])}</b></a>'
        nav += "</nav>"
    cover = ""
    if p.get("cover"):
        cover = f'<div class="wrap post-cover">{img(p["cover"], p["title"], cls="", width=1800, extra=" fetchpriority=\"high\"")}</div>'
    body = f"""<section class="wrap post-head">{crumbs}<h1>{esc(p['title'])}</h1><div class="meta">{chips}</div></section>
{cover}
<div class="wrap post-wrap">{aside}<article class="prose">{render_body(p['body'])}{nav}</article></div>"""
    alt = trip_url(trip, "en") if trip else PATHS["en"]["home"]
    write(p["url"], layout(lang, p["url"], p["title"], p.get("description") or p["excerpt"], body, alt, image=p.get("cover"), active="trips"))


def page_map(lang, trips):
    t = T[lang]
    P = PATHS[lang]
    lines = []
    for x in trips:
        lines += trip_lines(x)
    legend = "".join(f'<a href="{trip_url(x, lang)}" style="color:var(--ink);text-decoration:none"><i style="background:{x["color"]}"></i>{esc(x["title"][lang])}</a>' for x in trips)
    body = f"""<section class="wrap post-head"><p class="kicker">{t['map_kicker']}</p><h1>{t['map_page_title']}</h1>
<p style="margin:0;font-size:19px;color:var(--ink-soft)">{t['map_aside']}</p></section>
<div class="wrap">{map_div({"points": all_points(trips, lang), "lines": lines}, "map tall", t['map_page_title'])}
<div class="map-legend">{legend}</div></div><div style="height:96px"></div>"""
    other = PATHS["en" if lang == "fr" else "fr"]["map"]
    write(P["map"], layout(lang, P["map"], t["map_page_title"], t["map_title"], body, other, active="map"))


def page_books(lang, books, trips):
    t = T[lang]
    P = PATHS[lang]
    by_slug = {x["slug"]: x for x in trips}
    rows = ""
    for b in books:
        tr = by_slug.get(b.get("trip") or "")
        link = f'<a href="{trip_url(tr, lang)}" style="font-weight:700">{"Lire les récits du voyage →" if lang == "fr" else "Read the stories →"}</a>' if tr else ""
        rows += f"""<section class="section" id="{b['id']}" style="padding:48px 0;border-top:1px solid var(--line)"><div class="wrap book-strip">
<img src="{b['cover']}" alt="{esc(('Couverture du livre ' if lang == 'fr' else 'Cover of the book ') + b['title'][lang])}" loading="lazy">
<div style="display:flex;flex-direction:column;gap:14px"><h2 class="h-sec">{esc(b['title'][lang])}</h2>
<p style="margin:0;font-size:18px;color:var(--ink-soft)">{esc(b['tagline'][lang])}</p><span class="label">{esc(b['detail'][lang])}</span>{link}</div></div></section>"""
    body = f"""<section class="wrap post-head"><p class="kicker">{t['books_kicker']}</p><h1>{t['books_title']}</h1>
<p style="margin:0;font-size:19px;color:var(--ink-soft);max-width:720px">{t['books_page_lead']}</p></section>{rows}<div style="height:64px"></div>"""
    other = PATHS["en" if lang == "fr" else "fr"]["books"]
    write(P["books"], layout(lang, P["books"], t["books_title"], t["books_aside"], body, other, image="/assets/img/books/kyushu.jpg", active="books"))


def page_archive(lang, posts):
    t = T[lang]
    P = PATHS[lang]
    years = {}
    for p in sorted(posts, key=lambda p: p["dt"], reverse=True):
        years.setdefault(p["dt"].year, []).append(p)
    blocks = ""
    for y, ps in years.items():
        lis = "".join(f'<li><a href="{p["url"]}" lang="fr">{esc(p["title"])}</a><span>{esc(fdate(p["dt"], lang))}'
                      f'{" · " + esc(p["trip"]["title"][lang]) if p.get("trip") else ""}</span></li>' for p in ps)
        blocks += f'<div class="year"><h2>{y}</h2><ul>{lis}</ul></div>'
    body = f"""<section class="wrap post-head"><p class="kicker">{t['nav_archive']}</p><h1>{t['archive_title']}</h1>
<p style="margin:0;font-size:19px;color:var(--ink-soft)">{t['archive_lead']}</p></section>
<div class="wrap" style="padding-bottom:96px">{blocks}</div>"""
    other = PATHS["en" if lang == "fr" else "fr"]["archive"]
    write(P["archive"], layout(lang, P["archive"], t["archive_title"], t["archive_lead"], body, other))


def page_about(lang):
    P = PATHS[lang]
    src = os.path.join(ROOT, "content", "pages", f"about.{lang}.html")
    content = open(src, encoding="utf-8").read() if os.path.exists(src) else ""
    t = T[lang]
    body = f"""<section class="wrap post-head"><p class="kicker">{t['about_kicker']}</p><h1>{t['about_title']}</h1></section>
<div class="wrap post-wrap"><aside class="post-aside"><figure class="polaroid tilt-r" style="margin:0;padding:8px"><div class="frame">
<img src="/assets/img/home/velos.jpg" alt="{esc('Nos deux vélos et la remorque' if lang == 'fr' else 'Our two bikes and the trailer')}"><figcaption>{'En route' if lang == 'fr' else 'On the road'}</figcaption></div></figure></aside>
<article class="prose">{content}</article></div>"""
    other = PATHS["en" if lang == "fr" else "fr"]["about"]
    write(P["about"], layout(lang, P["about"], t["about_kicker"], t["about_short"], body, other, image="/assets/img/home/velos.jpg", active="about"))


def page_404():
    t = T["fr"]
    te = T["en"]
    body = f"""<section class="wrap post-head" style="padding:80px 32px 120px"><p class="kicker">404</p><h1>{t['notfound_title']}</h1>
<p style="margin:0;font-size:19px;color:var(--ink-soft)">{t['notfound_txt']}</p>
<div class="actions"><a class="btn solid" href="/">{t['home']}</a><a class="btn" href="/archives/">{t['archive_title']}</a></div>
<p lang="en" style="margin:24px 0 0;color:var(--muted)">{te['notfound_title']} <a href="/en/">{te['home']}</a></p></section>"""
    write("/404.html", layout("fr", "/404.html", "Page introuvable", t["notfound_txt"], body))


def feeds(posts, trips):
    latest = sorted(posts, key=lambda p: p["dt"], reverse=True)[:20]
    items = ""
    for p in latest:
        cover = media(p.get("cover"), 1200)
        if cover.startswith("/"):
            cover = SITE_URL + cover
        items += f"""<item><title>{esc(p['title'])}</title><link>{SITE_URL}{p['url']}</link><guid>{SITE_URL}{p['url']}</guid>
<pubDate>{p['dt'].strftime('%a, %d %b %Y %H:%M:%S')} +0000</pubDate><description>{esc(p['excerpt'])}</description>
{f'<enclosure url="{esc(cover)}" type="image/jpeg" length="0"/>' if cover else ''}</item>"""
    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>The Quiet Adventure</title><link>{SITE_URL}/</link>
<description>Carnets de voyage, à vélo et en famille.</description><language>fr</language>{items}</channel></rss>"""
    with open(os.path.join(OUT, "feed.xml"), "w", encoding="utf-8") as f:
        f.write(rss)
    urls = []
    for lang in ("fr", "en"):
        urls += list(PATHS[lang].values())
        urls += [trip_url(x, lang) for x in trips]
    urls += [p["url"] for p in posts]
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sm += "".join(f"<url><loc>{SITE_URL}{u}</loc></url>\n" for u in urls) + "</urlset>\n"
    with open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sm)
    with open(os.path.join(OUT, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")


OLD_CATEGORIES = {
    "asia": "/voyages/", "europe": "/voyages/", "north-america": "/voyages/", "oceania": "/voyages/", "south-america": "/voyages/colombie/",
    "road-trips": "/voyages/", "vie-quotidienne": "/voyages/echappees-a-velo-en-france/", "africa": "/voyages/", "non-categorise": "/archives/",
    "asia/china": "/voyages/australie/", "asia/indonesie": "/voyages/bali/", "asia/japan": "/voyages/kyushu-a-velo/", "asia/malaisia": "/voyages/",
    "asia/philippines": "/voyages/escapades/", "asia/south-korea": "/voyages/coree-a-velo/", "asia/sri-lanka": "/voyages/escapades/",
    "asia/south-korea/east-coast": "/voyages/coree-a-velo/", "asia/south-korea/jeju-island": "/voyages/coree-a-velo/",
    "asia/south-korea/seomjingang": "/voyages/coree-a-velo/", "asia/south-korea/seoul-to-busan": "/voyages/coree-a-velo/",
    "asia/south-korea/yeongsangang": "/voyages/coree-a-velo/",
    "europe/croatie": "/voyages/retour-en-europe-a-velo/", "europe/france": "/voyages/", "europe/france/voyages-a-velo": "/voyages/",
    "europe/italie": "/voyages/retour-en-europe-a-velo/", "europe/montenegro": "/voyages/escapades/", "europe/slovenie": "/voyages/retour-en-europe-a-velo/",
    "europe/suisse": "/voyages/suisse-en-train/",
    "north-america/canada": "/voyages/quebec/", "north-america/canada/british-columbia": "/voyages/canada-2020/",
    "north-america/canada/ontario": "/voyages/canada-2020/", "north-america/canada/quebec": "/voyages/quebec/",
    "north-america/usa": "/voyages/ouest-americain/", "oceania/australia": "/voyages/australie/", "oceania/new-zealand": "/voyages/nouvelle-zelande/",
    "south-america/colombia": "/voyages/colombie/",
}


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    posts = load_posts()
    trips, leftovers = assign_trips(posts, json.load(open(os.path.join(ROOT, "data", "trips.json"), encoding="utf-8")))
    books = json.load(open(os.path.join(ROOT, "data", "books.json"), encoding="utf-8"))
    for p in posts:
        URL_BY_SLUG[p["url"].rstrip("/").split("/")[-1]] = p["url"]
    for lang in ("fr", "en"):
        page_home(lang, posts, trips, books)
        page_trips(lang, trips)
        for x in trips:
            page_trip(lang, x, books)
        page_map(lang, trips)
        page_books(lang, books, trips)
        page_archive(lang, posts)
        page_about(lang)
    for p in posts:
        page_post(p, None)
    page_404()
    feeds(posts, trips)
    for cat, target in OLD_CATEGORIES.items():
        redirect(f"/category/{cat}/", target)
    redirect("/feed/", "/feed.xml")
    shutil.copytree(os.path.join(ROOT, "assets"), os.path.join(OUT, "assets"))
    if os.path.isdir(os.path.join(ROOT, "media")):
        shutil.copytree(os.path.join(ROOT, "media"), os.path.join(OUT, "media"))
    if os.path.exists(os.path.join(ROOT, "CNAME")):
        shutil.copy(os.path.join(ROOT, "CNAME"), os.path.join(OUT, "CNAME"))
    open(os.path.join(OUT, ".nojekyll"), "w").close()
    print(f"Site construit : {len(posts)} récits, {len(trips)} voyages"
          + (f", {len(leftovers)} récits hors voyage : " + ", ".join(p['slug'] for p in leftovers) if leftovers else ""))


if __name__ == "__main__":
    main()
    if "--serve" in sys.argv:
        import functools
        import http.server
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=OUT)
        print("http://localhost:8000")
        http.server.ThreadingHTTPServer(("", 8000), handler).serve_forever()
