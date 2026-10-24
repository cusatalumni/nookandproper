#!/usr/bin/env python3
"""Compose Pinterest pins (1000x1500) from an Amazon product photo.

Zero image-generation credits: deterministic layout over a real product photo.
Design v2 — editorial layout ported from Manoj's own redesign: display-serif
headline above the photo with the last phrase in italic accent, dark pill badge,
gold spec circle, bold sub-headline, CTA pill, legible affiliate disclosure.

    python3 pin_factory.py --image p.jpg --kicker "Kitchen & Air Fryer" \
        --headline "Dinner in 20 minutes, one drawer." --price "$70–120" \
        --spec "6 QT" --out pins/x.png
"""
import argparse
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1000, 1500
CREAM = (250, 246, 240)
INK = (30, 25, 21)
MUTED = (122, 111, 99)
ACCENT = (168, 89, 60)
GOLD = (224, 165, 62)
CARD = (255, 253, 250)

BASE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(BASE, "assets", "fonts")
SYS = ["/usr/share/fonts/truetype/liberation", "/usr/share/fonts/truetype/dejavu"]


def _load(name, size, weight=None):
    p = os.path.join(FONTS, name)
    if os.path.exists(p):
        f = ImageFont.truetype(p, size)
        if weight is not None:
            try:
                f.set_variation_by_axes([weight])
            except Exception:
                pass
        return f
    for d in SYS:
        for cand in ("LiberationSerif-Regular.ttf", "DejaVuSerif.ttf"):
            q = os.path.join(d, cand)
            if os.path.exists(q):
                return ImageFont.truetype(q, size)
    return ImageFont.load_default()


def display(size, weight=900):
    return _load("Playfair.ttf", size, weight)


def display_italic(size, weight=900):
    return _load("PlayfairItalic.ttf", size, weight)


def sans(size, bold=False):
    for d in SYS:
        for cand in (["LiberationSans-Bold.ttf", "DejaVuSans-Bold.ttf"] if bold
                     else ["LiberationSans-Regular.ttf", "DejaVuSans.ttf"]):
            q = os.path.join(d, cand)
            if os.path.exists(q):
                return ImageFont.truetype(q, size)
    return ImageFont.load_default()


def tracked(d, xy, text, fnt, fill, tracking=5):
    x, y = xy
    for c in text:
        d.text((x, y), c, font=fnt, fill=fill)
        x += d.textlength(c, font=fnt) + tracking
    return x


def wrap(d, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def rounded(d, box, r, fill, outline=None, width=1):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def cover(im, bw, bh):
    im = im.convert("RGB")
    sw, sh = im.size
    scale = max(bw / sw, bh / sh)
    im = im.resize((int(sw * scale + .5), int(sh * scale + .5)), Image.LANCZOS)
    if scale > 1.6:
        im = im.filter(ImageFilter.UnsharpMask(radius=2.2, percent=105, threshold=3))
    nw, nh = im.size
    return im.crop(((nw - bw) // 2, (nh - bh) // 2, (nw - bw) // 2 + bw, (nh - bh) // 2 + bh))


def split_headline(headline):
    """Last phrase carries the italic accent."""
    h = headline.strip().rstrip(".")
    if "," in h:
        a, b = h.split(",", 1)
        return a.strip() + ",", b.strip() + "."
    w = h.split()
    if len(w) <= 2:
        return "", h + "."
    return " ".join(w[:-2]), " ".join(w[-2:]) + "."


def compose(image_path, out_path, kicker, headline, price="", brand="kada finds",
            cta="Shop on Amazon", badge="", sub="", spec="", note=""):
    pin = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(pin)
    M = 72

    # --- kicker -------------------------------------------------------------
    tracked(d, (M, 56), kicker.upper(), sans(23, True), MUTED, tracking=5)

    # --- display headline: word-level flow so the italic accent never orphans --
    lead, accent = split_headline(headline)
    words = [(w, False) for w in lead.split()] + [(w, True) for w in accent.split()]
    max_w = W - 2 * M
    y = 104
    chosen = None
    for cand in (112, 104, 96, 88, 80, 72, 64, 58):
        hf, af = display(cand), display_italic(cand)
        lines, cur, curw = [], [], 0.0
        space = d.textlength(" ", font=hf)
        for w, is_acc in words:
            fnt = af if is_acc else hf
            ww = d.textlength(w + " ", font=fnt)
            if cur and curw + ww - space > max_w:
                lines.append(cur); cur, curw = [], 0.0
            cur.append((w, fnt, is_acc)); curw += ww
        if cur:
            lines.append(cur)
        if len(lines) <= 3:
            chosen = (cand, hf, af, lines)
            break
    cand, hf, af, lines = chosen
    lh = int(cand * 1.06)
    for ln in lines:
        x = M
        for w, fnt, is_acc in ln:
            d.text((x, y), w, font=fnt, fill=ACCENT if is_acc else INK)
            x += d.textlength(w + " ", font=fnt)
        y += lh

    # --- photo card ---------------------------------------------------------
    py = max(y + 30, 470)
    ph = min(700, 1150 - py)
    ix0, iy0, ix1, iy1 = M, py, W - M, py + ph
    rounded(d, [ix0, iy0, ix1, iy1], 22, fill=CARD)
    photo = cover(Image.open(image_path), ix1 - ix0 - 8, iy1 - iy0 - 8)
    mask = Image.new("L", photo.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, photo.size[0] - 1, photo.size[1] - 1], 19, fill=255)
    pin.paste(photo, (ix0 + 4, iy0 + 4), mask)

    if badge:
        bf = sans(25, True)
        bw = d.textlength(badge, font=bf) + 40
        rounded(d, [ix0 + 18, iy0 + 18, ix0 + 18 + bw, iy0 + 18 + 54], 27, fill=INK)
        d.text((ix0 + 38, iy0 + 30), badge, font=bf, fill=(255, 253, 250))

    # gold spec circle, overlapping the photo's bottom-right corner
    if spec or price:
        cx, cy, r = ix1 - 78, iy1 - 62, 84
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GOLD)
        sf = sans(24, True)
        if spec:
            sw = d.textlength(spec, font=sf)
            d.text((cx - sw / 2, cy - 46), spec, font=sf, fill=(50, 36, 12))
        size = 38
        for cand in (38, 34, 30, 26, 22, 18):
            size = cand
            pf = display(cand, 700)
            if d.textlength(price, font=pf) <= 2 * r - 22:
                break
        pf = display(size, 700)
        pw = d.textlength(price, font=pf)
        d.text((cx - pw / 2, cy - 12), price, font=pf, fill=(38, 26, 8))

    # brand mark
    mf = sans(19, True)
    mv = brand.upper()
    mw = d.textlength(mv, font=mf) + 26
    rounded(d, [ix0 + 16, iy1 - 44, ix0 + 16 + mw, iy1 - 12], 6, fill=(255, 253, 250))
    d.text((ix0 + 29, iy1 - 38), mv, font=mf, fill=(60, 50, 42))

    # --- sub-headline + note -----------------------------------------------
    y = iy1 + 38
    if sub:
        for cand in (46, 42, 38, 34, 30):
            sf2 = display(cand, 800)
            if d.textlength(sub, font=sf2) <= W - 2 * M:
                break
        d.text((M, y), sub, font=sf2, fill=INK)
        y += int(cand * 1.2)
    if note:
        y += 4
        nf = sans(28)
        for ln in wrap(d, note, nf, W - 2 * M)[:2]:
            d.text((M, y), ln, font=nf, fill=MUTED)
            y += 38

    # --- CTA -----------------------------------------------------------------
    by = 1300
    rounded(d, [M, by, W - M, by + 92], 46, fill=ACCENT)
    cf = sans(33, True)
    cw = d.textlength(cta, font=cf)
    d.text(((W - cw) / 2, by + 26), cta, font=cf, fill=(255, 253, 250))

    # --- disclosure (kept legible on purpose) --------------------------------
    ff = sans(23)
    foot = f"{brand} · Amazon Associate — we earn from qualifying purchases"
    fw = d.textlength(foot, font=ff)
    d.text(((W - fw) / 2, H - 46), foot, font=ff, fill=MUTED)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    pin.save(out_path, "PNG", optimize=True)
    return out_path


def main():
    ap = argparse.ArgumentParser()
    for f in ("image", "out", "headline"):
        ap.add_argument(f"--{f}", required=(f != "image") if False else True)
    for f in ("kicker", "price", "badge", "sub", "spec", "note", "cta", "brand"):
        ap.add_argument(f"--{f}", default="")
    a = ap.parse_args()
    print(compose(a.image, a.out, a.kicker, a.headline, a.price,
                  a.brand or "kada finds", a.cta or "Shop on Amazon",
                  a.badge, a.sub, a.spec, a.note))


if __name__ == "__main__":
    main()
