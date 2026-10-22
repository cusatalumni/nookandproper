#!/usr/bin/env python3
"""Pinterest API helper: refresh the access token, list boards, create a pin.

Token file: ~/agent-state/.secrets/pinterest.json  (refresh token from the OAuth callback)
Env:        PINTEREST_APP_ID, PINTEREST_APP_SECRET   (for refreshing)
"""
import argparse, json, os, sys, urllib.parse, urllib.request

TOK = os.path.expanduser("~/agent-state/.secrets/pinterest.json")
API = "https://api.pinterest.com/v5"


def _req(url, data=None, headers=None, method=None):
    body = None
    if data is not None:
        if isinstance(data, dict) and not headers.get("Content-Type", "").startswith("application/json"):
            body = urllib.parse.urlencode(data).encode()
        elif isinstance(data, dict):
            body = json.dumps(data).encode()
        else:
            body = data
    r = urllib.request.Request(url, data=body, headers=headers or {}, method=method)
    with urllib.request.urlopen(r, timeout=30) as resp:
        raw = resp.read().decode()
    return json.loads(raw) if raw else {}


def refresh():
    tok = json.load(open(TOK))
    cid, sec = os.environ.get("PINTEREST_APP_ID"), os.environ.get("PINTEREST_APP_SECRET")
    if not cid or not sec:
        sys.exit("PINTEREST_APP_ID / PINTEREST_APP_SECRET not set in the environment")
    import base64
    basic = base64.b64encode(f"{cid}:{sec}".encode()).decode()
    j = _req(API + "/oauth/token", {"grant_type": "refresh_token", "refresh_token": tok["refresh_token"]},
             {"Authorization": "Basic " + basic, "Content-Type": "application/x-www-form-urlencoded"})
    if "access_token" not in j:
        sys.exit(f"refresh failed: {j}")
    tok["access_token"] = j["access_token"]
    if j.get("refresh_token"):
        tok["refresh_token"] = j["refresh_token"]
    os.makedirs(os.path.dirname(TOK), exist_ok=True)
    json.dump(tok, open(TOK, "w"), indent=2)
    os.chmod(TOK, 0o600)
    return tok["access_token"]


def boards():
    at = refresh()
    j = _req(API + "/boards?page_size=100", headers={"Authorization": "Bearer " + at})
    return j.get("items", [])


def create_board(name, description=""):
    at = refresh()
    return _req(API + "/boards", {"name": name, "description": description},
                {"Authorization": "Bearer " + at, "Content-Type": "application/json"})


def pin(board_id, image_url, title, description, link):
    at = refresh()
    body = {"board_id": board_id, "media_source": {"source_type": "image_url", "url": image_url},
            "title": title[:100], "description": description[:800], "link": link}
    return _req(API + "/pins", body,
                {"Authorization": "Bearer " + at, "Content-Type": "application/json"})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["boards", "create-board", "pin", "token"])
    ap.add_argument("--name"); ap.add_argument("--board-id"); ap.add_argument("--image-url")
    ap.add_argument("--title"); ap.add_argument("--description", default=""); ap.add_argument("--link")
    a = ap.parse_args()
    if a.cmd == "token":
        print("ok — access token refreshed")
    elif a.cmd == "boards":
        for b in boards():
            print(f'{b["id"]}  {b["name"]}')
    elif a.cmd == "create-board":
        print(json.dumps(create_board(a.name), indent=2)[:400])
    elif a.cmd == "pin":
        print(json.dumps(pin(a.board_id, a.image_url, a.title, a.description, a.link), indent=2)[:600])


if __name__ == "__main__":
    main()
