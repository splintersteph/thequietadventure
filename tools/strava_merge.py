"""Fusionne des exports Strava (list_activities avec polylignes) dans data/strava/activities.json.

Usage : python tools/strava_merge.py export1.json export2.json …
Seuls les sorties vélo et randonnées avec une trace sont gardées. Les 300 premiers et
derniers mètres de chaque trace sont retirés pour ne pas indiquer de lieu de départ précis.
"""
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "strava", "activities.json")
KEEP = ("Ride", "Hike")


def decode(s):
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
        pts.append((lat, lng))
    return pts


def encode(pts):
    out, plat, plng = [], 0, 0
    for lat, lng in pts:
        for v in (lat - plat, lng - plng):
            v = ~(v << 1) if v < 0 else v << 1
            while v >= 0x20:
                out.append(chr((0x20 | (v & 0x1F)) + 63))
                v >>= 5
            out.append(chr(v + 63))
        plat, plng = lat, lng
    return "".join(out)


def dist(a, b):
    la1, lo1, la2, lo2 = (math.radians(x / 1e5) for x in (*a, *b))
    x = (lo2 - lo1) * math.cos((la1 + la2) / 2)
    return 6371000 * math.hypot(x, la2 - la1)


def trim(pts, m=300):
    def cut(seq):
        acc = 0
        for i in range(1, len(seq)):
            acc += dist(seq[i - 1], seq[i])
            if acc >= m:
                return seq[i:]
        return []
    pts = cut(pts)
    return cut(pts[::-1])[::-1]


def main(files):
    acts = {}
    if os.path.exists(OUT):
        acts = {a["id"]: a for a in json.load(open(OUT, encoding="utf-8"))}
    for f in files:
        for a in json.load(open(f, encoding="utf-8"))["activities"]:
            if not any(k in a["sport_type"] for k in KEEP) or not a.get("reduced_polyline"):
                continue
            pts = trim(decode(a["reduced_polyline"]))
            if len(pts) < 2:
                continue
            s = a["summary"]
            acts[a["id"]] = {
                "id": a["id"], "date": a["start_local"], "type": a["sport_type"], "name": a["name"],
                "place": a.get("location_summary") or "", "dist": round(s.get("distance") or 0),
                "elev": round(s.get("elevation_gain") or 0), "time": s.get("moving_time") or 0,
                "poly": encode(pts),
            }
    out = sorted(acts.values(), key=lambda a: a["date"])
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("[\n" + ",\n".join(json.dumps(a, ensure_ascii=False) for a in out) + "\n]\n")
    print(len(out), "activités")


if __name__ == "__main__":
    main(sys.argv[1:])
