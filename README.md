# Kada Finds — pin blog

Static affiliate site. `build.py` renders `content/` into `out/`, which Vercel serves.

## How it fits together

| File | Job |
|---|---|
| `content/site.json` | brand, tag, the five category articles |
| `content/queue.json` | the 20-product queue: headline, price, spec, image, link, status |
| `content/feed.json` | the daily posts shown under each category |
| `pin_factory.py` | composites a 1000×1500 pin from a product photo (no image credits) |
| `daily.py` | `--plan` / `--run` / `--post` — the daily rotation |
| `add_post.py` | appends one daily blog post |
| `build.py` | renders `out/index.html` |
| `out/` | **the deployed site** — commit this |

## Deploy (Vercel via GitHub)

1. Create the GitHub repo, push this folder.
2. Vercel → Add New → Project → import the repo.
3. Framework preset: **Other**. Build command: **empty**. Output directory: **out**.
4. Deploy. Every push to `main` redeploys automatically.

## Daily run

```
python3 daily.py --post      # today's 3 pins (marks them posted)
python3 add_post.py ...      # one blog paragraph per pin
python3 build.py             # rebuild out/
git add -A && git commit -m "daily pins" && git push
```
