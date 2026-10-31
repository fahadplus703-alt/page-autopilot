"""Small Meta Graph API helper used by the poster and the comment replier."""
import os
import time
import requests

API = "https://graph.facebook.com/v23.0"


class GraphError(RuntimeError):
    pass


def call(method, path, token, **params):
    params["access_token"] = token
    url = path if path.startswith("http") else f"{API}/{path.lstrip('/')}"
    for attempt in range(3):
        r = requests.request(method, url, data=params if method == "POST" else None,
                             params=params if method != "POST" else None, timeout=60)
        if r.status_code < 500:
            break
        time.sleep(5 * (attempt + 1))
    data = r.json() if r.content else {}
    if r.status_code >= 400 or "error" in data:
        msg = data.get("error", {}).get("message", r.text[:300])
        raise GraphError(f"{method} {path}: {msg}")
    return data


def page_info(token):
    """Page id, name and linked Instagram business account id, read from the page token itself."""
    me = call("GET", "me", token, fields="id,name,instagram_business_account")
    return {
        "page_id": me["id"],
        "name": me.get("name"),
        "ig_id": (me.get("instagram_business_account") or {}).get("id"),
    }


def token_for(cfg):
    tok = os.environ.get(cfg["token_secret"], "").strip()
    if not tok:
        raise GraphError(f"secret {cfg['token_secret']} is not set")
    return tok
