#!/usr/bin/env python3
"""Extract ASINs straight from the crawler's markdown links (pd_rd_i / /dp/)."""
import json, re, subprocess, sys, os
BASE = os.path.dirname(os.path.abspath(__file__))
QUEUE = os.path.join(BASE, "content", "queue.json")
OUT = os.path.join(BASE, "content", "amz", "asins.json")

LINK = re.compile(r'\]\((https?://[^)\s]*(?:pd_rd_i=|/dp/)([A-Z0-9]{10})[^)\s]*)\)')
TITLE = re.compile(r'!\[([^\]]{20,300})\]')


def crawl(q):
    url = "https://www.amazon.com/s?k=" + re.sub(r"[^A-Za-z0-9 ]", " ", q).replace(" ", "+")[:180]
    p = subprocess.run(["gsk", "crawler", url], capture_output=True, text=True, timeout=240)
    d = json.loads(p.stdout)
    if d.get("status") != "ok":
        raise RuntimeError(d.get("message"))
    return d["data"]["result"]


def best(md, title):
    tw = {w.lower() for w in re.findall(r"\w+", title) if len(w) > 3}
    scored = {}
    # walk titles and links in document order, associate each link with the nearest prior title
    events = [(m.start(), "t", m.group(1)) for m in TITLE.finditer(md)]
    events += [(m.start(), "l", m.group(2)) for m in LINK.finditer(md)]
    events.sort()
    cur = ""
    for _, kind, val in events:
        if kind == "t":
            cur = val
        else:
            if not re.match(r"^B0[A-Z0-9]{8}$", val):
                continue
            cw = {w.lower() for w in re.findall(r"\w+", cur) if len(w) > 3}
            s = len(tw & cw)
            if s > scored.get(val, (-1, ""))[0]:
                scored[val] = (s, cur)
    if not scored:
        return None, 0
    asin, (s, t) = max(scored.items(), key=lambda kv: kv[1][0])
    return asin, s


def main():
    q = json.load(open(QUEUE))
    res = json.load(open(OUT)) if os.path.exists(OUT) else {}
    only = set(sys.argv[1:]) or None
    for it in q["items"]:
        if only and it["id"] not in only:
            continue
        if it["id"] in res and res[it["id"]].get("score", 0) >= 3:
            continue
        try:
            md = crawl(it["product"])
            a, s = best(md, it["product"])
            if a and s >= 3:
                res[it["id"]] = {"asin": a, "score": s}
                print(f"{it['id']}: {a} (score {s})")
            else:
                print(f"{it['id']}: weak/none ({a}, {s})")
        except Exception as e:
            print(f"{it['id']}: FAIL {e}")
        json.dump(res, open(OUT, "w"), indent=2)
    print(f"\nresolved {len(res)}/20")


if __name__ == "__main__":
    main()
