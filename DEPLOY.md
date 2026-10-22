# Deploying Nook & Proper

## 1. GitHub (5 minutes)

1. github.com → New repository → name it `nookandproper` → **Public** → Create.
2. On the empty repo page click **uploading an existing file**.
3. Unzip the package, then drag the **contents** of the folder into the upload box
   (select all the files and the `content`, `assets`, `out` folders together).
4. Commit.

## 2. Vercel (3 minutes)

1. vercel.com → Add New → **Project** → import `nookandproper`.
2. Framework Preset: **Other**. Build Command: **leave empty**. Output Directory: **out**.
3. Deploy.

The site is live at `nookandproper.vercel.app`. Every push to `main` redeploys.

## 3. Why the project must be named `nookandproper`

The Vercel project name becomes the subdomain. Name the project anything else and the
address becomes `<name>.vercel.app`; the canonical URL and OG tags in `content/site.json`
(`site_url`) would then be wrong. Change it there and rebuild if you rename.

## Day-to-day

```
python3 daily.py --post     # today's 3 pins
python3 add_post.py --cat <cat> --title "..." --body "..." --pin x.png --link "..." --price "..."
python3 build.py
git add -A && git commit -m "daily pins" && git push
```
