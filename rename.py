#!/usr/bin/env python3
"""Rename the brand everywhere: content, pins (re-composited), site. Local, no credits."""
import json, os, sys, re, shutil
import pin_factory

BASE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(BASE, "content", "site.json")
QUEUE = os.path.join(BASE, "content", "queue.json")
KICK = {"home-organization": "Home Organisation", "pet-enrichment": "Pet Enrichment",
        "kitchen-air-fryer": "Kitchen & Air Fryer", "home-fitness": "Home Fitness",
        "sleep-comfort": "Sleep & Comfort"}
SPEC = {"ho-1":"6 PACK","ho-2":"1 L","ho-3":"6 PACK","ho-4":"EXPANDABLE","pe-1":"20 IN",
        "pe-2":"2.5 L","pe-3":"MEDIUM","pe-4":"TRAY","kit-1":"4 QT","kit-2":"24 PC",
        "kit-3":"305 PCS","kit-4":"3-IN-1","fit-1":"14% INCLINE","fit-2":"3/4 IN",
        "fit-3":"14 IN","fit-4":"50 LB","slp-1":"3 INCH","slp-2":"42×84","slp-3":"CERVICAL",
        "slp-4":"EVO"}


def main():
    if len(sys.argv) < 2:
        print("usage: rename.py 'New Brand' [domain]"); return
    brand = sys.argv[1]
    domain = sys.argv[2] if len(sys.argv) > 2 else ""

    for path, key in ((SITE, "brand"), (QUEUE, "brand")):
        d = json.load(open(path))
        d[key] = brand.lower()
        if key == "brand" and path == SITE:
            d["brand"] = brand          # display case on the site
        json.dump(d, open(path, "w"), indent=2, ensure_ascii=False)

    q = json.load(open(QUEUE))
    q["brand"] = brand.lower()
    json.dump(q, open(QUEUE, "w"), indent=2, ensure_ascii=False)

    for it in q["items"]:
        pr = it.get("price", "")
        pr = pr.split("·")[-1].strip() if "·" in pr else pr
        pin_factory.compose(f"content/imgcache/{it['id']}.jpg", f"pins/{it['pin']}",
                            kicker=KICK[it["cat"]], headline=it["headline"], price=pr,
                            badge="", sub=it.get("sub", ""), spec=SPEC.get(it["id"], ""),
                            brand=brand.lower())
    dst = os.path.join(BASE, "out", "pins")
    os.makedirs(dst, exist_ok=True)
    for fn in os.listdir(os.path.join(BASE, "pins")):
        shutil.copy2(os.path.join(BASE, "pins", fn), os.path.join(dst, fn))
    print(f"renamed to {brand!r}" + (f" ({domain})" if domain else "") +
          f" · re-composited {len(q['items'])} pins")


if __name__ == "__main__":
    main()
