#!/usr/bin/env python3
"""Append one daily blog post to content/feed.json."""
import json, os, sys, argparse
from datetime import date
BASE = os.path.dirname(os.path.abspath(__file__))
FEED = os.path.join(BASE, "content", "feed.json")
ap = argparse.ArgumentParser()
ap.add_argument("--cat", required=True); ap.add_argument("--title", required=True)
ap.add_argument("--body", required=True); ap.add_argument("--pin", required=True)
ap.add_argument("--link", required=True); ap.add_argument("--price", default="")
a = ap.parse_args()
feed = json.load(open(FEED)) if os.path.exists(FEED) else []
import re as _re
_slug = _re.sub(r"[^a-zA-Z0-9]+", "-", a.title).strip("-").lower()[:70]
for _f in feed:
    _fs = _re.sub(r"[^a-zA-Z0-9]+", "-", _f["title"]).strip("-").lower()[:70]
    if _fs == _slug or _f.get("pin") == a.pin:
        raise SystemExit(f"refusing duplicate: '{a.title}' is already published")
feed.insert(0, {"date": date.today().isoformat(), "cat": a.cat, "title": a.title,
                "body": a.body, "pin": a.pin, "link": a.link, "price": a.price})
json.dump(feed, open(FEED, "w"), indent=2, ensure_ascii=False)
print(f"post added · feed now {len(feed)}")
