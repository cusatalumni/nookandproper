#!/usr/bin/env python3
"""Build the pin-blog site from content/site.json into a single self-contained HTML page.

Affiliate links are generated from the Amazon Associates tag in site.json.
We use keyword search URLs (tag-safe, no invented ASINs). Swap `asin` in a pin
to emit a /dp/ product link instead.
"""
import json
import os
import sys
from datetime import date

BASE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(BASE, "content", "site.json")
QUEUE = os.path.join(BASE, "content", "queue.json")
OUT = os.path.join(BASE, "out", "index.html")


def load():
    with open(SITE) as f:
        site = json.load(f)
    if os.path.exists(QUEUE):
        with open(QUEUE) as f:
            site["_queue"] = json.load(f)
    feed_path = os.path.join(BASE, "content", "feed.json")
    if os.path.exists(feed_path):
        with open(feed_path) as f:
            site["_feed"] = json.load(f)
    return site


def cat_pins(site, slug):
    """Pins come from the queue: rendered ones show, the rest are listed as upcoming."""
    q = site.get("_queue") or {}
    feed_pins = {f.get("pin") for f in site.get("_feed", [])}
    items = [i for i in q.get("items", []) if i.get("cat") == slug
             and i.get("pin") not in feed_pins]
    done = [i for i in items
            if i.get("status") == "rendered" and i.get("pin")
            and os.path.exists(os.path.join(BASE, "pins", i["pin"]))]
    todo = [i for i in items if i.get("status", "queued") == "queued"]
    return done, todo


def affiliate(site, pin):
    tag = site["tag"]
    if pin.get("asin"):
        return f"https://www.amazon.com/dp/{pin['asin']}?tag={tag}"
    q = pin.get("query") or pin["title"]
    from urllib.parse import quote_plus
    return f"https://www.amazon.com/s?k={quote_plus(q)}&tag={tag}"


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


CSS = """
:root{
  --cream:#faf6f0; --ink:#241f1b; --muted:#6d635a;
  --accent:#a8593c; --line:#e6dcd0; --card:#fffdfa;
}
*{box-sizing:border-box}
body{margin:0;background:var(--cream);color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  line-height:1.65;-webkit-font-smoothing:antialiased}
.wrap{max-width:1080px;margin:0 auto;padding:0 24px}
a{color:var(--accent)}
header.site{border-bottom:1px solid var(--line);background:var(--card)}
header.site .wrap{display:flex;align-items:center;justify-content:space-between;
  padding:22px 24px;flex-wrap:wrap;gap:10px}
.brand{font-family:Georgia,"Times New Roman",serif;font-size:23px;letter-spacing:.2px;margin:0;font-weight:600}
.brand span{color:var(--accent)}
nav.top{font-size:13px;color:var(--muted);letter-spacing:.06em;text-transform:uppercase}
.hero{padding:64px 0 44px;text-align:center}
.hero h1{font-family:Georgia,serif;font-size:clamp(30px,5vw,50px);line-height:1.15;
  margin:0 0 16px;font-weight:600;letter-spacing:-.5px}
.hero p{color:var(--muted);max-width:640px;margin:0 auto;font-size:17px}
.rule{width:56px;height:3px;background:var(--accent);margin:26px auto 0}
.toc{display:flex;flex-wrap:wrap;gap:10px;justify-content:center;padding:0 0 56px}
.toc a{font-size:13px;letter-spacing:.05em;text-transform:uppercase;text-decoration:none;
  border:1px solid var(--line);border-radius:999px;padding:8px 16px;color:var(--muted);
  background:var(--card)}
.toc a:hover{border-color:var(--accent);color:var(--accent)}
article.post{padding:48px 0;border-top:1px solid var(--line)}
.kicker{font-size:12px;letter-spacing:.16em;text-transform:uppercase;color:var(--accent);
  margin:0 0 10px;font-weight:600}
article.post h2{font-family:Georgia,serif;font-size:clamp(24px,3.6vw,34px);line-height:1.25;
  margin:0 0 8px;font-weight:600}
.meta{font-size:13px;color:var(--muted);margin:0 0 22px}
.lede{font-size:18px;color:#3c342d;margin:0 0 18px}
article.post p{margin:0 0 16px}
.why{background:var(--card);border-left:3px solid var(--accent);padding:16px 20px;
  margin:0 0 26px;font-size:15px;color:#4a4139}
.why b{color:var(--ink)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:20px;
  margin:26px 0 10px}
.pin{display:block;text-decoration:none;color:inherit;background:var(--card);
  border:1px solid var(--line);border-radius:14px;overflow:hidden;transition:.18s}
.pin:hover{transform:translateY(-3px);box-shadow:0 10px 26px rgba(60,40,20,.12)}
.pin img{width:100%;display:block;aspect-ratio:2/3;object-fit:cover;background:#efe7dc}
.ph{aspect-ratio:2/3;display:flex;flex-direction:column;justify-content:space-between;
  padding:20px 18px 18px;background:linear-gradient(160deg,#f3e9dc 0%,#e9dccb 55%,#dfcdb6 100%);
  position:relative;overflow:hidden}
.ph:after{content:"";position:absolute;inset:11px;border:1px solid rgba(140,100,70,.22);border-radius:7px;pointer-events:none}
.ph .k{font-size:9.5px;letter-spacing:.19em;text-transform:uppercase;color:#9c6a4c;font-weight:700}
.ph .t{font-family:Georgia,serif;font-size:17px;line-height:1.3;color:#2b231d;font-weight:600;
  text-align:center;align-self:center;padding:0 4px}
.ph .f{font-size:9px;letter-spacing:.14em;text-transform:uppercase;color:#8a7563;text-align:center}
.pin .cap{padding:12px 14px 15px}
.pin .cap b{display:block;font-size:14px;line-height:1.35;font-weight:600}
.pin .cap small{display:block;color:var(--muted);font-size:12px;margin-top:5px}
.tag-list{font-size:13px;color:var(--muted);margin:14px 0 0}
footer.site{border-top:1px solid var(--line);padding:36px 0 56px;margin-top:32px;
  font-size:12.5px;color:var(--muted);line-height:1.7}
footer.site .wrap{max-width:760px}
.disclosure{background:var(--card);border:1px solid var(--line);border-radius:10px;
  padding:14px 16px;margin-bottom:18px}
@media(max-width:560px){.hero{padding:44px 0 32px}.grid{grid-template-columns:repeat(2,1fr);gap:12px}
  article.post{padding:36px 0}.pin .cap{padding:9px 10px 12px}.pin .cap b{font-size:12px}}
"""


def render(site):
    cats = site["categories"]
    out = []
    out.append(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(site['brand'])} — {esc(site.get('tagline','Trending finds, pinned daily'))}</title>
<meta name="description" content="{esc(site.get('description',''))}">
<meta property="og:title" content="{esc(site['brand'])} — {esc(site.get('tagline',''))}">
<meta property="og:description" content="{esc(site.get('description',''))}">
<meta property="og:type" content="website">
<meta property="og:url" content="{esc(site.get('site_url',''))}">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{esc(site.get('site_url',''))}">
<style>{CSS}</style>
</head>
<body>
<header class="site"><div class="wrap">
  <p class="brand">{esc(site['brand'].split(' ')[0])} <span>{esc(' '.join(site['brand'].split(' ')[1:]))}</span></p>
  <nav class="top">Updated {esc(site.get('updated',''))}</nav>
</div></header>

<div class="wrap">
  <section class="hero">
    <h1>{esc(site.get('headline',''))}</h1>
    <p>{esc(site.get('subhead',''))}</p>
    <div class="rule"></div>
  </section>
  <div class="toc">""")

    for c in cats:
        out.append(f'<a href="#{esc(c["slug"])}">{esc(c["name"])}</a>')
    out.append("</div>")

    feed = site.get("_feed", [])
    for c in cats:
        daily = [p for p in feed if p.get("cat") == c["slug"]]
        if daily:
            out.append(f'  <article class="post" id="{esc(c["slug"])}">')
            out.append(f'    <p class="kicker">{esc(c["name"])} · Daily picks</p>')
            out.append("    <div class=\"grid\">")
            for p in daily[:12]:
                href = p.get("link") or affiliate(site, p)
                out.append(f"""      <a class="pin" href="{esc(href)}" target="_blank" rel="nofollow sponsored noopener">
        <img src="pins/{esc(p['pin'])}" alt="{esc(p['title'])}" loading="lazy">
        <div class="cap"><b>{esc(p['title'])}</b><small>{esc(p.get('price',''))}</small></div>
      </a>""")
            out.append("    </div>")
            for p in daily[:12]:
                out.append(f"    <h3 style=\"font-family:Georgia,serif;font-size:20px;margin:26px 0 6px\">{esc(p['title'])}</h3>")
                out.append(f"    <p class=\"meta\">{esc(p.get('date',''))}</p>")
                out.append(f"    <p>{esc(p['body'])}</p>")
            out.append("  </article>")
        for post in c["posts"]:
            out.append(f"""
  <article class="post" id="{esc(c['slug'])}">
    <p class="kicker">{esc(c['name'])}</p>
    <h2>{esc(post['title'])}</h2>
    <p class="meta">{esc(post['date'])} · {len(post['pins'])} pins</p>
    <p class="lede">{esc(post['lede'])}</p>
    <div class="why"><b>Why it's trending:</b> {esc(c.get('why',''))}</div>""")
            for para in post.get("body", []):
                out.append(f"    <p>{esc(para)}</p>")
            done, todo = cat_pins(site, c["slug"])
            if done:
                out.append('    <div class="grid">')
                for p in done:
                    href = p.get("link") or affiliate(site, p)
                    out.append(f"""      <a class="pin" href="{esc(href)}" target="_blank" rel="nofollow sponsored noopener">
        <img src="pins/{esc(p['pin'])}" alt="{esc(p['headline'])}" loading="lazy">
        <div class="cap"><b>{esc(p['headline'])}</b><small>{esc(p.get('price',''))}</small></div>
      </a>""")
                out.append("    </div>")
            if todo:
                out.append('    <p class="tag-list"><b>Next up in this category:</b> '
                           + esc(" · ".join(t["headline"] for t in todo[:4])) + "</p>")
            if c.get("keywords"):
                out.append(f'    <p class="tag-list">Search: {esc(" · ".join(c["keywords"]))}</p>')
            out.append("  </article>")

    out.append(f"""
</div>
<footer class="site"><div class="wrap">
  <div class="disclosure"><b>Affiliate disclosure.</b> {esc(site['brand'])} is a participant in the Amazon
  Services LLC Associates Program. As an Amazon Associate we earn from qualifying purchases.
  Prices and availability are accurate as of the date shown and are subject to change.</div>
  <p>© {date.today().year} {esc(site['brand'])}. Pins updated daily.</p>
</div></footer>
</body>
</html>""")
    return "\n".join(out)


def main():
    site = load()
    site["updated"] = site.get("updated") or date.today().isoformat()
    html = render(site)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        f.write(html)
    total = sum(len(p["pins"]) for c in site["categories"] for p in c["posts"])
    print(f"wrote {OUT} · {len(site['categories'])} categories · {total} pins")


if __name__ == "__main__":
    main()
