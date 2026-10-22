#!/usr/bin/env python3
"""Find real Amazon US listings (product title + product photo) via gsk crawler."""
import json, re, subprocess, sys, os

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "content", "amz", "found.json")
QUERIES = [
    ("ho-1",  "clear stackable storage bins set of 6", "storage bins"),
    ("ho-2",  "clear pantry containers set airtight", "pantry containers"),
    ("ho-3",  "under bed storage bags zippered", "under bed storage"),
    ("ho-4",  "hanging closet organizer storage", "closet organizer"),
    ("pe-1",  "snuffle mat for dogs", "snuffle mat"),
    ("pe-2",  "cat water fountain stainless steel", "fountain"),
    ("pe-3",  "calming dog bed donut fluffy", "dog bed"),
    ("pe-4",  "lick mat slow feeder dog", "lick mat"),
    ("kit-1", "6 quart air fryer", "air fryer"),
    ("kit-2", "glass meal prep containers set", "meal prep containers"),
    ("kit-3", "air fryer parchment liners disposable", "air fryer liners"),
    ("kit-4", "immersion blender hand blender", "immersion blender"),
    ("fit-1", "walking pad treadmill under desk", "walking pad"),
    ("fit-2", "kitchen floor mat cushioned anti fatigue", "mat"),
    ("fit-3", "pilates ring yoga mat set", "pilates ring"),
    ("fit-4", "adjustable dumbbells set", "dumbbells"),
    ("slp-1", "cooling gel mattress topper", "mattress topper"),
    ("slp-2", "blackout curtains bedroom 100 percent", "blackout curtains"),
    ("slp-3", "memory foam contour pillow neck pain", "pillow"),
    ("slp-4", "white noise machine sleep", "white noise machine"),
]

ENTRY = re.compile(r'!\[(?P<title>[^\]]{20,300})\]\((?P<img>https://sspark\.genspark\.ai/i/[A-Za-z0-9]+)[^)]*\)', re.S)


def crawl(query):
    url = f"https://www.amazon.com/s?k={query.replace(' ', '+')}"
    p = subprocess.run(["gsk", "crawler", url], capture_output=True, text=True, timeout=200)
    d = json.loads(p.stdout)
    if d.get("status") != "ok":
        raise RuntimeError(d.get("message"))
    return d["data"]["result"]


def parse(md, must):
    best, best_score = None, 0
    for m in ENTRY.finditer(md):
        t = re.sub(r"\s+", " ", m.group("title")).strip()
        low = t.lower()
        if "shop the" in low or "store on amazon" in low or len(t) < 38:
            continue
        score = sum(1 for w in must.split() if w in low)
        if score > best_score:
            best_score, best = score, {"title": t[:170], "img": m.group("img")}
    return best if best_score >= len(must.split()) - 1 else None


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    res = json.load(open(OUT)) if os.path.exists(OUT) else {}
    only = set(sys.argv[1:]) or None
    for pid, q, must in QUERIES:
        if only and pid not in only:
            continue
        try:
            md = crawl(q)
            best = parse(md, must)
            if best:
                res[pid] = {"query": q, **best}
                print(f"{pid}: {best['title'][:78]}")
            else:
                print(f"{pid}: NO MATCH")
        except Exception as e:
            print(f"{pid}: FAIL {e}")
        json.dump(res, open(OUT, "w"), indent=2)
    print(f"\n{len(res)}/20")


if __name__ == "__main__":
    main()
