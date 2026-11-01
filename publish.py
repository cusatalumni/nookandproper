#!/usr/bin/env python3
"""Publish today's pins with zero model calls: queue -> feed -> build -> push.

Copy is already written in the queue (each ASIN item carries `body`), so the
daily run is a pure script. Run it, then say one line in chat.

    python3 publish.py            # 3 pins, build, push
    python3 publish.py --n 1      # smaller batch
    python3 publish.py --dry      # show the pack, change nothing
"""
import argparse, json, os, re, subprocess, sys
from datetime import date

import daily

BASE = os.path.dirname(os.path.abspath(__file__))
FEED = os.path.join(BASE, "content", "feed.json")


def slug(t):
    return re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()[:70]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=None)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    q = daily.load()
    by_id = {i["id"]: i for i in q["items"]}
    feed = json.load(open(FEED)) if os.path.exists(FEED) else []
    seen_slug = {slug(f["title"]) for f in feed}
    seen_pin = {f.get("pin") for f in feed}

    if a.dry:
        left = [i for i in q["items"] if i.get("status") == "rendered" and not i.get("posted_at")]
        print(json.dumps({"ready": len(left),
                          "next": [{"id": i["id"], "headline": i["headline"]}
                                   for i in left[: a.n or q.get("per_day", 3)]]}, indent=1))
        return

    pack = daily.todays_pack(a.n)          # marks posted_at so a rerun never repeats
    added = []
    for p in pack["pack"]:
        it = by_id.get(p["id"], {})
        body = it.get("body", "")
        if not body:
            print(f"skip {p['id']}: no body copy in queue", file=sys.stderr)
            continue
        if slug(p["headline"]) in seen_slug or p["pin"] in seen_pin:
            print(f"skip {p['id']}: already in feed", file=sys.stderr)
            continue
        feed.insert(0, {"date": date.today().isoformat(), "cat": p["cat"],
                        "title": p["headline"], "body": body, "pin": p["pin"],
                        "link": p["link"], "price": p.get("price", "")})
        seen_slug.add(slug(p["headline"])); seen_pin.add(p["pin"])
        added.append(p)

    if not added:
        print(json.dumps({"published": 0, "note": "nothing new to publish",
                          "ready_left": pack.get("ready_left", 0)}, indent=1))
        return

    json.dump(feed, open(FEED, "w"), indent=2, ensure_ascii=False)
    out = subprocess.run(["./push.sh", f"daily pins {date.today().isoformat()}"],
                         cwd=BASE, capture_output=True, text=True)
    print(json.dumps({"published": [p["headline"] for p in added],
                      "feed": len(feed), "ready_left": pack["ready_left"],
                      "push_ok": out.returncode == 0,
                      "push": (out.stdout + out.stderr).strip()[-400:]}, indent=1))


if __name__ == "__main__":
    main()
