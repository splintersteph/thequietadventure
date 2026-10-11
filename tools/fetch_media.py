#!/usr/bin/env python3
"""Bring every photo and video used by the stories into media/.

Reads data/media-manifest.json (written by import_wp.py) and downloads each
missing file from the WordPress site. Photos are fetched resized to 1600 px
through the WordPress image CDN; videos are fetched as-is and, when ffmpeg is
available, re-encoded to 720p to keep the repository small.

Must run while thequietadventure.com still points to WordPress.
"""
import concurrent.futures as cf
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CDN = "https://i0.wp.com/thequietadventure.com/"
ORIGIN = "https://thequietadventure.com/"
UA = {"User-Agent": "Mozilla/5.0 (thequietadventure migration)"}


def get(url, dest):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r, open(dest + ".part", "wb") as f:
        shutil.copyfileobj(r, f)
    if os.path.getsize(dest + ".part") < 200:
        raise IOError("fichier vide")
    os.replace(dest + ".part", dest)


def shrink(path, max_side=1600):
    """Resize big originals so the repository stays light."""
    try:
        from PIL import Image, ImageOps
        Image.MAX_IMAGE_PIXELS = None
    except ImportError:
        return
    try:
        _shrink(path, max_side, Image, ImageOps)
    except Exception as e:  # noqa: BLE001
        print("  redimensionnement impossible :", path, e)


def _shrink(path, max_side, Image, ImageOps):
    with Image.open(path) as im:
        if max(im.size) <= max_side:
            return
        im = ImageOps.exif_transpose(im)
        im.thumbnail((max_side, max_side))
        if path.lower().endswith((".jpg", ".jpeg")):
            im.convert("RGB").save(path, quality=80, optimize=True, progressive=True)
        else:
            im.save(path, optimize=True)


def fetch(item):
    try:
        return _fetch(item)
    except Exception as e:  # noqa: BLE001
        return item[0], "FAIL " + repr(e)


def _fetch(item):
    local, src = item
    dest = os.path.join(ROOT, local)
    if os.path.exists(dest):
        if not local.lower().endswith((".mp4", ".mov", ".webm")):
            shrink(dest)
        return local, "ok"
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    is_video = local.lower().endswith((".mp4", ".mov", ".webm"))
    urls = [ORIGIN + src] if is_video else [ORIGIN + src, CDN + src + "?w=1600&quality=80&strip=info"]
    for attempt in range(3):
        for url in urls:
            try:
                get(url, dest)
                if not is_video:
                    shrink(dest)
                if is_video and shutil.which("ffmpeg"):
                    tmp = dest + ".720.mp4"
                    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", dest, "-vf", "scale='min(1280,iw)':-2",
                                    "-c:v", "libx264", "-crf", "28", "-preset", "veryfast", "-c:a", "aac", "-b:a", "96k",
                                    "-movflags", "+faststart", tmp], check=True)
                    os.replace(tmp, dest)
                return local, "new"
            except Exception as e:  # noqa: BLE001
                err = repr(e)
        time.sleep(2 * (attempt + 1))
    return local, "FAIL " + err



def main():
    err = ""
    manifest = json.load(open(os.path.join(ROOT, "data", "media-manifest.json"), encoding="utf-8"))
    # files from an earlier run that no story uses any more
    for dirpath, _, files in os.walk(os.path.join(ROOT, "media")):
        for fn in files:
            rel = os.path.relpath(os.path.join(dirpath, fn), ROOT).replace(os.sep, "/")
            if rel not in manifest:
                os.remove(os.path.join(dirpath, fn))
    todo = list(manifest.items())
    print(f"{len(todo)} médias à vérifier")
    fails, new = [], 0
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        for i, (local, status) in enumerate(ex.map(fetch, todo), 1):
            if status == "new":
                new += 1
            elif status.startswith("FAIL"):
                fails.append(f"{local}\t{status}")
            if i % 100 == 0:
                print(f"  {i}/{len(todo)}")
    with open(os.path.join(ROOT, "data", "media-missing.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(fails) + ("\n" if fails else ""))
    print(f"{new} nouveaux fichiers, {len(fails)} échecs (voir data/media-missing.txt)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
