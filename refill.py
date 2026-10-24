#!/usr/bin/env python3
"""Source one real Amazon listing per category and append it to the queue."""
import json, os, re
import discover, materialize  # reuse crawler + composer

BASE = os.path.dirname(os.path.abspath(__file__))
SPEC = {"home-organization": "Home Organisation", "pet-enrichment": "Pet Enrichment",
        "kitchen-air-fryer": "Kitchen & Air Fryer", "home-fitness": "Home Fitness",
        "sleep-comfort": "Sleep & Comfort"}

NEW = [
    ("home-organization", "adjustable drawer dividers cutlery", "drawer dividers",
     "The Drawer That Stops Eating Cutlery", "Adjustable dividers beat a fixed tray.",
     "Drawer organisers · $15–35", "ADJUSTABLE"),
    ("pet-enrichment", "reusable pet hair remover roller", "pet hair remover",
     "The 30-Second Fix for Pet Hair on the Sofa", "No batteries, no refills, no vacuum.",
     "Hair removers · $12–25", "REUSABLE"),
    ("kitchen-air-fryer", "silicone baking mat sheet pan", "baking mat",
     "The Sheet Pan Mat That Replaced Foil", "Nothing sticks, and it washes in seconds.",
     "Baking mats · $12–25", "2 PACK"),
    ("home-fitness", "resistance bands set with handles", "resistance bands",
     "A Gym in a Drawer for Under $30", "The cheapest honest entry into home fitness.",
     "Band sets · $18–40", "5 BANDS"),
    ("sleep-comfort", "sunrise alarm clock wake up light", "sunrise",
     "Wake Up Before Your Alarm Does", "Light first, sound later — that is the trick.",
     "Sunrise alarms · $30–60", "SUNRISE"),
]


def main():
    q = json.load(open(os.path.join(BASE, "content", "queue.json")))
    fp = os.path.join(BASE, "content", "amz", "found.json")
    found = json.load(open(fp)) if os.path.exists(fp) else {}
    added = []
    for i, (cat, query, must, headline, sub, price, spec) in enumerate(NEW, 1):
        try:
            md = discover.crawl(query)
            best = discover.parse(md, must)
        except Exception as e:
            print(f"{cat}: FAIL {e}")
            continue
        if not best:
            print(f"{cat}: NO MATCH ({query})")
            continue
        nid = f"n{i}"
        found[nid] = {"query": query, **best}
        words = " ".join(re.sub(r"[^A-Za-z0-9 ]", " ", best["title"]).split()[:9])
        item = {"id": nid, "cat": cat, "product": best["title"][:120],
                "headline": headline, "sub": sub, "price": price, "badge": "",
                "spec": spec, "asin": "", "image_source": best["img"],
                "pin": f"{nid}.png",
                "link": "https://www.amazon.com/s?k=" + __import__("urllib.parse").parse.quote_plus(words, safe="") + f"&tag={q['tag']}",
                "status": "queued"}
        q["items"].append(item)
        added.append(item)
        print(f"{nid}: {best['title'][:72]}")
    json.dump(found, open(fp, "w"), indent=2)
    json.dump(q, open(os.path.join(BASE, "content", "queue.json"), "w"), indent=2, ensure_ascii=False)
    print(f"\nappended {len(added)} products")


if __name__ == "__main__":
    main()
