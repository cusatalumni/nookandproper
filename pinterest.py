#!/usr/bin/env python3
"""Talk to Pinterest through our own Vercel endpoints, so the app secret and the
refresh token stay in Vercel's environment and never live in this sandbox.

Env: NP_API_KEY   (the same value set in Vercel)
     NP_BASE      (optional, defaults to https://nookandproper.vercel.app)
"""
import argparse, base64, json, os, sys, urllib.error, urllib.request

BASE = os.environ.get("NP_BASE", "https://nookandproper.vercel.app").rstrip("/")
KEY = os.environ.get("NP_API_KEY", "")


def _call(path, data=None):
    if not KEY:
        sys.exit("NP_API_KEY is not set in this environment")
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(
        BASE + path, data=body,
        headers={"x-api-key": KEY, "Content-Type": "application/json"},
        method="POST" if data is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        return {"_http": e.code, "_body": e.read().decode()[:500]}


def boards():
    return _call("/api/pinterest/boards")


def pin(board_id, title, description, link, image_url=None, image_file=None):
    payload = {"board_id": board_id, "title": title, "description": description, "link": link}
    if image_file:
        ext = image_file.lower().rsplit(".", 1)[-1]
        payload["content_type"] = "image/png" if ext == "png" else "image/jpeg"
        payload["image_base64"] = base64.b64encode(open(image_file, "rb").read()).decode()
    else:
        payload["image_url"] = image_url
    return _call("/api/pinterest/pin", payload)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["boards", "pin", "selftest"])
    ap.add_argument("--board-id"); ap.add_argument("--title"); ap.add_argument("--description", default="")
    ap.add_argument("--link"); ap.add_argument("--image-url"); ap.add_argument("--image-file")
    a = ap.parse_args()
    if a.cmd == "selftest":
        r = _call("/api/pinterest/boards")
        print("key accepted, boards:" if isinstance(r, list) else "response:", r)
    elif a.cmd == "boards":
        r = boards()
        for b in (r if isinstance(r, list) else []):
            print(f'{b["id"]}  {b["name"]}')
        if not isinstance(r, list):
            print(r)
    elif a.cmd == "pin":
        print(json.dumps(pin(a.board_id, a.title, a.description, a.link,
                             image_url=a.image_url, image_file=a.image_file), indent=2)[:700])


if __name__ == "__main__":
    main()
