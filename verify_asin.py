#!/usr/bin/env python3
"""Confirm a candidate ASIN really is the product: crawl /dp/<ASIN> and compare titles."""
import json, re, subprocess, os
BASE = os.path.dirname(os.path.abspath(__file__))
ASINS = os.path.join(BASE, "content", "amz", "asins.json")
QUEUE = os.path.join(BASE, "content", "queue.json")

def crawl(url):
    p = subprocess.run(["gsk", "crawler", url], capture_output=True, text=True, timeout=240)
    d = json.loads(p.stdout)
    return d["data"]["result"] if d.get("status") == "ok" else ""

q = {i["id"]: i for i in json.load(open(QUEUE))["items"]}
res = json.load(open(ASINS))
ok = {}
for pid, info in res.items():
    asin = info["asin"]
    it = q.get(pid)
    if not it:
        continue
    md = crawl(f"https://www.amazon.com/dp/{asin}")
    tw = {w.lower() for w in re.findall(r"\w+", it["product"]) if len(w) > 4}
    found = {w for w in tw if w in md.lower()}
    ratio = len(found) / max(len(tw), 1)
    verdict = "OK" if ratio >= 0.5 else "REJECT"
    print(f"{pid} {asin} ratio={ratio:.2f} {verdict}")
    if verdict == "OK":
        ok[pid] = {"asin": asin, "ratio": round(ratio, 2)}
json.dump(ok, open(os.path.join(BASE, "content", "amz", "verified.json"), "w"), indent=2)
print(f"\nverified {len(ok)}/{len(res)}")
