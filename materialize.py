#!/usr/bin/env python3
"""Download product photos and compose every queued pin."""
import json, os, re, urllib.request
from urllib.parse import quote_plus
import pin_factory

BASE = os.path.dirname(os.path.abspath(__file__))
QUEUE = os.path.join(BASE, "content", "queue.json")
FOUND = os.path.join(BASE, "content", "amz", "found.json")
PINS = os.path.join(BASE, "pins")
CACHE = os.path.join(BASE, "content", "imgcache")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/121.0 Safari/537.36")
KICK = {"home-organization": "Home Organisation", "pet-enrichment": "Pet Enrichment",
        "kitchen-air-fryer": "Kitchen & Air Fryer", "home-fitness": "Home Fitness",
        "sleep-comfort": "Sleep & Comfort"}


def main():
    q = json.load(open(QUEUE))
    found = json.load(open(FOUND))
    os.makedirs(CACHE, exist_ok=True)
    tag = q["tag"]
    done = 0
    for it in q["items"]:
        f = found.get(it["id"])
        if not f:
            print(f"{it['id']}: no listing found"); continue
        img_path = os.path.join(CACHE, f"{it['id']}.jpg")
        if not os.path.exists(img_path):
            url = f["img"].replace("?width=1024", "?width=1024")
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=40) as r:
                open(img_path, "wb").write(r.read())
        # affiliate link: tagged Amazon search keyed to the exact product title
        words = " ".join(f["title"].split()[:9])
        it["asin"] = ""                      # not exposed by the crawler
        it["product"] = f["title"][:120]
        it["image_source"] = f["img"]
        it["link"] = f"https://www.amazon.com/s?k={quote_plus(words)}&tag={tag}"
        it["pin"] = f"{it['id']}.png"
        price_full = it.get("price", "")
        price_short = price_full.split("·")[-1].strip() if "·" in price_full else price_full
        pin_factory.compose(img_path, os.path.join(PINS, it["pin"]),
                            kicker=KICK[it["cat"]], headline=it["headline"],
                            price=price_short, badge=it.get("badge", ""),
                            sub=it.get("sub", ""), brand=q["brand"])
        it["status"] = "rendered"
        done += 1
        print(f"{it['id']}: {it['pin']}  <- {f['title'][:60]}")
    json.dump(q, open(QUEUE, "w"), indent=2, ensure_ascii=False)
    # sync to the served folder
    import shutil
    dst = os.path.join(BASE, "out", "pins"); os.makedirs(dst, exist_ok=True)
    for fn in os.listdir(PINS):
        shutil.copy2(os.path.join(PINS, fn), os.path.join(dst, fn))
    print(f"\ncomposed {done} pins")


if __name__ == "__main__":
    main()
