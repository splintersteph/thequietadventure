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
from decor import hero_decor, motif_svg, post_decor, post_flags, flags_html, stamp_svg, trip_flags  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "_site")
SITE_URL = "https://thequietadventure.com"
BASE = os.environ.get("BASE_PATH", "").rstrip("/")
OG = "--no-og" not in sys.argv  # images d'aperçu : une minute de plus à la construction  # "/thequietadventure" when served from github.io
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
        "trk_velo": "À vélo", "trk_pied": "À pied", "tracks_title": "Les traces de ce récit", "tracks_n": "traces",
        "tracks_kicker_velo": "Sur la route", "tracks_kicker_pied": "Sur le sentier", "tracks_kicker_mix": "Sur la route",
        "moving_velo": "en selle", "moving_pied": "de marche", "moving_mix": "en mouvement",
        "km_velo": "à vélo", "km_pied": "à pied", "km_mix": "parcourus",
        "read_min": "min de lecture", "back_trips": "← Tous les voyages",
        "book_of_trip": "Le livre du voyage", "book_cta": "Découvrir le livre",
        "books_page_lead": "Après chaque voyage, nous reprenons les récits et les plus belles photos pour en faire un livre. [Indiquer ici comment se procurer les livres : PDF, impression, Amazon…]",
        "archive_title": "Tous les récits", "archive_lead": "Dix ans de carnets, du plus récent au plus ancien.",
        "map_page_title": "La carte de nos voyages",
        "trips_page_title": "Nos voyages", "trips_page_lead": "Les grands voyages à vélo, les road trips et les années d'expatriation, rangés par voyage plutôt que par pays.",
        "notfound_title": "Cette page s'est perdue en route.", "notfound_txt": "Elle a peut-être changé d'adresse avec le nouveau site.", "home": "Retour à l'accueil",
        "modes": {"velo": "À vélo", "train": "En train", "roadtrip": "Road trip", "expat": "Expatriation"},
        "lang_name": "Français",
        "search": "Rechercher dans les récits", "search_short": "Chercher", "theme_dark": "Passer en mode nuit", "theme_light": "Passer en mode jour",
    },
    "en": {
        "tagline": "travel journal",
        "nav_trips": "Journeys", "nav_map": "Map", "nav_books": "Books", "nav_about": "About us", "nav_archive": "Archive",
        "menu": "Menu", "skip": "Skip to content",
        "hero_title": "Travelling slowly, as a family, at the pace of the pedals.",
        "hero_lead": "Our travel stories, day after day: cycling routes, trains caught at the last second, playgrounds found for Clémence and the people we met along the way.",
        "read_latest": "Latest journey", "explore_map": "Explore the map",
        "latest_kicker": "Our latest journey", "whole_trip": "The whole journey →",
        "trips_kicker": "The big journeys", "trips_title": "One journey, one journal. Each reads like a book.",
        "also": "Also:", "all_trips": "All journeys",
        "books_kicker": "Our books", "books_title": "Every journey becomes a photo book.",
        "books_aside": "The blog stories, laid out again with the best photos of each trip.",
        "map_kicker": "The map", "map_title": "All our stories, where they happened.",
        "map_aside": "Each dot is a story. Click it to open it.",
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
        "trk_velo": "By bike", "trk_pied": "On foot", "tracks_title": "The routes of this story", "tracks_n": "routes",
        "tracks_kicker_velo": "On the road", "tracks_kicker_pied": "On the trail", "tracks_kicker_mix": "On the road",
        "moving_velo": "in the saddle", "moving_pied": "walking", "moving_mix": "moving",
        "km_velo": "by bike", "km_pied": "on foot", "km_mix": "covered",
        "read_min": "min read", "back_trips": "← All journeys",
        "book_of_trip": "The book of the journey", "book_cta": "See the book",
        "books_page_lead": "After each journey we gather the stories and the best photos into a book. [Explain here how to get the books: PDF, print, Amazon…]",
        "archive_title": "All stories", "archive_lead": "Ten years of journals, newest first.",
        "map_page_title": "The map of our travels",
        "trips_page_title": "Our journeys", "trips_page_lead": "Long bike journeys, road trips and years abroad, organised by journey rather than by country.",
        "notfound_title": "This page got lost on the way.", "notfound_txt": "It may have moved with the new site.", "home": "Back to the homepage",
        "modes": {"velo": "By bike", "train": "By train", "roadtrip": "Road trip", "expat": "Living abroad"},
        "lang_name": "English",
        "search": "Search the stories", "search_short": "Search", "theme_dark": "Switch to night mode", "theme_light": "Switch to day mode",
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
    "toulouse-bordeaux-a-velo": ["france"], "marseille-lyon-a-velo": ["france"], "provence-a-velo": ["france"], "via-allier-a-velo": ["france"],
    "australie": ["oceanie"], "nouvelle-zelande": ["oceanie"],
    "ouest-americain": ["amerique"], "floride-et-louisiane": ["amerique"], "quebec": ["amerique"], "hiver-a-montreal": ["amerique"], "canada-2020": ["amerique"], "colombie": ["amerique"],
    "sri-lanka": ["asie"], "philippines": ["asie"], "montenegro": ["europe"],
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


class _Lazy:
    """extras.py importe build.py : on le charge seulement au premier usage."""
    def __getattr__(self, k):
        import extras
        return getattr(extras, k)


VT = _Lazy()


class _LazyDesign:
    def __getattr__(self, k):
        import design
        return getattr(design, k)


DZ = _LazyDesign()


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
        h["fstem"] = re.sub(r"^\d{4}-\d\d-\d\d-", "", os.path.basename(f)[:-5])
        h["dt"] = dt.datetime.fromisoformat(h["date"])
        h["words"] = len(text_of(h["body"]).split())
        h["excerpt"] = excerpt(h["body"])
        en = os.path.join(ROOT, "content", "posts-en", os.path.basename(f))
        if os.path.exists(en):
            eraw = open(en, encoding="utf-8").read()
            em = re.match(r"\s*<!--\s*(\{.*?\})\s*-->\s*", eraw, re.S)
            e = json.loads(em.group(1))
            e["body"] = eraw[em.end():]
            e["url"] = "/en" + h["url"]
            e["words"] = len(text_of(e["body"]).split())
            e["excerpt"] = excerpt(e["body"])
            h["en"] = e
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
        t["color"] = t.get("color") or PALETTE[i % len(PALETTE)]
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


# ------------------------------------------------------------------ Strava
def _load_strava():
    path = os.path.join(ROOT, "data", "strava", "activities.json")
    acts = {a["id"]: a for a in json.load(open(path, encoding="utf-8"))} if os.path.exists(path) else {}
    manual = os.path.join(ROOT, "data", "strava", "manual.json")  # traces redessinées, sans activité Strava
    if os.path.exists(manual):
        acts.update({a["id"]: a for a in json.load(open(manual, encoding="utf-8"))["activities"]})
    mp = os.path.join(ROOT, "data", "strava", "posts.json")
    mapping = json.load(open(mp, encoding="utf-8")) if os.path.exists(mp) else {}
    return acts, mapping.get("posts", {}), mapping.get("trips", {})


STRAVA, STRAVA_POSTS, STRAVA_TRIPS = _load_strava()
TRACKS_VERSION = __import__("hashlib").md5(json.dumps(sorted(STRAVA)).encode()).hexdigest()[:8]


def assign_strava(trips):
    """Each story gets the activities embedded in it plus those listed in data/strava/posts.json."""
    for t in trips:
        ids = []
        for p in t["posts"]:
            own = re.findall(r'<div class="strava" data-activity="(\d+)"></div>', p["body"])
            own += STRAVA_POSTS.get(p["fstem"], []) + STRAVA_POSTS.get(p["slug"], [])
            p["acts"] = [STRAVA[i] for i in dict.fromkeys(own) if i in STRAVA]
            ids += [a["id"] for a in p["acts"]]
        ids += STRAVA_TRIPS.get(t["slug"], [])
        t["acts"] = sorted((STRAVA[i] for i in dict.fromkeys(ids) if i in STRAVA), key=lambda a: a["date"])


def tracks_url(t):
    return f"/traces/{t['slug']}.json?v={TRACKS_VERSION}"


def write_tracks(trips):
    for t in trips:
        if t["acts"]:
            path = os.path.join(OUT, "traces", f"{t['slug']}.json")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump([[a["id"], a["poly"]] for a in t["acts"]], f, separators=(",", ":"))


def act_totals(acts):
    return (sum(a["dist"] for a in acts) / 1000, sum(a["elev"] for a in acts), sum(a["time"] for a in acts))


def fkm(km, lang="fr"):
    if km >= 10:
        return f"{km:,.0f}".replace(",", "\u202f" if lang == "fr" else ",")
    return f"{km:.1f}".replace(".", "," if lang == "fr" else ".")


def fdur(sec):
    h, m = divmod(round(sec / 60), 60)
    return f"{h} h {m:02d}" if h else f"{m} min"


def act_kind(acts, lang):
    rides = sum(1 for a in acts if "Ride" in a["type"])
    if rides == len(acts):
        return "velo"
    return "pied" if rides == 0 else "mix"


def mini_trace(a, color, w=132, h=92):
    """Small inline SVG drawing of one activity, drawn with a stroke animation."""
    pts = decode_polyline(a["poly"])
    if len(pts) < 2:
        return ""
    step = max(1, len(pts) // 90)
    pts = pts[::step] + [pts[-1]]
    k = math.cos(math.radians(sum(p[0] for p in pts) / len(pts)))
    xs = [p[1] * k for p in pts]
    ys = [-p[0] for p in pts]
    span = max(max(xs) - min(xs), max(ys) - min(ys), 1e-6)
    pad = 10
    sc = min((w - 2 * pad) / max(max(xs) - min(xs), span * 0.2), (h - 2 * pad) / max(max(ys) - min(ys), span * 0.2))
    ox = (w - (max(xs) - min(xs)) * sc) / 2
    oy = (h - (max(ys) - min(ys)) * sc) / 2
    c = [((x - min(xs)) * sc + ox, (y - min(ys)) * sc + oy) for x, y in zip(xs, ys)]
    d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in c)
    (x0, y0), (x1, y1) = c[0], c[-1]
    return (f'<svg class="trk-svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" aria-hidden="true">'
            f'<path class="trk-bg" d="{d}"/><path class="trk-line" d="{d}" pathLength="1" stroke="{color}"/>'
            f'<circle class="trk-a" cx="{x0:.1f}" cy="{y0:.1f}" r="3.5"/><circle class="trk-b" cx="{x1:.1f}" cy="{y1:.1f}" r="4" fill="{color}"/></svg>')


def act_card(a, color, lang="fr", tag="div"):
    t = T[lang]
    d = dt.datetime.fromisoformat(a["date"])
    kind = "velo" if "Ride" in a["type"] else "pied"
    bits = [f"<b>{fkm(a['dist'] / 1000, lang)}</b> km"]
    if a["elev"] >= 15:
        bits.append(f"<b>{a['elev']:,}</b> m D+".replace(",", "\u202f"))
    if a["time"]:
        bits.append(fdur(a["time"]))
    name = a["name"].replace("->", "→").replace("➡️", "→").replace("➡", "→")
    inner = (f'{mini_trace(a, color)}<span class="trk-txt"><span class="trk-kind">{t["trk_" + kind]} · {esc(fdate(d, lang))}</span>'
             f'<span class="trk-name">{esc(name)}</span><span class="trk-stats">{" · ".join(bits)}</span>')
    if a.get("manual"):  # trace redessinée : pas de page Strava
        return f'<{tag} class="trk" style="--trip:{color}"><div class="trk-static">{inner}</span></div></{tag}>'
    return (f'<{tag} class="trk" style="--trip:{color}">'
            f'<a href="https://www.strava.com/activities/{a["id"]}" rel="noopener" aria-label="{esc(name)} ({t["strava_go"].rstrip(" →")})">'
            f'{inner}<span class="trk-go">{t["strava_go"]}</span></span></a></{tag}>')


def tracks_section(p, trip, lang="fr"):
    acts = p.get("acts") or []
    if not acts:
        return ""
    t = T[lang]
    km, elev, sec = act_totals(acts)
    kind = act_kind(acts, lang)
    embedded = set(re.findall(r'data-activity="(\d+)"', p["body"]))
    listed = [a for a in acts if a["id"] not in embedded]
    stats = [f"<span><b>{fkm(km, lang)}</b> km</span>"]
    if elev >= 30:
        stats.append(f"<span><b>{elev:,}</b> m D+</span>".replace(",", "\u202f"))
    if sec:
        stats.append(f"<span><b>{fdur(sec)}</b> {t['moving_' + kind]}</span>")
    if len(acts) > 1:
        stats.append(f"<span><b>{len(acts)}</b> {t['tracks_n']}</span>")
    data = {"tracks": [{"src": tracks_url(trip), "color": trip["color"]}], "hl": [a["id"] for a in acts], "fit": "hl"}
    lst = "".join(act_card(a, trip["color"], lang, "li") for a in listed)
    return f"""<section class="tracks" id="traces" style="--trip:{trip['color']}"><div class="tracks-head">
<p class="kicker">{t['tracks_kicker_' + kind]}</p><h2>{t['tracks_title']}</h2><div class="tk-stats">{"".join(stats)}</div></div>
{map_div(data, "map tk-map", t['tracks_title'])}
{f'<ol class="trk-list">{lst}</ol>' if lst else ''}</section>"""


def trip_lines(t):
    """Fallback when no Strava trace exists: dashed line through the stories."""
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


def trip_map_data(t, points, hl=None):
    """Map data for a trip: real Strava traces when we have them, otherwise the fallback line."""
    data = {"points": points}
    if t.get("acts"):
        data["tracks"] = [{"src": tracks_url(t), "color": t["color"]}]
        if hl:
            data["hl"] = hl
    else:
        data["lines"] = trip_lines(t)
    legs = VT.leg_lines(t)
    if legs:
        data["lines"] = data.get("lines", []) + legs
    return data


# ------------------------------------------------------------------ helpers
def fdate(d, lang, day=True):
    m = MONTHS[lang][d.month - 1]
    if lang == "fr":
        return f"{d.day if d.day > 1 else '1er'} {m} {d.year}" if day else f"{m} {d.year}"
    return f"{m} {d.day}, {d.year}" if day else f"{m} {d.year}"


def trip_url(t, lang):
    return f"/voyages/{t['slug']}/" if lang == "fr" else f"/en/journeys/{t['en_slug']}/"


def img(src, alt, cls="ph", width=1000, extra="", vt=None):
    import extras
    vts = f' style="view-transition-name:{vt}"' if vt else ""
    lq = extras.lq_style(src)
    if lq and vts:
        lq = lq.replace(' style="', ' style="view-transition-name:' + vt + ';')
        vts = ""
    return f'<img class="{cls}" src="{esc(media(src, width))}" alt="{esc(alt)}" loading="lazy" decoding="async"{extra}{lq}{vts}>'


def map_div(data, cls="map", label=""):
    return f'<div class="{cls}" data-map="{esc(json.dumps(data, ensure_ascii=False, separators=(",", ":")))}" role="region" aria-label="{esc(label)}"></div>'


def layout(lang, path, title, desc, content, alt_path=None, image=None, active=None, body_class="", og=None, head="", scripts=""):
    t = T[lang]
    P = PATHS[lang]
    other = "en" if lang == "fr" else "fr"
    alt_path = alt_path or PATHS[other]["home"]
    full_title = f"{title} — The Quiet Adventure" if title else "The Quiet Adventure"
    og_size = ""
    if og:
        og_size = '\n<meta property="og:image:width" content="1200">\n<meta property="og:image:height" content="630">'
        og = SITE_URL + og
    else:
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
<html lang="{lang}" data-search="/data/search-{lang}.json?v={VERSION}">
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
<meta property="og:image" content="{esc(og)}">{og_size}
<meta property="og:locale" content="{'fr_FR' if lang == 'fr' else 'en_GB'}">
<meta name="twitter:card" content="summary_large_image">
<link rel="alternate" type="application/rss+xml" title="The Quiet Adventure" href="{FEED[lang]}">
<link rel="icon" href="/assets/img/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Caveat:wght@500;700&family=Karla:wght@400;500;700&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,600;1,6..72,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/css/site.css?v={VERSION}">
<meta name="theme-color" content="#F3ECDF">
<script>window.TQA_BASE="{BASE}";var th=null;try{{th=localStorage.getItem("tqa-theme")}}catch(e){{}}if(!th&&window.matchMedia&&matchMedia("(prefers-color-scheme: dark)").matches)th="dark";if(th)document.documentElement.dataset.theme=th;</script>
{head}
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
<a href="{'/passeport/' if lang == 'fr' else '/en/passport/'}"{' aria-current="page"' if active == 'passport' else ''}>{'Passeport' if lang == 'fr' else 'Passport'}</a>
{nav_link('books', t['nav_books'])}
{nav_link('about', t['nav_about'])}
<div class="lang" role="group" aria-label="Langue / Language">{switch}</div>
<span class="tools"><button type="button" class="search-btn" aria-label="{t['search']}"><svg viewBox="0 0 24 24" width="17" height="17" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M15.5 15.5 21 21" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg><span>{t['search_short']}</span><kbd>/</kbd></button>
<button type="button" class="theme-btn" aria-label="{t['theme_dark']}" data-dark="{t['theme_dark']}" data-light="{t['theme_light']}"><svg class="moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/></svg><svg class="sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4.2"/><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M4.9 19.1l1.8-1.8M17.3 6.7l1.8-1.8"/></svg></button></span>
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
<div class="links"><a href="{FEED[lang]}">{t['rss']}</a><a href="{P['archive']}">{t['nav_archive']}</a><a href="{P['trips']}">{t['nav_trips']}</a><a href="{P['books']}">{t['nav_books']}</a><a href="{'/passeport/' if lang == 'fr' else '/en/passport/'}">{'Le passeport' if lang == 'fr' else 'The passport'}</a></div>
</div>
<div class="bottom"><span>The Quiet Adventure — {t['since']}</span><span><a href="{PATHS['fr']['home']}" lang="fr">Français</a> · <a href="{PATHS['en']['home']}" lang="en">English</a></span></div>
</div>
</footer>
<script src="/assets/js/site.js?v={VERSION}" defer></script>
{scripts}
</body>
</html>
"""


def asset_version():
    import hashlib
    h = hashlib.md5()
    for f in ("assets/css/site.css", "assets/js/site.js", "assets/js/globe.js", "assets/js/route.js"):
        h.update(open(os.path.join(ROOT, f), "rb").read())
    return h.hexdigest()[:8]


VERSION = asset_version()


def with_base(content):
    if not BASE:
        return content
    content = re.sub(r'((?:href|src|action)=")/(?!/)', lambda m: m.group(1) + BASE + "/", content)
    return re.sub(r'(&quot;(?:url|src)&quot;:&quot;)/(?!/)', lambda m: m.group(1) + BASE + "/", content)


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
<div class="card-media">{img(t.get('cover'), t['title'][lang], width=900, vt=VT.vt_trip(t))}<span class="card-stamp">{stamp_svg(t, lang, 84)}</span></div>
<div class="body"><span class="flags">{trip_flags(t, 18)}</span><span class="label ochre">{esc(lbl)}</span><h3>{esc(t['title'][lang])}</h3>
<p>{esc(t['lead'][lang])}</p><span class="label">{n} {T[lang]['stories'] if n > 1 else T[lang]['story']}</span></div></a>"""


def V(p, lang):
    """The post as shown in a language: its translation when there is one, else the French original."""
    if lang == "en" and p.get("en"):
        return p["en"]
    return p


def fr_note(p, lang):
    return ' <span class="lang-note" lang="en">FR</span>' if lang == "en" and not p.get("en") else ""


def post_lang(p, lang):
    return "en" if lang == "en" and p.get("en") else "fr"


def story_card(p, lang="fr"):
    t = p.get("trip")
    lbl = fdate(p["dt"], lang)
    if t:
        lbl = f"{T[lang]['step']} {p['step']} · {lbl}"
    v = V(p, lang)
    return f"""<a class="story" href="{v['url']}" lang="{post_lang(p, lang)}">
{img(p.get('cover'), v['title'], width=900, vt=VT.vt_post(p))}
<span class="label">{post_flags(p, 13)} {esc(lbl)}</span><h3>{esc(v['title'])}{fr_note(p, lang)}</h3><p>{esc(v['excerpt'])}</p></a>"""


def latest_section(trip, latest, lang):
    t = T[lang]
    tiles = ""
    for i, p in enumerate(latest):
        note = fr_note(p, lang)
        v = V(p, lang)
        tiles += f"""<a class="lt lt{i}" href="{v['url']}" lang="{post_lang(p, lang)}">{img(p.get('cover'), v['title'], cls='bg', width=1400 if i == 0 else 800, vt=VT.vt_post(p))}
<span class="lt-shade"></span><span class="lt-pin">{p['step']}</span>
<span class="lt-body"><span class="lt-meta">{post_flags(p, 15)} {esc(fdate(p['dt'], lang))}</span>
<span class="lt-title">{esc(v['title'])}{note}</span>{f'<span class="lt-ex">{esc(v["excerpt"])}</span>' if i == 0 else ''}
<span class="lt-go">{'Lire le récit' if lang == 'fr' else 'Read the story'} <b aria-hidden="true">→</b></span></span></a>"""
    n = len(trip["posts"])
    return f"""<section class="latest" style="--trip:{trip['color']}"><div class="wrap">
<div class="latest-head"><div><p class="kicker">{t['latest_kicker']}</p><h2 class="h-sec">{esc(trip['title'][lang])}</h2>
<p class="latest-lead">{esc(trip['lead'][lang])}</p>
<div class="latest-meta"><span class="flag-chip">{trip_flags(trip, 18)}</span><span>{esc(trip['period'][lang])}</span><span>{n} {t['stories']}</span></div></div>
<a class="latest-stamp" href="{trip_url(trip, lang)}" aria-label="{esc(t['whole_trip'])}">{stamp_svg(trip, lang, 150)}</a></div>
<div class="latest-grid">{tiles}</div>
<div class="latest-foot"><a class="btn light" href="{trip_url(trip, lang)}">{t['whole_trip']}</a></div>
</div></section>"""


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
                pts.append({"lat": p["geo"][0], "lng": p["geo"][1], "title": V(p, lang)["title"], "url": V(p, lang)["url"],
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
    first_url = V(latest[0], lang)["url"] if (lang == "fr" or latest[0].get("en")) else trip_url(latest_trip, lang)
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

{DZ.on_this_day(posts, lang)}

{VT.globe_section(lang, trips)}

{latest_section(latest_trip, latest, lang)}

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
    write(P["home"], layout(lang, P["home"], "", desc, body, alt_path=PATHS["en" if lang == "fr" else "fr"]["home"],
                            scripts=VT.GLOBE_SCRIPTS.format(v=VERSION), body_class="home"))


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


def leg_km(p):
    if not p.get("acts"):
        return ""
    return f' · {fkm(act_totals(p["acts"])[0])} km'


def trip_km_chip(trip, lang):
    acts = trip.get("acts") or []
    if not acts:
        return ""
    km = act_totals(acts)[0]
    kind = "velo" if trip.get("mode") == "velo" else act_kind(acts, lang)
    return f'<span>{fkm(km)} km {T[lang]["km_" + kind]}</span>'


def route_next(trip, lang):
    """End of the timeline: a little road that leads the traveller on to the next journey."""
    nxt = trip.get("next_trip")
    if not nxt:
        return (f'<li class="route-end"><a href="{PATHS[lang]["trips"]}"><span>'
                f'{"La suite s’écrit en ce moment…" if lang == "fr" else "The next chapter is being written…"}</span></a></li>')
    rider = motif_svg(nxt.get("mode", "velo"), 34, "#FFFDF8", 2.4)
    return f"""<li class="route-next" style="--next:{nxt['color']}"><a class="rn" href="{trip_url(nxt, lang)}">
<span class="rn-end"><span>{'Fin du voyage' if lang == 'fr' else 'The end'}</span></span>
<span class="rn-road" aria-hidden="true"><svg viewBox="0 0 120 220" preserveAspectRatio="none"><path d="M60 0 C60 60 20 70 30 120 S100 170 60 220" pathLength="1"/></svg>
<span class="rn-rider">{rider}</span></span>
<span class="rn-card">{img(nxt.get('cover'), nxt['title'][lang], cls='rn-img', width=1200)}<span class="rn-shade"></span>
<span class="rn-stamp">{stamp_svg(nxt, lang, 110)}</span>
<span class="rn-txt"><span class="rn-kicker">{'Le voyage suivant' if lang == 'fr' else 'The next journey'}</span>
<span class="rn-title">{esc(nxt['title'][lang])}</span><span class="rn-meta">{trip_flags(nxt, 16)} {esc(nxt['period'][lang])}</span>
<span class="rn-go">{'Continuer la route' if lang == 'fr' else 'Keep going'} <b aria-hidden="true">→</b></span></span></span></a></li>"""


def page_trip(lang, trip, books):
    t = T[lang]
    url = trip_url(trip, lang)
    other_url = trip_url(trip, "en" if lang == "fr" else "fr")
    n = len(trip["posts"])
    items = ""
    month = None
    for p in trip["posts"]:
        note = fr_note(p, lang)
        v = V(p, lang)
        m = (p["dt"].year, p["dt"].month)
        if m != month:
            month = m
            items += f'<li class="route-month"><span>{esc(fdate(p["dt"], lang, False))}</span></li>'
        side = "l" if p["step"] % 2 else "r"
        items += f"""<li class="leg {side}"><span class="pin" aria-hidden="true">{p['step']}</span>
<a class="leg-card" href="{v['url']}" lang="{post_lang(p, lang)}"><figure class="snap">{img(p.get('cover'), v['title'], cls='', width=900, vt=VT.vt_post(p))}
<figcaption>{esc(fdate(p['dt'], lang))}</figcaption></figure>
<div class="leg-txt"><span class="label ochre">{t['step']} {p['step']} {t['of']} {n}{leg_km(p)}</span><h3>{esc(v['title'])}{note}</h3><p>{esc(v['excerpt'])}</p>
<span class="go">{'Lire le récit →' if lang == 'fr' else ('Read the story →' if p.get('en') else 'Read the story (in French) →')}</span></div></a></li>"""
    pts = [{"lat": p["geo"][0], "lng": p["geo"][1], "title": V(p, lang)["title"], "url": V(p, lang)["url"],
            "label": f"{t['step']} {p['step']}", "color": trip["color"]} for p in trip["posts"] if p.get("geo")]
    map_sec = ""
    if pts:
        map_sec = f"""<section class="section band" style="padding:64px 0"><div class="wrap">
<div class="sec-head"><div><p class="kicker">{t['trip_map']}</p></div></div>
{map_div(trip_map_data(trip, pts), "map", t['trip_map'])}</div></section>"""
    book = next((b for b in books if b["id"] == trip.get("book")), None)
    book_sec = ""
    if book:
        book_sec = f"""<section class="section"><div class="wrap book-strip">
<img src="{book['cover']}" alt="{esc(('Couverture du livre ' if lang == 'fr' else 'Cover of the book ') + book['title'][lang])}" loading="lazy">
<div style="display:flex;flex-direction:column;gap:16px"><p class="kicker">{t['book_of_trip']}</p><h2 class="h-sec">{esc(book['title'][lang])}</h2>
<p style="margin:0;color:var(--ink-soft);font-size:18px">{esc(book['tagline'][lang])} {esc(book['detail'][lang])}.</p>
<div class="actions"><a class="btn" href="{PATHS[lang]['books']}#{book['id']}">{t['book_cta']}</a></div></div></div></section>"""
    body = f"""<section class="trip-hero">{img(trip.get('cover'), trip['title'][lang], cls='', width=1800, extra=' fetchpriority="high"', vt=VT.vt_trip(trip))}{hero_decor(trip, lang)}
<div class="wrap"><a class="crumbs" href="{PATHS[lang]['trips']}">{t['back_trips']}</a>
<p class="kicker" style="margin-top:18px">{esc(trip['period'][lang])}</p><h1>{esc(trip['title'][lang])}</h1><p>{esc(trip['lead'][lang])}</p>
<div class="chips"><span class="flag-chip">{trip_flags(trip, 18)}</span><span>{t['modes'][trip['mode']]}</span><span>{n} {t['stories'] if n > 1 else t['story']}</span>{trip_km_chip(trip, lang)}</div></div></section>
{DZ.trip_frise(trip, lang)}
{map_sec}
<section class="section"><div class="wrap"><div class="sec-head"><div><p class="kicker">{t['trip_stories']}</p></div></div>
<ol class="route" style="--trip:{trip['color']}">{items}{route_next(trip, lang)}</ol></div></section>
{book_sec}"""
    write(url, layout(lang, url, trip["title"][lang], trip["lead"][lang], body, other_url, image=trip.get("cover"), active="trips"))


STRAVA_ICON = '<svg class="ic" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#2F5D50" stroke-width="1.6" aria-hidden="true"><circle cx="6" cy="17" r="3.5"/><circle cx="18" cy="17" r="3.5"/><path d="M6 17l4-8h5l3 8M10 9l-1.5-3H6M15 9l-2 8"/></svg>'


URL_BY_SLUG = {}


def render_body(body, lang="fr", trip=None):
    t = T[lang]
    body = DZ.mosaic(body)

    def fix_link(m):
        url = m.group(2)
        mm = re.match(r"^/\d{4}/\d{2}/\d{2}/([^/]+)/?$", url)
        if mm and mm.group(1) in URL_BY_SLUG:
            url = V(URL_BY_SLUG[mm.group(1)], lang)["url"]
        return m.group(1) + url + m.group(3)
    body = re.sub(r'(<a[^>]*?\shref=")(/\d{4}/[^"]+)(")', fix_link, body)

    def strava(m):
        aid = m.group(1)
        if aid in STRAVA:
            return act_card(STRAVA[aid], trip["color"] if trip else "#2F5D50", lang)
        return (f'<a class="strava-card" href="https://www.strava.com/activities/{aid}" rel="noopener">'
                f'<span class="t">{STRAVA_ICON}<b>{t["strava_title"]}</b></span><span class="go">{t["strava_go"]}</span></a>')
    body = re.sub(r'<div class="strava" data-activity="(\d+)"></div>', strava, body)
    body = re.sub(r'(<(?:img|video)[^>]*?\ssrc=")(/media/[^"]+)(")', lambda m: m.group(1) + esc(media(m.group(2))) + m.group(3), body)
    body = re.sub(r'(<a[^>]*?\shref=")(/media/[^"]+)(")', lambda m: m.group(1) + esc(media(m.group(2), 2000)) + m.group(3), body)
    return body


def page_post(p, lang="fr"):
    t = T[lang]
    v = V(p, lang)
    trip = p.get("trip")
    mins = max(1, round(v["words"] / 230))
    fl = "".join(f'<a href="{DZ.country_url(c, lang)}" title="{esc(VT.COUNTRY_NAMES[c][0 if lang == "fr" else 1])}">{flags_html([c], 16)}</a>'
                 for c in VT.countries_of(p))
    chips = (f'<span class="flag-chip">{fl}</span>' if fl else "") + f"<span>{esc(fdate(p['dt'], lang))}</span><span>{mins} {t['read_min']}</span>"
    crumbs = ""
    aside = ""
    nav = ""
    prev_html = ""
    dbody = DZ.day_ids(p, render_body(v['body'], lang, trip=trip), lang)[0]
    rbody, route = VT.route_body(p, dbody, lang) if trip else (dbody, "")
    if route:
        rbody = DZ.day_sketches(rbody, p.get("acts"), trip["color"], lang)
    rbody = VT.lq_body(rbody)
    if trip:
        tp = trip["posts"]
        i = p["step"] - 1
        crumbs = f'<a class="crumbs" href="{trip_url(trip, lang)}">← {esc(trip["title"][lang])} · {t["step"].lower()} {p["step"]} {t["of"]} {len(tp)}</a>'
        chips = f"<span>{esc(trip['title'][lang])}</span>" + chips
        if p.get("acts"):
            km = act_totals(p["acts"])[0]
            chips += f'<a class="km-chip" href="#traces">{motif_svg("velo" if act_kind(p["acts"], lang) != "pied" else "pied", 18, "currentColor", 1.8)}{fkm(km)} km</a>'
        lis = "".join(
            f'<a href="{V(q, lang)["url"]}"{" aria-current=\"page\" style=\"font-weight:700;color:var(--ink)\"" if q is p else ""}>{q["step"]}. {esc(V(q, lang)["title"])}</a>'
            for q in tp) if len(tp) <= 40 else ""
        mini = ""
        if route:
            mini = VT.route_panel(lang, trip.get("mode", "velo"))
        elif p.get("geo"):
            pts = [{"lat": q["geo"][0], "lng": q["geo"][1], "title": V(q, lang)["title"], "url": V(q, lang)["url"], "color": trip["color"] if q is not p else "#B5483B",
                    "r": 5 if q is not p else 8} for q in tp if q.get("geo")]
            mini = map_div(trip_map_data(trip, pts, [a["id"] for a in p.get("acts", [])]), "map", t["trip_map"]).replace('class="map"', 'class="map" style="aspect-ratio:auto;height:240px;min-height:0"')
        aside = f"""<aside class="post-aside"><div class="aside-card"><span class="aside-stamp">{stamp_svg(trip, lang, 96)}</span><span class="kicker">{t['the_trip']}</span>
<a href="{trip_url(trip, lang)}" style="font-family:var(--serif);font-size:22px;text-decoration:none;color:var(--ink)">{esc(trip['title'][lang])}</a>
<span class="label">{esc(trip['period'][lang])}</span>{mini}{f'<details class="aside-list"><summary>{t["trip_stories"]} ({len(tp)})</summary><nav aria-label="{esc(t["trip_stories"])}">{lis}</nav></details>' if route and lis else f'<nav aria-label="{esc(t["trip_stories"])}">{lis}</nav>'}</div></aside>"""
        prev_p = tp[i - 1] if i > 0 else None
        next_p = tp[i + 1] if i + 1 < len(tp) else None
        mode_icon = motif_svg(trip.get("mode", "velo"), 30, "#FFFDF8", 2.4)
        nav = f'<nav class="post-nav2" aria-label="{esc(t["trip_stories"])}" style="--trip:{trip["color"]}">'
        if next_p:
            nv = V(next_p, lang)
            nav += f"""<a class="nx" href="{nv['url']}">{img(next_p.get('cover'), '', cls='bg', width=1200, vt=VT.vt_post(next_p))}
<span class="shade"></span><span class="nx-top"><span class="nx-kicker">{t['next'].replace(' →', '')}</span><span class="nx-step">{t['step']} {next_p['step']}</span></span>
<span class="nx-title">{esc(nv['title'])}</span><span class="nx-date">{esc(fdate(next_p['dt'], lang))}</span>
<span class="nx-road" aria-hidden="true"><span class="nx-rider">{mode_icon}</span><span class="nx-arrow">→</span></span></a>"""
        else:
            nxt = trip.get("next_trip")
            if nxt:
                nav += f"""<a class="nx" href="{trip_url(nxt, lang)}" style="--trip:{nxt['color']}">{img(nxt.get('cover'), '', cls='bg', width=1200)}
<span class="shade"></span><span class="nx-top"><span class="nx-kicker">{'Voyage suivant' if lang == 'fr' else 'Next journey'}</span><span class="nx-step">{trip_flags(nxt, 14)}</span></span>
<span class="nx-title">{esc(nxt['title'][lang])}</span><span class="nx-date">{esc(nxt['period'][lang])}</span>
<span class="nx-road" aria-hidden="true"><span class="nx-rider">{motif_svg(nxt.get("mode", "velo"), 30, "#FFFDF8", 2.4)}</span><span class="nx-arrow">→</span></span></a>"""
            else:
                nav += f"""<a class="nx end" href="{trip_url(trip, lang)}"><span class="shade"></span><span class="nx-top"><span class="nx-kicker">{'Fin du voyage' if lang == 'fr' else 'End of the journey'}</span></span>
<span class="nx-title">{'Revoir tout le voyage' if lang == 'fr' else 'See the whole journey'} : {esc(trip['title'][lang])}</span>
<span class="nx-road" aria-hidden="true"><span class="nx-rider">{mode_icon}</span><span class="nx-arrow">→</span></span></a>"""
        nav += "</nav>"
        if prev_p:
            pv = V(prev_p, lang)
            prev_html = f"""<a class="pv" href="{pv['url']}">{img(prev_p.get('cover'), '', cls='', width=500, vt=VT.vt_post(prev_p))}<span><span class="label">{t['prev']}</span><b>{esc(pv['title'])}</b></span></a>"""
    cover = ""
    if p.get("cover"):
        cover = f'<div class="wrap post-cover"><div class="cover-frame">{img(p["cover"], v["title"], cls="", width=1800, extra=" fetchpriority=\"high\"", vt=VT.vt_post(p))}{post_decor(trip, lang)[0]}</div></div>'
    top = post_decor(trip, lang)[1]
    scripts = ""
    if route:
        kind = act_kind(p["acts"], lang)
        top = VT.route_extras(lang, "pied" if kind == "pied" else "velo", trip["color"])
        safe = route.replace("</", "<\\/")
        scripts = f'<script type="application/json" id="rt-data">{safe}</script>\n<script src="/assets/js/route.js?v={VERSION}" defer></script>'
    body = f"""{top}<section class="wrap post-head">{crumbs}<h1>{esc(v['title'])}</h1><div class="meta">{chips}</div></section>
{cover}
<div class="wrap post-wrap"{f' style="--trip:{trip["color"]}"' if trip else ""}>{aside}<article class="prose">{prev_html}{rbody}{tracks_section(p, trip, lang) if trip else ""}{nav}</article></div>"""
    if lang == "fr":
        alt = p["en"]["url"] if p.get("en") else (trip_url(trip, "en") if trip else PATHS["en"]["home"])
    else:
        alt = p["url"]
    og = VT.og_image(p, lang) if OG else None
    write(v["url"], layout(lang, v["url"], v["title"], v.get("description") or v["excerpt"], body, alt, image=p.get("cover"), active="trips",
                           og=og, scripts=scripts, body_class="post" + (" has-route" if route else "")))


def page_map(lang, trips):
    t = T[lang]
    P = PATHS[lang]
    lines, tracks = [], []
    for x in trips:
        if x.get("acts"):
            tracks.append({"src": tracks_url(x), "color": x["color"]})
        else:
            lines += trip_lines(x)
    legend = "".join(f'<a href="{trip_url(x, lang)}" style="color:var(--ink);text-decoration:none"><i style="background:{x["color"]}"></i>{trip_flags(x, 12)} {esc(x["title"][lang])}</a>' for x in trips)
    body = f"""<section class="wrap post-head"><p class="kicker">{t['map_kicker']}</p><h1>{t['map_page_title']}</h1>
<p style="margin:0;font-size:19px;color:var(--ink-soft)">{t['map_aside']}</p></section>
<div class="wrap">{map_div({"points": all_points(trips, lang), "lines": lines, "tracks": tracks, "fit": "points"}, "map tall", t['map_page_title'])}
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
        lis = "".join(f'<li><a href="{V(p, lang)["url"]}" lang="{post_lang(p, lang)}">{esc(V(p, lang)["title"])}</a>{fr_note(p, lang)}<span>{esc(fdate(p["dt"], lang))}'
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


FEED = {"fr": "/feed.xml", "en": "/en/feed.xml"}


def feeds(posts, trips):
    latest = sorted(posts, key=lambda p: p["dt"], reverse=True)[:20]
    for lang in ("fr", "en"):
        items = ""
        for p in latest:
            v = p["en"] if lang == "en" and p.get("en") else p
            cover = media(p.get("cover"), 1200)
            if cover.startswith("/"):
                cover = SITE_URL + cover
            items += f"""<item><title>{esc(v['title'])}</title><link>{SITE_URL}{v['url']}</link><guid>{SITE_URL}{v['url']}</guid>
<pubDate>{p['dt'].strftime('%a, %d %b %Y %H:%M:%S')} +0000</pubDate><description>{esc(v['excerpt'])}</description>
{f'<enclosure url="{esc(cover)}" type="image/jpeg" length="0"/>' if cover else ''}</item>"""
        desc = "Carnets de voyage, à vélo et en famille." if lang == "fr" else "Travel journals, by bike and as a family."
        home = "/" if lang == "fr" else "/en/"
        rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>The Quiet Adventure</title><link>{SITE_URL}{home}</link>
<description>{desc}</description><language>{lang}</language>{items}</channel></rss>"""
        os.makedirs(os.path.join(OUT, home.strip("/")), exist_ok=True)
        with open(os.path.join(OUT, home.strip("/"), "feed.xml"), "w", encoding="utf-8") as f:
            f.write(rss)
    urls = []
    for lang in ("fr", "en"):
        urls += list(PATHS[lang].values())
        urls += [trip_url(x, lang) for x in trips]
    urls += [p["url"] for p in posts] + [p["en"]["url"] for p in posts if p.get("en")]
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sm += "".join(f"<url><loc>{SITE_URL}{u}</loc></url>\n" for u in urls) + "</urlset>\n"
    with open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sm)
    with open(os.path.join(OUT, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")


OLD_CATEGORIES = {
    "asia": "/voyages/", "europe": "/voyages/", "north-america": "/voyages/", "oceania": "/voyages/", "south-america": "/voyages/colombie/",
    "road-trips": "/voyages/", "vie-quotidienne": "/voyages/", "africa": "/voyages/", "non-categorise": "/archives/",
    "asia/china": "/voyages/australie/", "asia/indonesie": "/voyages/bali/", "asia/japan": "/voyages/kyushu-a-velo/", "asia/malaisia": "/voyages/",
    "asia/philippines": "/voyages/philippines/", "asia/south-korea": "/voyages/coree-a-velo/", "asia/sri-lanka": "/voyages/sri-lanka/",
    "asia/south-korea/east-coast": "/voyages/coree-a-velo/", "asia/south-korea/jeju-island": "/voyages/coree-a-velo/",
    "asia/south-korea/seomjingang": "/voyages/coree-a-velo/", "asia/south-korea/seoul-to-busan": "/voyages/coree-a-velo/",
    "asia/south-korea/yeongsangang": "/voyages/coree-a-velo/",
    "europe/croatie": "/voyages/retour-en-europe-a-velo/", "europe/france": "/voyages/", "europe/france/voyages-a-velo": "/voyages/",
    "europe/italie": "/voyages/retour-en-europe-a-velo/", "europe/montenegro": "/voyages/montenegro/", "europe/slovenie": "/voyages/retour-en-europe-a-velo/",
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
    assign_strava(trips)
    chrono = sorted(trips, key=lambda x: x["start"])
    for a, b in zip(chrono, chrono[1:]):
        a["next_trip"] = b
    for p in posts:
        URL_BY_SLUG[p["url"].rstrip("/").split("/")[-1]] = p
    DZ.collect_days(posts)
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
        page_post(p, "fr")
        if p.get("en"):
            page_post(p, "en")
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
    write_tracks(trips)
    for lang in ("fr", "en"):
        VT.search_index(posts, lang)
        VT.page_passport(lang, posts)
        DZ.pages_countries(posts, lang)
    redirect("/labs/", "/")
    redirect("/voyages/escapades/", "/voyages/")  # scindé en Sri Lanka, Philippines, Monténégro
    redirect("/en/journeys/short-trips/", "/en/journeys/")
    redirect("/voyages/echappees-a-velo-en-france/", "/voyages/")  # voyage scindé en trois
    redirect("/en/journeys/cycling-getaways-in-france/", "/en/journeys/")
    VT.save_lqip()
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
