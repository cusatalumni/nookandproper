#!/usr/bin/env python3
"""Render the Nook & Proper static site:

    out/index.html                     home — 4 newest per category, links out
    out/category/<slug>.html           full category feed + the category article
    out/p/<slug>.html                  one page per pin (the Pinterest destination)
    out/about etc.               policy / about pages
    out/pins/*.png                     the pin images
"""
import json
import os
import re
from datetime import date

BASE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(BASE, "content", "site.json")
QUEUE = os.path.join(BASE, "content", "queue.json")
FEED = os.path.join(BASE, "content", "feed.json")
OUT = os.path.join(BASE, "out")
PER_HOME = 4
PER_PAGE = 12

CAT_LABEL = {"home-organization": "Home Organisation", "pet-enrichment": "Pet Enrichment",
             "kitchen-air-fryer": "Kitchen & Air Fryer", "home-fitness": "Home Fitness",
             "sleep-comfort": "Sleep & Comfort"}


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def amazon_path(link):
    """'/s?k=...' from a full Amazon URL, tag stripped — the geo script re-adds host+tag."""
    from urllib.parse import urlsplit, parse_qsl, urlencode
    try:
        u = urlsplit(link)
    except Exception:
        return "/"
    q = [(k, v) for k, v in parse_qsl(u.query) if k != "tag"]
    return u.path + ("?" + urlencode(q) if q else "")


def slugify(s, maxlen=70):
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s[:maxlen].rstrip("-")


def load():
    site = json.load(open(SITE))
    site["site_url"] = site.get("site_url", "").rstrip("/") + "/"
    site["_queue"] = json.load(open(QUEUE)) if os.path.exists(QUEUE) else {"items": []}
    site["_feed"] = json.load(open(FEED)) if os.path.exists(FEED) else []
    # one canonical post record per pin
    posts = []
    for f in site["_feed"]:
        pid = re.search(r"([a-z]+-\d+)", f.get("pin", ""))
        pid = pid.group(1) if pid else ""
        posts.append({
            "cat": f["cat"], "cat_label": CAT_LABEL.get(f["cat"], f["cat"]),
            "title": f["title"], "body": f["body"], "date": f.get("date", ""),
            "pin": f.get("pin", ""), "link": f.get("link", ""),
            "price": f.get("price", ""), "id": pid,
            "slug": slugify(f["title"]),
        })
    site["_posts"] = posts
    return site


CSS = """
:root{--cream:#faf6f0;--ink:#241f1b;--muted:#6d635a;--accent:#a8593c;--line:#e6dcd0;--card:#fffdfa}
*{box-sizing:border-box}
body{margin:0;background:var(--cream);color:var(--ink);line-height:1.65;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  -webkit-font-smoothing:antialiased}
.wrap{max-width:1080px;margin:0 auto;padding:0 24px}
a{color:var(--accent)}
header.site{border-bottom:1px solid var(--line);background:var(--card);position:sticky;top:0;z-index:9}
header.site .wrap{display:flex;align-items:center;justify-content:space-between;
  padding:18px 24px;flex-wrap:wrap;gap:12px}
.brand{font-family:Georgia,"Times New Roman",serif;font-size:22px;margin:0;font-weight:600;
  text-decoration:none;color:var(--ink);letter-spacing:-.2px}
.brand span{color:var(--accent)}
nav.main{display:flex;gap:20px;flex-wrap:wrap}
nav.main a{font-size:13px;letter-spacing:.05em;text-transform:uppercase;text-decoration:none;
  color:var(--muted);padding:4px 0;border-bottom:2px solid transparent}
nav.main a:hover,nav.main a.on{color:var(--accent);border-bottom-color:var(--accent)}
.hero{padding:58px 0 34px;text-align:center}
.hero h1{font-family:Georgia,serif;font-size:clamp(29px,4.6vw,46px);line-height:1.16;margin:0 0 14px;
  font-weight:600;letter-spacing:-.5px}
.hero p{color:var(--muted);max-width:620px;margin:0 auto;font-size:17px}
.rule{width:54px;height:3px;background:var(--accent);margin:24px auto 0}
.section{padding:34px 0 10px;border-top:1px solid var(--line)}
.section-head{display:flex;align-items:baseline;justify-content:space-between;gap:16px;
  margin-bottom:18px;flex-wrap:wrap}
.section-head h2{font-family:Georgia,serif;font-size:clamp(21px,3vw,27px);margin:0;font-weight:600}
.section-head a{font-size:13px;letter-spacing:.05em;text-transform:uppercase;text-decoration:none}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(206px,1fr));gap:20px}
.card{display:block;text-decoration:none;color:inherit;background:var(--card);
  border:1px solid var(--line);border-radius:14px;overflow:hidden;transition:.18s}
.card:hover{transform:translateY(-3px);box-shadow:0 10px 26px rgba(60,40,20,.12)}
.card img{width:100%;display:block;aspect-ratio:2/3;object-fit:cover;background:#efe7dc}
.card .cap{padding:11px 13px 14px}
.card .cap b{display:block;font-size:13.5px;line-height:1.35;font-weight:600}
.card .cap small{display:block;color:var(--muted);font-size:12px;margin-top:4px}
.article{padding:44px 0;border-top:1px solid var(--line)}
.kicker{font-size:12px;letter-spacing:.16em;text-transform:uppercase;color:var(--accent);
  margin:0 0 10px;font-weight:600}
.article h1,.article h2{font-family:Georgia,serif;font-size:clamp(25px,3.6vw,36px);line-height:1.22;
  margin:0 0 8px;font-weight:600}
.meta{font-size:13px;color:var(--muted);margin:0 0 20px}
.lede{font-size:18px;color:#3c342d;margin:0 0 18px}
.why{background:var(--card);border-left:3px solid var(--accent);padding:15px 19px;margin:0 0 24px;
  font-size:14.5px;color:#4a4139}
.postwrap{display:grid;grid-template-columns:minmax(0,340px) minmax(0,1fr);gap:36px;align-items:start}
.postwrap img{width:100%;border-radius:14px;border:1px solid var(--line);display:block}
.buy{display:inline-block;background:var(--accent);color:#fff;text-decoration:none;
  font-weight:700;font-size:16px;padding:16px 30px;border-radius:44px;margin:8px 0 6px}
.buy:hover{filter:brightness(1.08)}
.small{font-size:12.5px;color:var(--muted)}
.disclosure{background:var(--card);border:1px solid var(--line);border-radius:10px;
  padding:13px 16px;margin:18px 0;font-size:13px;color:var(--muted)}
footer.site{border-top:1px solid var(--line);padding:36px 0 54px;margin-top:34px;font-size:13px;
  color:var(--muted)}
footer.site .cols{display:flex;gap:40px;flex-wrap:wrap;justify-content:space-between}
footer.site h4{font-size:11px;letter-spacing:.14em;text-transform:uppercase;margin:0 0 10px;
  color:var(--ink)}
footer.site a{display:block;text-decoration:none;color:var(--muted);padding:3px 0;font-size:13px}
footer.site a:hover{color:var(--accent)}
.footnote{margin-top:26px;padding-top:18px;border-top:1px solid var(--line);font-size:12px}
.legal{padding:40px 0;max-width:760px}
.legal h1{font-family:Georgia,serif;font-size:clamp(25px,3.4vw,34px);margin:0 0 6px}
.legal h2{font-family:Georgia,serif;font-size:20px;margin:26px 0 8px}
.legal p,.legal li{font-size:15.5px;color:#3c342d}
@media(max-width:720px){.postwrap{grid-template-columns:1fr;gap:22px}.grid{
  grid-template-columns:repeat(2,1fr);gap:12px}.hero{padding:38px 0 24px}}
"""


def layout(site, title, body, canonical="", active="", og_image="",
           page_type="website", article=None):
    regions_js = json.dumps(site.get("regions", {}))
    verify_meta = "\n".join(site.get("verify_meta", []))
    article_meta = ""
    jsonld = ""
    if article:
        base = site.get("site_url", "").rstrip("/")
        article_meta = (
            f'\n<meta property="article:published_time" content="{esc(article["published"])}">'
            f'\n<meta property="article:section" content="{esc(article["section"])}">'
            f'\n<meta property="article:author" content="{esc(site["brand"])}">'
            f'\n<meta name="author" content="{esc(site["brand"])}">')
        ld = {
            "@context": "https://schema.org", "@type": "Article",
            "headline": title, "datePublished": article["published"],
            "articleSection": article["section"],
            "author": {"@type": "Organization", "name": site["brand"]},
            "publisher": {"@type": "Organization", "name": site["brand"]},
            "mainEntityOfPage": base + canonical,
            "image": base + "/pins/" + article["pin"],
            "description": site.get("description", ""),
        }
        jsonld = ('\n<script type="application/ld+json">'
                  + json.dumps(ld) + "</script>")
    nav = "".join(
        f'<a href="/category/{c['slug']}" class="{"on" if active == c["slug"] else ""}">'
        f'{esc(CAT_LABEL.get(c["slug"], c["name"]))}</a>'
        for c in site["categories"])
    year = date.today().year
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(site.get('description',''))}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:type" content="{esc(page_type)}">{article_meta}
<meta property="og:url" content="{esc(site.get('site_url','').rstrip('/') + canonical)}">
<meta property="og:image" content="{esc(site.get('site_url','').rstrip('/') + (og_image or '/pins/ho-1.png'))}">
<meta property="og:image:width" content="1000">
<meta property="og:image:height" content="1500">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{esc(site.get('site_url','').rstrip('/') + canonical)}">
{verify_meta}
<style>{CSS}</style>{jsonld}
<script>window.NP_REGIONS = {regions_js};
window.NP_DEFAULT_REGION = {esc(site.get('default_region','US'))};</script>
<script src="/assets/geo.js" defer></script>
</head>
<body>
<header class="site"><div class="wrap">
  <a class="brand" href="/">{esc(site['brand'].split(' ')[0])} <span>{esc(' '.join(site['brand'].split(' ')[1:]))}</span></a>
  <nav class="main">{nav}</nav>
</div></header>
{body}
<footer class="site"><div class="wrap">
  <div class="cols">
    <div><h4>Categories</h4>
      {"".join(f'<a href="/category/{c['slug']}">{esc(CAT_LABEL.get(c["slug"], c["name"]))}</a>' for c in site["categories"])}
    </div>
    <div><h4>{esc(site['brand'])}</h4>
      <a href="/about">About us</a>
      <a href="/affiliate-disclosure">Affiliate disclosure</a>
      <a href="/privacy">Privacy policy</a>
      <a href="/terms">Terms of use</a>
    </div>
  </div>
  <div class="footnote">
    <p>{esc(site['brand'])} is a participant in the Amazon Services LLC Associates Program, an affiliate
    advertising program designed to provide a means for sites to earn advertising fees by advertising and
    linking to Amazon.com. As an Amazon Associate we earn from qualifying purchases. Prices and availability
    are accurate as of the date shown and are subject to change.</p>
    <p>© {year} {esc(site['brand'])}. All rights reserved.</p>
  </div>
</div></footer>
</body>
</html>"""


def card(p):
    return (f'<a class="card" href="/p/{esc(p["slug"])}">'
            f'<img src="/pins/{esc(p["pin"])}" alt="{esc(p["title"])}" loading="lazy">'
            f'<div class="cap"><b>{esc(p["title"])}</b><small>{esc(p["price"])}</small></div></a>')


def render_home(site):
    posts = site["_posts"]
    out = [f"""<div class="wrap"><section class="hero">
  <h1>{esc(site.get('headline',''))}</h1>
  <p>{esc(site.get('subhead',''))}</p><div class="rule"></div>
</section>"""]
    for c in site["categories"]:
        mine = [p for p in posts if p["cat"] == c["slug"]]
        if not mine:
            continue
        label = CAT_LABEL.get(c["slug"], c["name"])
        out.append(f"""<section class="section">
  <div class="section-head"><h2>{esc(label)}</h2>
  <a href="/category/{esc(c['slug'])}">All {len(mine)} in {esc(label)} &rarr;</a></div>
  <div class="grid">{''.join(card(p) for p in mine[:PER_HOME])}</div>
</section>""")
    out.append("</div>")
    return "".join(out)


def render_category(site, c, page=1):
    allp = [p for p in site["_posts"] if p["cat"] == c["slug"]]
    pages = max(1, -(-len(allp) // PER_PAGE))
    posts = allp[(page - 1) * PER_PAGE: page * PER_PAGE]
    label = CAT_LABEL.get(c["slug"], c["name"])
    pillar = c["posts"][0] if c.get("posts") else None
    body = [f"""<div class="wrap">
<article class="article">
  <p class="kicker">{esc(label)}</p>
  <h1>{esc(pillar['title'] if pillar else label)}</h1>"""]
    if pillar:
        body.append(f'<p class="meta">{esc(pillar["date"])} · {len(posts)} picks</p>')
        body.append(f'<p class="lede">{esc(pillar["lede"])}</p>')
        body.append(f'<div class="why"><b>Why this category:</b> {esc(c.get("why",""))}</div>')
        for para in pillar.get("body", []):
            body.append(f"<p>{esc(para)}</p>")
    if posts:
        body.append(f'<div class="grid" style="margin-top:28px">{"".join(card(p) for p in posts)}</div>')
    if pages > 1:
        links = []
        for n in range(1, pages + 1):
            href = f"/category/{c['slug']}.html" if n == 1 else f"/category/{c['slug']}/page-{n}.html"
            links.append(f'<a class="pg{" on" if n == page else ""}" href="{href}">{n}</a>')
        body.append(f'<nav class="pager">{"".join(links)}</nav>')
    if c.get("keywords"):
        body.append(f'<p class="small" style="margin-top:22px">Search: {esc(" · ".join(c["keywords"]))}</p>')
    body.append('</article></div>')
    return "".join(body)


def render_post(site, p):
    related = [x for x in site["_posts"] if x["cat"] == p["cat"] and x["slug"] != p["slug"]][:4]
    body = f"""<div class="wrap"><article class="article">
  <p class="kicker">{esc(p['cat_label'])}</p>
  <div class="postwrap">
    <div><img src="/pins/{esc(p['pin'])}" alt="{esc(p['title'])}"></div>
    <div>
      <h1>{esc(p['title'])}</h1>
      <p class="meta">{esc(p['date'])}{(' · ' + esc(p['price'])) if p['price'] else ''}</p>
      <p>{esc(p['body'])}</p>
      <p><a class="buy" href="{esc(p['link'])}" data-amazon-path="{esc(amazon_path(p['link']))}" target="_blank" rel="nofollow sponsored noopener">Check price on Amazon</a></p>
      <p class="small" hidden>Showing the <b data-region-label></b> store for your location.</p>
      <p class="small">Opens the listing on Amazon.com. Price shown is the usual street price for this
      kind of product, not a live quote — check the listing for the current figure.</p>
      <div class="disclosure"><b>Affiliate disclosure.</b> We earn a commission from qualifying purchases
      made through this link, at no extra cost to you. This does not affect what we recommend.</div>
    </div>
  </div>"""
    if related:
        body += (f'<section class="section"><div class="section-head"><h2>More in '
                 f'{esc(p["cat_label"])}</h2><a href="/category/{esc(p["cat"])}.html">See all &rarr;</a></div>'
                 f'<div class="grid">{"".join(card(r) for r in related)}</div></section>')
    body += "</article></div>"
    return body


LEGAL = {
    "about": ("About us", """
<p>Nook &amp; Proper is a small independent edit of practical things for the home — the kind of
purchase that makes an everyday job slightly easier rather than the kind you admire in a photograph
and never use.</p>
<h2>What we cover</h2>
<p>Five categories, chosen because the sales data says people are actually buying them: home
organisation, pet enrichment, the air-fryer kitchen, home fitness, and sleep. We deliberately do not
cover beauty or fashion.</p>
<h2>How we choose</h2>
<p>We start from marketplace demand — what is genuinely selling, not what looks good on a mood board.
Each pick then has to pass a simpler test: would we explain it to a friend without embarrassment. If a
product only makes sense as an advert, it does not go in.</p>
<h2>How we make money</h2>
<p>Through affiliate commissions. If you buy through a link on this site we may earn a small
percentage, at no extra cost to you. That is the whole business model — we do not sell your data and we
do not take payment for a placement. See our <a href="/affiliate-disclosure">affiliate
disclosure</a> for the detail.</p>
<h2>Corrections</h2>
<p>Prices and availability change constantly. If something here is wrong, tell us and we will fix it
rather than quietly leave it up.</p>"""),

    "affiliate-disclosure": ("Affiliate disclosure", """
<p>Nook &amp; Proper is a participant in the Amazon Services LLC Associates Program, an affiliate
advertising program designed to provide a means for sites to earn advertising fees by advertising and
linking to Amazon.com.</p>
<h2>What that means in practice</h2>
<ul>
<li>When you click a product link and buy something, Amazon may pay us a commission.</li>
<li>The price you pay is exactly the same. The commission comes out of Amazon's margin, not your pocket.</li>
<li>We are never paid to feature a specific product, and no brand can buy a place in our edit.</li>
</ul>
<h2>Different countries</h2>
<p>We take part in the Amazon Associates programmes in more than one country. Depending on where you
are, product links open amazon.com, amazon.in or amazon.ae, with that marketplace's associate tag. The
product may cost more or less than the figure shown here, and may not be sold in your country at all.</p>
<h2>Prices</h2>
<p>Price bands shown on this site are typical street prices for that kind of product at the time of
writing. They are guidance, not a quote, and they change — sometimes within hours. Always check the
figure on the Amazon listing before buying.</p>
<h2>Trademarks</h2>
<p>Amazon and the Amazon logo are trademarks of Amazon.com, Inc. or its affiliates. Product names,
logos and brands are the property of their respective owners and are used here only to identify the
products being discussed.</p>
<h2>Images</h2>
<p>Product photography is supplied by the retailer and is used within the terms of the affiliate
program. The layout, typography, framing and watermark on every pin are ours.</p>"""),

    "privacy": ("Privacy policy", """
<p>This policy explains what happens to information when you visit Nook &amp; Proper. It is written to
be read, not to be survived.</p>
<h2>What we collect</h2>
<p>The site itself sets no tracking cookies and asks for no personal details. There is no account, no
comment system and no newsletter sign-up form.</p>
<h2>Which Amazon store you see</h2>
<p>The site reads the country your connection comes from — a two-letter code, provided by our host's
edge network — so that the product links open the Amazon store for your country with the matching
associate tag. That is the only use of it. It is not stored, not profiled, and no cookie is set for
it.</p>
<h2>Third parties</h2>
<p>When you click a product link you leave this site for Amazon, which sets its own cookies and
applies its own privacy policy. Amazon's affiliate programme may record that the visit came from here
so that a commission can be attributed. We never see your name, address, payment details or what you
bought.</p>
<h2>Hosting</h2>
<p>The site is served as static files by our hosting provider, which may keep standard server logs
including IP address and browser type for security and reliability.</p>
<h2>Your rights</h2>
<p>Because we hold no personal data about you, there is nothing for us to export or delete. If you
believe we hold something, contact us and we will look into it.</p>
<h2>Changes</h2>
<p>If this policy changes, the date at the top of the page changes with it.</p>"""),

    "terms": ("Terms of use", """
<p>By using Nook &amp; Proper you agree to the terms below. They are deliberately short.</p>
<h2>Information, not advice</h2>
<p>Everything here is general product commentary. It is not professional, medical, financial or safety
advice. A mattress topper is not a treatment for a medical condition; a walking pad is not a substitute
for medical clearance to exercise. Use your own judgement and, where it matters, a professional's.</p>
<h2>Accuracy</h2>
<p>We aim to be accurate and we correct mistakes when we find them, but prices, availability and
product specifications change without notice. Always confirm details on the retailer's listing before
buying.</p>
<h2>Affiliate links</h2>
<p>This site contains affiliate links. See the <a href="/affiliate-disclosure">affiliate
disclosure</a>.</p>
<h2>Liability</h2>
<p>The site is provided as-is. To the extent permitted by law, we are not liable for losses arising
from purchases made through third-party retailers or from reliance on what is written here.</p>
<h2>Content</h2>
<p>The writing, layout and pin designs are ours and may not be republished without permission. Product
photography belongs to its respective owner.</p>"""),
}


def render_legal(site, key):
    title, body = LEGAL[key]
    return f'<div class="wrap"><article class="legal"><h1>{esc(title)}</h1>' \
           f'<p class="meta">Last updated {date.today().isoformat()}</p>{body}</article></div>'


def clean_out():
    """Drop stale pages so renamed or removed posts never leave orphans. Keeps pins/."""
    import shutil
    for name in os.listdir(OUT):
        if name == "pins":
            continue
        path = os.path.join(OUT, name)
        shutil.rmtree(path) if os.path.isdir(path) else os.remove(path)


def main():
    os.makedirs(OUT, exist_ok=True)
    clean_out()
    site = load()
    site["updated"] = date.today().isoformat()
    written = []

    def write(rel, html):
        path = os.path.join(OUT, rel)
        os.makedirs(os.path.dirname(path) or OUT, exist_ok=True)
        open(path, "w").write(html)
        written.append(rel)

    # domain-verification files (Pinterest, Google, etc.) must sit at the site root
    verify_dir = os.path.join(BASE, "content", "verify")
    if os.path.isdir(verify_dir):
        import shutil as _sh
        for fn in os.listdir(verify_dir):
            src = os.path.join(verify_dir, fn)
            if os.path.isfile(src) and not fn.startswith(("_", ".")):
                _sh.copy2(src, os.path.join(OUT, fn))

    # static assets the pages need (fonts are build-only, not served)
    import shutil
    os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)
    for fn in os.listdir(os.path.join(BASE, "assets")):
        src = os.path.join(BASE, "assets", fn)
        if os.path.isfile(src) and fn.endswith(".js"):
            shutil.copy2(src, os.path.join(OUT, "assets", fn))

    write("index.html", layout(site, f"{site['brand']} — {site.get('tagline','')}",
                               render_home(site), "/"))
    urls = ["/index.html", "/about", "/affiliate-disclosure", "/privacy", "/terms"]
    for c in site["categories"]:
        n = max(1, -(-len([p for p in site["_posts"] if p["cat"] == c["slug"]]) // PER_PAGE))
        for pg in range(1, n + 1):
            rel = (f"category/{c['slug']}.html" if pg == 1
                   else f"category/{c['slug']}/page-{pg}.html")
            ttl = CAT_LABEL.get(c["slug"], c["name"]) + ("" if pg == 1 else f" — page {pg}")
            clean = (f"/category/{c['slug']}" if pg == 1 else f"/category/{c['slug']}/page-{pg}")
            write(rel, layout(site, f"{ttl} — {site['brand']}",
                              render_category(site, c, pg), clean, active=c["slug"]))
            urls.append(clean)
    for p in site["_posts"]:
        rel = f"p/{p['slug']}.html"
        write(rel, layout(site, f"{p['title']} — {site['brand']}", render_post(site, p),
                          f"/p/{p['slug']}", active=p["cat"], og_image=f"/pins/{p['pin']}",
                          page_type="article",
                          article={"published": p["date"] or date.today().isoformat(),
                                   "section": p["cat_label"], "pin": p["pin"]}))
        urls.append(f"/p/{p['slug']}")

    for key in LEGAL:
        write(f"{key}.html", layout(site, f"{LEGAL[key][0]} — {site['brand']}",
                                    render_legal(site, key), f"/{key}"))

    # pin -> destination sheet for Pinterest (not served, for Manoj)
    lines = ["# Pinterest pin destinations", "",
             "Use the URL as the pin's destination link. The Amazon link is what the page's",
             "button goes to — do not paste that into Pinterest.", ""]
    for p in site["_posts"]:
        lines.append(f"- **{p['title']}** ({p['cat_label']})")
        lines.append(f"  - Pin image: `/pins/{p['pin']}`")
        lines.append(f"  - Destination: {site.get('site_url','').rstrip('/')}/p/{p['slug']}")
        lines.append(f"  - Goes to Amazon: {p['link']}")
    open(os.path.join(BASE, "pin-destinations.md"), "w").write("\n".join(lines) + "\n")

    base = site.get("site_url", "").rstrip("/")
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        sm.append(f"  <url><loc>{esc(base + u)}</loc><lastmod>{date.today().isoformat()}</lastmod></url>")
    sm.append("</urlset>")
    open(os.path.join(OUT, "sitemap.xml"), "w").write("\n".join(sm))
    open(os.path.join(OUT, "robots.txt"), "w").write(
        f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n")

    print(f"wrote {len(written)} pages · {len(site['_posts'])} posts · "
          f"{len(site['categories'])} categories")


if __name__ == "__main__":
    main()
