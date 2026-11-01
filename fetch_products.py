#!/usr/bin/env python3
"""Fetch real listing data for a list of ASINs over plain HTTP — zero credits.

Amazon serves full product pages to a well-formed browser request even when
gsk crawler / the headless browser are blocked. Everything needed for a pin
(title, price, 1500px product photo) comes out of that one HTML response.

    python3 fetch_products.py B08ZK5WDWN B08CGHSY9G ...

Writes content/amz/catalog_asin.json: {ASIN: {title, price, img, ok, note}}
and caches the downloaded photo in content/imgcache/<ASIN>.<ext>.
"""
import json, os, re, sys, time
import requests

BASE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(BASE, "content", "imgcache")
OUT = os.path.join(BASE, "content", "amz", "catalog_asin.json")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/121.0 Safari/537.36")
HEAD = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}


def parse(html):
    out = {}
    m = re.search(r'id="productTitle"[^>]*>\s*(.*?)\s*<', html, re.S)
    out["title"] = re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
    price = ""
    m = re.search(r'"priceAmount"\s*:\s*([0-9.]+)', html) or \
        re.search(r'class="a-offscreen">\s*\$([0-9,.]+)\s*<', html)
    if m:
        try:
            price = f"{float(m.group(1).replace(',', '')):.2f}"
        except ValueError:
            price = ""
    out["price"] = price
    imgs = re.findall(r'"hiRes":"(https://[^"]+)"', html) or \
        re.findall(r'"large":"(https://[^"]+)"', html) or \
        re.findall(r'id="landingImage"[^>]*src="(https://[^"]+)"', html)
    out["img"] = imgs[0] if imgs else ""
    if "Page Not Found" in html or "dogs of Amazon" in html or not out["title"]:
        out["ok"] = False
        out["note"] = "no product data in response"
    else:
        out["ok"] = True
        out["note"] = ""
    return out


def fetch(asin, tries=2):
    url = f"https://www.amazon.com/dp/{asin}"
    last = ""
    for i in range(tries):
        try:
            r = requests.get(url, headers=HEAD, timeout=25)
            if r.status_code == 200 and len(r.text) > 40000:
                d = parse(r.text)
                if d.get("ok"):
                    return d
                last = d.get("note") or "short page"
            else:
                last = f"HTTP {r.status_code} / {len(r.text)} bytes"
        except Exception as e:
            last = str(e)[:80]
        time.sleep(3)
    return {"ok": False, "title": "", "price": "", "img": "", "note": last}


def main():
    os.makedirs(CACHE, exist_ok=True)
    asins = [a.strip().upper() for a in sys.argv[1:] if a.strip()]
    cat = {}
    if os.path.exists(OUT):
        cat = json.load(open(OUT))
    for a in asins:
        if a in cat and cat[a].get("ok"):
            print(f"{a} cached"); continue
        d = fetch(a)
        cat[a] = d
        print(f"{a} ok={d['ok']} ${d['price']} {d['title'][:64]} {d['note']}")
        if d["ok"] and d["img"]:
            try:
                r = requests.get(d["img"], headers=HEAD, timeout=30)
                ext = ".png" if d["img"].lower().endswith(".png") else ".jpg"
                p = os.path.join(CACHE, a + ext)
                open(p, "wb").write(r.content)
                d["cached"] = os.path.relpath(p, BASE)
            except Exception as e:
                d["cached"] = ""
                d["note"] = f"img failed: {e}"[:80]
        json.dump(cat, open(OUT, "w"), indent=2, ensure_ascii=False)
        time.sleep(2.5)
    ok = sum(1 for v in cat.values() if v.get("ok"))
    print(f"\n{ok}/{len(cat)} ASINs resolved")


if __name__ == "__main__":
    main()
