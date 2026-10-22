#!/usr/bin/env python3
"""Credit-aware daily pin loop.

Picks the next N items from a round-robin queue so all five categories are
covered inside a week, downloads each product photo from Amazon's image CDN,
and composites a 1000x1500 pin with pin_factory. Costs ZERO image-generation
credits — it is deterministic layout over a real product photo.

    python3 daily.py --plan            # show what today's rotation would be
    python3 daily.py --run             # render them
    python3 daily.py --status          # queue position and what is missing

A queued item needs `asin` filled in. `image_url` is derived from the ASIN, so
pasting an ASIN (or a full /dp/ URL, which is parsed for the ASIN) is the only
manual input the loop needs.
"""
import argparse
import json
import os
import re
import shutil
import sys
import urllib.request
from datetime import date, datetime, timezone

import pin_factory

BASE = os.path.dirname(os.path.abspath(__file__))
QUEUE = os.path.join(BASE, "content", "queue.json")
PINS = os.path.join(BASE, "pins")
CACHE = os.path.join(BASE, "content", "imgcache")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/121.0 Safari/537.36")
IMG_SUFFIXES = ["_SL1500_", "_SL1200_", "_SL1000_", "_SCLZZZZZZZ_"]


def load():
    with open(QUEUE) as f:
        return json.load(f)


def save(q):
    tmp = QUEUE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(q, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, QUEUE)


def normalise_asin(v):
    """Accept an ASIN or any Amazon URL containing one."""
    if not v:
        return ""
    v = v.strip()
    m = re.search(r"/(?:dp|gp/product)/([A-Z0-9]{10})", v)
    if m:
        return m.group(1)
    m = re.search(r"^([A-Z0-9]{10})$", v.upper())
    return m.group(1) if m else ""


def next_batch(q, n):
    """Round-robin across categories so every category lands inside a week."""
    order = q["order"]
    items = q["items"]
    by_cat = {c: [i for i in items if i["cat"] == c and i.get("status", "queued") == "queued"]
              for c in order}
    cursor = q["state"].get("cursor", 0) % len(order)
    picked = []
    guard = 0
    while len(picked) < n and guard < len(order) * 4:
        cat = order[cursor % len(order)]
        if by_cat[cat]:
            picked.append(by_cat[cat].pop(0))
        cursor += 1
        guard += 1
        if all(not v for v in by_cat.values()):
            break
    return picked, cursor % len(order)


def fetch_image(asin, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    last = None
    for sfx in IMG_SUFFIXES:
        url = f"https://m.media-amazon.com/images/P/{asin}.01.{sfx}.jpg"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=25) as r:
                data = r.read()
            if len(data) < 4000:
                last = f"{sfx}: too small ({len(data)}b)"
                continue
            with open(dest, "wb") as f:
                f.write(data)
            return dest, url
        except Exception as e:
            last = f"{sfx}: {e}"
    raise RuntimeError(f"no image for {asin} ({last})")


def run(per_day=None, do_render=True):
    q = load()
    n = per_day or q.get("per_day", 3)
    batch, new_cursor = next_batch(q, n)
    today = date.today().isoformat()
    out = {"date": today, "batch": [], "skipped": []}

    if not batch:
        out["note"] = "queue is empty — add ASINs to content/queue.json"
        return out

    for it in batch:
        asin = normalise_asin(it.get("asin", ""))
        if not asin:
            it["status"] = "needs_asin"
            out["skipped"].append({"id": it["id"], "reason": "no asin"})
            continue
        it["asin"] = asin
        img = os.path.join(CACHE, f"{asin}.jpg")
        try:
            if not os.path.exists(img):
                _, src = fetch_image(asin, img)
                it["image_source"] = src
        except Exception as e:
            out["skipped"].append({"id": it["id"], "reason": str(e)})
            continue
        pin_name = f"{it['id']}.png"
        if do_render:
            pin_factory.compose(
                img, os.path.join(PINS, pin_name),
                kicker=dict(zip(q["order"], ["Home Organisation", "Pet Enrichment",
                                             "Kitchen & Air Fryer", "Home Fitness",
                                             "Sleep & Comfort"]))[it["cat"]],
                headline=it["headline"], price=it.get("price", ""),
                badge=it.get("badge", ""), sub=it.get("sub", ""),
                brand=q["brand"])
        it["pin"] = pin_name
        it["status"] = "rendered" if do_render else "planned"
        it["rendered_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        it["link"] = f"https://www.amazon.com/dp/{asin}?tag={q['tag']}"
        out["batch"].append(it)

    if do_render:
        q["state"]["cursor"] = new_cursor
        q["state"]["runs"].append({"date": today, "ids": [b["id"] for b in out["batch"]]})
        save(q)
    # keep out/pins in sync with pins/
    dst = os.path.join(BASE, "out", "pins")
    os.makedirs(dst, exist_ok=True)
    for f in os.listdir(PINS):
        shutil.copy2(os.path.join(PINS, f), os.path.join(dst, f))
    return out


def todays_pack(n=None):
    """Next N ready-but-unposted pins, marked posted so a wake never repeats one."""
    q = load()
    n = n or q.get("per_day", 3)
    ready = [i for i in q["items"]
             if i.get("status") == "rendered" and not i.get("posted_at")]
    # queue order is already round-robin across categories — never re-sort it
    batch = ready[:n]
    pack = []
    for it in batch:
        it["posted_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        pack.append({"id": it["id"], "cat": it["cat"], "headline": it["headline"],
                     "sub": it.get("sub", ""), "price": it.get("price", ""),
                     "pin": it["pin"], "link": it.get("link", ""),
                     "product": it.get("product", "")})
    save(q)
    left = sum(1 for i in q["items"]
               if i.get("status") == "rendered" and not i.get("posted_at"))
    queued = sum(1 for i in q["items"] if i.get("status", "queued") == "queued")
    return {"date": date.today().isoformat(), "pack": pack,
            "ready_left": left, "queued_left": queued,
            "refill_soon": left < 4 or queued < 4}


def status():
    q = load()
    from collections import Counter
    c = Counter(i.get("status", "queued") for i in q["items"])
    per = Counter(i["cat"] for i in q["items"]
                  if i.get("status", "queued") == "queued")
    nd = q.get("per_day", 3)
    days = -(-sum(per.values()) // nd) if per else 0
    return {"counts": dict(c), "queued_per_category": dict(per),
            "days_of_content_left": days, "cursor": q["state"].get("cursor", 0)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--post", action="store_true")
    ap.add_argument("--n", type=int, default=None)
    a = ap.parse_args()
    if a.status:
        print(json.dumps(status(), indent=2)); return
    if a.post:
        print(json.dumps(todays_pack(a.n), indent=2)); return
    if a.plan:
        q = load(); b, _ = next_batch(q, a.n or q.get("per_day", 3))
        print(json.dumps({"date": date.today().isoformat(),
                          "planned": [{"id": i["id"], "cat": i["cat"],
                                       "headline": i["headline"],
                                       "needs_asin": not normalise_asin(i.get("asin", ""))}
                                      for i in b]}, indent=2)); return
    print(json.dumps(run(a.n), indent=2))


if __name__ == "__main__":
    main()
