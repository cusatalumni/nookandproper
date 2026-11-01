#!/usr/bin/env python3
"""Turn the verified ASIN catalog + editorial copy into queued, rendered pins.

Reads  content/amz/catalog_asin.json   (fetch_products.py output: title/price/img)
       content/products_asin.json      (headline/sub/spec/body per ASIN)
Writes content/queue.json (appends, round-robin order across the five categories)
       pins/<id>.png            (1000x1500, composed locally — zero credits)

An ASIN is queued only if its page really resolved AND its photo cached, so a
dead or mismatched ASIN can never reach a pin.
"""
import json, os, sys
from PIL import Image
import pin_factory, daily

BASE = os.path.dirname(os.path.abspath(__file__))
CAT = os.path.join(BASE, "content", "amz", "catalog_asin.json")
ED = os.path.join(BASE, "content", "products_asin.json")
PINS = os.path.join(BASE, "pins")
ORDER = ["home-organization", "pet-enrichment", "kitchen-air-fryer",
         "home-fitness", "sleep-comfort"]
KICKER = {"home-organization": "Home Organisation", "pet-enrichment": "Pet Enrichment",
          "kitchen-air-fryer": "Kitchen & Air Fryer", "home-fitness": "Home Fitness",
          "sleep-comfort": "Sleep & Comfort"}


def main(render=True):
    cat = json.load(open(CAT))
    ed = json.load(open(ED))
    q = daily.load()
    have = {i.get("id") for i in q["items"]}
    have_asins = {i.get("asin") for i in q["items"] if i.get("asin")}

    by_cat, skipped = {c: [] for c in ORDER}, []
    for asin, e in ed.items():
        c = cat.get(asin) or {}
        if not c.get("ok") or not c.get("cached"):
            skipped.append((asin, "no live page / no photo")); continue
        if asin in have_asins:
            skipped.append((asin, "already queued")); continue
        if e["id"] in have:
            skipped.append((asin, f"id {e['id']} taken")); continue
        img = os.path.join(BASE, c["cached"]) if c["cached"] else ""
        if not img or not os.path.exists(img):
            skipped.append((asin, "image file missing")); continue
        try:
            w, h = Image.open(img).size
            if min(w, h) < 400:
                skipped.append((asin, f"photo too small {w}x{h}")); continue
        except Exception as ex:
            skipped.append((asin, f"unreadable image: {ex}")); continue
        by_cat[e["cat"]].append((asin, e, img))

    new = []
    # round-robin: one from each category per turn as long as any are left
    i = 0
    while any(by_cat[c] for c in ORDER):
        c = ORDER[i % len(ORDER)]
        i += 1
        if not by_cat[c]:
            continue
        asin, e, img = by_cat[c].pop(0)
        price = cat[asin]["price"]
        pin_name = f"{e['id']}.png"
        if render:
            pin_factory.compose(
                img, os.path.join(PINS, pin_name),
                kicker=KICKER[e["cat"]], headline=e["headline"],
                price=f"${price}" if price else "", badge="",
                sub=e["sub"], spec=e["spec"], brand=q["brand"])
        item = {"id": e["id"], "cat": e["cat"], "product": cat[asin]["title"][:200],
                "headline": e["headline"], "sub": e["sub"],
                "price": f"${price}" if price else "", "badge": "",
                "spec": e["spec"], "asin": asin,
                "image_source": cat[asin]["img"], "pin": pin_name,
                "link": f"https://www.amazon.com/dp/{asin}?tag={q['tag']}",
                "body": e["body"], "status": "rendered",
                "rendered_at": daily.datetime.now(daily.timezone.utc).isoformat(timespec="seconds")}
        q["items"].append(item)
        new.append(item)

    daily.save(q)
    print(json.dumps({"queued": len(new),
                      "ids": [n["id"] for n in new],
                      "skipped": skipped}, indent=1))
    return new


if __name__ == "__main__":
    main(render="--no-render" not in sys.argv)
