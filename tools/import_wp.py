#!/usr/bin/env python3
"""Import a WordPress export (WXR .xml) into content/posts/*.html.

Each post becomes one HTML file whose first lines are a JSON header inside an
HTML comment, followed by the cleaned article body. Also writes
data/media-manifest.json: every WordPress upload the content uses, so
tools/fetch_media.py can bring the files into media/.

Usage: python3 tools/import_wp.py path/to/export.xml
"""
import html
import json
import os
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NS = {
    "wp": "http://wordpress.org/export/1.2/",
    "content": "http://purl.org/rss/1.0/modules/content/",
}
UPLOAD_RE = re.compile(r"wp-content/uploads/([^?#\"'\s]+)")
MEDIA = {}  # local path -> source url


def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s[:80].strip("-") or "recit"


def local_media(url):
    """Map a WordPress upload URL to /media/<path>; register it for fetching."""
    if not url:
        return None
    url = html.unescape(url)
    m = UPLOAD_RE.search(url)
    if not m:
        return url if url.startswith("http") else None
    path = m.group(1)
    MEDIA["media/" + path] = "wp-content/uploads/" + path
    return "/media/" + path


class Cleaner(HTMLParser):
    KEEP = {"p", "h2", "h3", "h4", "h5", "ul", "ol", "li", "blockquote", "figure",
            "figcaption", "a", "strong", "em", "b", "i", "br", "hr", "table", "thead",
            "tbody", "tr", "td", "th", "cite", "sup", "sub", "code"}
    VOID = {"br", "hr", "img", "source"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.stack = []          # tags as opened (None = unwrapped)
        self.gallery = None      # list of images while inside a gallery
        self.gallery_depth = 0
        self.skip_depth = 0      # inside an element whose content is dropped

    # ---- helpers
    def emit(self, s):
        if self.skip_depth:
            return
        if self.gallery is not None:
            return
        self.out.append(s)

    def img_html(self, a):
        src = a.get("data-orig-file") or a.get("data-url") or a.get("src") or ""
        loc = local_media(src)
        if not loc:
            return ""
        alt = html.escape(a.get("alt") or "", quote=True)
        dims = ""
        size = a.get("data-orig-size") or ""
        m = re.match(r"(\d+),(\d+)", size)
        if not m and a.get("data-width") and a.get("data-height"):
            m = re.match(r"(\d+),(\d+)", a["data-width"] + "," + a["data-height"])
        if m:
            w, h = int(m.group(1)), int(m.group(2))
            if w > 1600:
                h, w = round(h * 1600 / w), 1600
            dims = f' width="{w}" height="{h}"'
        return f'<img src="{loc}" alt="{alt}"{dims} loading="lazy" decoding="async">'

    # ---- parser callbacks
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get("class") or ""
        if tag in self.VOID:
            if tag == "img":
                h = self.img_html(a)
                if self.gallery is not None:
                    if h:
                        self.gallery.append(h)
                else:
                    self.emit(h)
            elif tag in ("br", "hr"):
                self.emit(f"<{tag}>")
            return
        if self.skip_depth:
            self.skip_depth += 1
            self.stack.append(None)
            return
        if tag in ("script", "style", "noscript", "button", "svg"):
            self.skip_depth = 1
            self.stack.append(None)
            return
        if tag == "div" and ("tiled-gallery" in cls or "wp-block-gallery" in cls) and self.gallery is None:
            self.gallery = []
            self.gallery_depth = 1
            self.stack.append("__gallery")
            return
        if self.gallery is not None:
            self.gallery_depth += 1
            self.stack.append(None)
            return
        if tag == "figure" and "wp-block-gallery" in cls:
            self.gallery = []
            self.gallery_depth = 1
            self.stack.append("__gallery")
            return
        if tag == "div" and "strava-embed-placeholder" in cls:
            aid = a.get("data-embed-id")
            if aid:
                self.emit(f'<div class="strava" data-activity="{aid}"></div>')
            self.skip_depth = 1
            self.stack.append(None)
            return
        if tag == "video":
            src = local_media(a.get("src"))
            if src:
                self.emit(f'<video controls preload="metadata" playsinline src="{src}"></video>')
            self.skip_depth = 1
            self.stack.append(None)
            return
        if tag == "iframe":
            src = a.get("src") or ""
            if "komoot" in src or "youtube" in src or "vimeo" in src:
                self.emit(f'<iframe src="{html.escape(src, quote=True)}" loading="lazy" title="Carte de l\'itinéraire"></iframe>')
            self.skip_depth = 1
            self.stack.append(None)
            return
        if tag == "h1":
            tag = "h2"
        if tag == "h6":
            tag = "h5"
        if tag in self.KEEP:
            extra = ""
            if tag == "a":
                href = a.get("href") or ""
                if "strava-embeds.com" in href:
                    self.skip_depth = 1
                    self.stack.append(None)
                    return
                if "wp-content/uploads" in href:
                    href = local_media(href) or href
                href = re.sub(r"^https?://(www\.)?thequietadventure\.com", "", href)
                extra = f' href="{html.escape(href, quote=True)}"'
                if href.startswith("http"):
                    extra += ' rel="noopener"'
            self.emit(f"<{tag}{extra}>")
            self.stack.append(tag)
        else:
            self.stack.append(None)  # unwrap

    def handle_endtag(self, tag):
        if tag in self.VOID:
            return
        if not self.stack:
            return
        top = self.stack.pop()
        if self.skip_depth:
            self.skip_depth -= 1
            return
        if top == "__gallery":
            imgs = self.gallery or []
            self.gallery = None
            if imgs:
                n = min(len(imgs), 3)
                self.out.append(f'<div class="gallery g{n}">' + "".join(imgs) + "</div>")
            return
        if self.gallery is not None:
            self.gallery_depth -= 1
            return
        if top:
            self.emit(f"</{top}>")

    def handle_data(self, data):
        if self.gallery is not None:
            return
        self.emit(html.escape(data, quote=False))


def clean(body):
    # videopress blocks carry their mp4 in JSON
    def vp(m):
        js = m.group(1)
        src = re.search(r'"src":"([^"]+)"', js)
        return f'<video src="{src.group(1)}"></video>' if src else ""
    body = re.sub(r"<!-- wp:videopress/video (\{.*?\}) /?-->.*?(<!-- /wp:videopress/video -->|$)", vp, body, flags=re.S)
    body = re.sub(r"<!-- wp:(table-of-contents|a8c/blog-posts).*?<!-- /wp:\1 -->", "", body, flags=re.S)
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    c = Cleaner()
    c.feed(body)
    c.close()
    out = "".join(c.out)
    out = re.sub(r"<p>\s*</p>", "", out)
    out = re.sub(r"<(strong|em|b|i)>\s*</\1>", "", out)
    out = re.sub(r"\s*\n\s*", "\n", out)
    out = re.sub(r"(</(p|h2|h3|h4|h5|ul|ol|blockquote|figure|div)>)(?!\n)", r"\1\n", out)
    return out.strip()


def text_excerpt(body, n=40):
    t = re.sub(r"<[^>]+>", " ", body)
    t = html.unescape(re.sub(r"\s+", " ", t)).strip()
    words = t.split(" ")
    return " ".join(words[:n]) + ("…" if len(words) > n else "")


def main(xml_path):
    ch = ET.parse(xml_path).getroot().find("channel")
    items = ch.findall("item")
    attachments = {}
    for i in items:
        if i.find("wp:post_type", NS).text == "attachment":
            attachments[i.find("wp:post_id", NS).text] = i.find("wp:attachment_url", NS).text

    out_dir = os.path.join(ROOT, "content", "posts")
    os.makedirs(out_dir, exist_ok=True)
    used_slugs = set()
    n = 0
    for i in items:
        if i.find("wp:post_type", NS).text != "post" or i.find("wp:status", NS).text != "publish":
            continue
        title = html.unescape(i.find("title").text or "").strip()
        wp_slug = i.find("wp:post_name", NS).text or ""
        if wp_slug == "hello-world":
            continue
        date = i.find("wp:post_date", NS).text
        link = i.find("link").text or ""
        old_path = re.sub(r"^https?://[^/]+", "", link)
        meta = {}
        for m in i.findall("wp:postmeta", NS):
            meta[m.find("wp:meta_key", NS).text] = m.find("wp:meta_value", NS).text or ""
        slug = wp_slug if not wp_slug.isdigit() else slugify(title)
        base = slug
        k = 2
        while slug in used_slugs:
            slug = f"{base}-{k}"
            k += 1
        used_slugs.add(slug)

        raw = i.find("content:encoded", NS).text or ""
        stravas = re.findall(r'data-embed-id="(\d+)"', raw)
        body = clean(raw)
        cats = [c.get("nicename") for c in i.findall("category") if c.get("domain") == "category"]
        tags = [html.unescape(c.text or "") for c in i.findall("category") if c.get("domain") == "post_tag"]
        cover = None
        tid = meta.get("_thumbnail_id")
        if tid and tid in attachments:
            cover = local_media(attachments[tid])
        if not cover:
            m = re.search(r'<img src="([^"]+)"', body)
            cover = m.group(1) if m else None
        geo = None
        g = meta.get("_mks_map_geolocation_data", "")
        lat = re.search(r'"latitude";s:\d+:"(-?[\d.]+)"', g)
        lng = re.search(r'"longitude";s:\d+:"(-?[\d.]+)"', g)
        if lat and lng:
            geo = [round(float(lat.group(1)), 5), round(float(lng.group(1)), 5)]
        desc = meta.get("advanced_seo_description") or text_excerpt(body, 32)
        header = {
            "title": title,
            "date": date,
            "slug": slug,
            "url": old_path if old_path.endswith("/") else old_path + "/",
            "categories": cats,
            "tags": tags,
            "cover": cover,
            "description": desc,
            "geo": geo,
            "strava": stravas,
            "lang": "fr",
        }
        fn = f"{date[:10]}-{slug}.html"
        with open(os.path.join(out_dir, fn), "w", encoding="utf-8") as f:
            f.write("<!--\n" + json.dumps(header, ensure_ascii=False, indent=2) + "\n-->\n")
            f.write(body + "\n")
        n += 1

    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    with open(os.path.join(ROOT, "data", "media-manifest.json"), "w", encoding="utf-8") as f:
        json.dump(dict(sorted(MEDIA.items())), f, ensure_ascii=False, indent=0)
    print(f"{n} récits importés, {len(MEDIA)} médias référencés")


if __name__ == "__main__":
    main(sys.argv[1])
