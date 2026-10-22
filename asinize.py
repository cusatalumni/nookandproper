#!/usr/bin/env python3
"""Resolve real /dp/ ASINs for each queued product via gsk summarizer."""
import json, re, subprocess, sys, os

BASE = os.path.dirname(os.path.abspath(__file__))
QUEUE = os.path.join(BASE, "content", "queue.json")
OUT = os.path.join(BASE, "content", "amz", "asins.json")
Q = ("This is an Amazon search results page. The product I want has the title: {title}. "
     "Reply with ONLY its 10-character ASIN (it starts with B0 and appears in a /dp/ link or a "
     "data-asin attribute next to that product). Reply NONE if that exact product is not on the page.")

PAIR = re.compile(r'([A-Z0-9]{10})\s*[:\-–]\s*(.{5,180})')
URLP = re.compile(r'/dp/([A-Z0-9]{10})')


def run(title):
    url = "https://www.amazon.com/s?k=" + re.sub(r"[^A-Za-z0-9 ]", " ", title).replace(" ", "+")[:180]
    p = subprocess.run(["gsk", "summarize_large_document", url, "--question", Q.replace("{title}", title[:110])],
                       capture_output=True, text=True, timeout=240)
    d = json.loads(p.stdout)
    if d.get("status") != "ok":
        raise RuntimeError(d.get("message"))
    return d["data"]["result"]


def pick(md, title):
    tw = {w.lower() for w in re.findall(r"\w+", title) if len(w) > 3}
    best, score = None, -1
    for asin, cand in PAIR.findall(md):
        if not re.match(r"^B0[A-Z0-9]{8}$", asin):   # ASINs, not model numbers
            continue
        cw = {w.lower() for w in re.findall(r"\w+", cand) if len(w) > 3}
        s = len(tw & cw)
        if s > score:
            score, best = s, asin
    if best is None:
        for u in URLP.findall(md):
            if re.match(r"^B0[A-Z0-9]{8}$", u):
                best = u
                break
    return best, score


def main():
    q = json.load(open(QUEUE))
    res = json.load(open(OUT)) if os.path.exists(OUT) else {}
    only = set(sys.argv[1:]) or None
    for it in q["items"]:
        if only and it["id"] not in only:
            continue
        if it.get("asin"):
            continue
        try:
            md = run(it["product"])
            asin, sc = pick(md, it["product"])
            if asin:
                res[it["id"]] = {"asin": asin, "score": sc}
                print(f"{it['id']}: {asin} (match score {sc})")
            else:
                print(f"{it['id']}: NONE")
        except Exception as e:
            print(f"{it['id']}: FAIL {e}")
        json.dump(res, open(OUT, "w"), indent=2)
    print(f"\nresolved {len(res)}")


if __name__ == "__main__":
    main()
