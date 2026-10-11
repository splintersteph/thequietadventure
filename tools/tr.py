"""Outil de traduction des récits.

  python tools/tr.py extract <stem>...      -> affiche les segments à traduire (T| titre, D| description, n| paragraphe)
  python tools/tr.py apply <fichier.txt>    -> écrit content/posts-en/<stem>.html depuis un fichier de traductions
  python tools/tr.py todo                   -> liste les récits pas encore traduits (du plus récent au plus ancien)

Le fichier de traductions reprend le même format :  ### <stem>  puis une ligne par segment.
Les jetons ⟦n⟧ (photos, vidéos…) doivent être conservés tels quels.
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "content", "posts")
DST = os.path.join(ROOT, "content", "posts-en")
BLOCK = re.compile(r"<(p|h[1-6]|li|figcaption|blockquote)(\s[^>]*)?>(.*?)</\1>", re.S)
EMBED = re.compile(r"<(?:img|iframe|video)\b[^>]*?(?:/>|>(?:</(?:iframe|video)>)?)|<br\s*/?>", re.S)


def stem_path(stem):
    m = glob.glob(os.path.join(SRC, f"*-{stem}.html")) or glob.glob(os.path.join(SRC, f"{stem}.html"))
    assert len(m) == 1, (stem, m)
    return m[0]


def stem_of(path):
    return re.sub(r"^\d{4}-\d\d-\d\d-", "", os.path.basename(path)[:-5])


def parse(path):
    raw = open(path, encoding="utf-8").read()
    m = re.match(r"\s*<!--\s*(\{.*?\})\s*-->\s*", raw, re.S)
    return json.loads(m.group(1)), raw[m.end():]


def segments(body):
    """Yield (start, end, text_with_tokens, embeds) for every block that holds text."""
    out = []
    for m in BLOCK.finditer(body):
        inner = m.group(3)
        if m.group(1) == "blockquote" and "<p" in inner:
            continue
        embeds = []

        def tok(e):
            embeds.append(e.group(0))
            return f"⟦{len(embeds) - 1}⟧"
        txt = EMBED.sub(tok, inner)
        if not re.sub(r"<[^>]+>|⟦\d+⟧|&nbsp;|\s", "", txt):
            continue
        txt = " ".join(txt.split())
        out.append((m.start(3), m.end(3), txt, embeds))
    return out


def extract(stems):
    for s in stems:
        h, body = parse(stem_path(s))
        print(f"### {s}")
        print("T|", h["title"])
        print("D|", h.get("description") or "")
        for i, (_a, _b, txt, _e) in enumerate(segments(body), 1):
            print(f"{i}|", txt)
        print()


def apply(fname):
    blocks = re.split(r"^### +(\S+)\s*$", open(fname, encoding="utf-8").read(), flags=re.M)
    for stem, chunk in zip(blocks[1::2], blocks[2::2]):
        path = stem_path(stem)
        h, body = parse(path)
        segs = segments(body)
        tr = {}
        for line in chunk.splitlines():
            m = re.match(r"^(T|D|\d+)\|\s?(.*)$", line)
            if m:
                tr[m.group(1)] = m.group(2).strip()
        missing = [str(i) for i in range(1, len(segs) + 1) if str(i) not in tr]
        if missing or "T" not in tr:
            print(f"!! {stem}: segments manquants {missing[:10]}")
            continue
        new, pos = [], 0
        for i, (a, b, txt, embeds) in enumerate(segs, 1):
            t = tr[str(i)]
            toks = re.findall(r"⟦(\d+)⟧", t)
            if sorted(toks) != sorted(str(k) for k in range(len(embeds))):
                print(f"!! {stem} segment {i}: jetons {toks} ≠ {len(embeds)}")
            t = re.sub(r"⟦(\d+)⟧", lambda m: embeds[int(m.group(1))], t)
            new.append(body[pos:a])
            new.append(t)
            pos = b
        new.append(body[pos:])
        head = {"title": tr["T"], "description": tr.get("D", ""), "source": os.path.basename(path)}
        with open(os.path.join(DST, os.path.basename(path)), "w", encoding="utf-8") as f:
            f.write("<!--\n" + json.dumps(head, ensure_ascii=False, indent=2) + "\n-->\n" + "".join(new))
        print("ok", stem, len(segs))


def todo():
    done = {os.path.basename(f) for f in glob.glob(os.path.join(DST, "*.html"))}
    rest = [f for f in sorted(glob.glob(os.path.join(SRC, "*.html")), reverse=True) if os.path.basename(f) not in done]
    for f in rest:
        _h, body = parse(f)
        print(stem_of(f), len(re.sub(r"<[^>]+>", " ", body).split()))
    print(len(rest), "à traduire")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "extract":
        extract(sys.argv[2:])
    elif cmd == "apply":
        for fn in sys.argv[2:]:
            apply(fn)
    else:
        todo()
