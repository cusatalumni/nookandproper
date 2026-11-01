#!/usr/bin/env python3
"""Re-compose every queued pin that came from a verified ASIN (after a design tweak)."""
import json, os
import daily, pin_factory

BASE = os.path.dirname(os.path.abspath(__file__))
KICK = {"home-organization": "Home Organisation", "pet-enrichment": "Pet Enrichment",
        "kitchen-air-fryer": "Kitchen & Air Fryer", "home-fitness": "Home Fitness",
        "sleep-comfort": "Sleep & Comfort"}

cat = json.load(open(os.path.join(BASE, "content", "amz", "catalog_asin.json")))
q = daily.load()
n = 0
for it in q["items"]:
    a = it.get("asin")
    if not a or a not in cat or not cat[a].get("cached"):
        continue
    img = os.path.join(BASE, cat[a]["cached"])
    if not os.path.exists(img):
        continue
    pin_factory.compose(img, os.path.join(BASE, "pins", it["pin"]),
                        kicker=KICK.get(it["cat"], it["cat"]), headline=it["headline"],
                        price=it.get("price", ""), badge=it.get("badge", ""),
                        sub=it.get("sub", ""), spec=it.get("spec", ""), brand=q["brand"])
    n += 1
print(f"re-rendered {n} pins")
