"""Reply to new comments on recent Facebook and Instagram posts of each page.

Replies are written by Google Gemini (free tier) in the page's persona and language.
Skips: the page's own comments, spam (links, promo words), and anything already handled.
State lives in state/replied.json so nothing is answered twice.
"""
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from graph import call, page_info, token_for, GraphError  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state" / "replied.json"
LOOKBACK_DAYS = 7
SPAM = re.compile(r"(https?://|www\.|\.com\b|t\.me/|whats\s?app|dm me|inbox me|earn \$|crypto|forex|bitcoin|"
                  r"follow (me|back)|f4f|promo|giveaway|৳\s?\d{3,}|ইনবক্স|লিংকে|bit\.ly)", re.I)


def ai_reply(cfg, post_caption, comment):
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        return None
    prompt = (f"You manage the social page described as: {cfg['persona']}\n"
              f"Reply language: {cfg['reply_language']}.\n"
              f"Post caption: {post_caption[:400]}\n"
              f"Comment from a follower: {comment[:500]}\n\n"
              "Write ONE short, friendly, human reply (max 25 words). Answer questions briefly and honestly; "
              "if you are unsure of a fact, say so. Never ask for money, phone numbers or DMs. "
              "No hashtags, no links. Output only the reply text.")
    r = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}",
        json={"contents": [{"parts": [{"text": prompt}]}],
              "generationConfig": {"temperature": 0.8, "maxOutputTokens": 120}}, timeout=60)
    if r.status_code >= 400:
        print("gemini error", r.text[:200])
        return None
    try:
        text = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError):
        return None
    return text.strip('"').strip()


def recent(ts):
    t = datetime.fromisoformat(ts.replace("+0000", "+00:00"))
    return t > datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)


def handle_facebook(cfg, token, info, done):
    pid = info["page_id"]
    data = call("GET", f"{pid}/feed", token, limit=25,
                fields="id,message,created_time,comments.limit(50){id,message,from,created_time,comment_count}")
    for post in data.get("data", []):
        if not recent(post["created_time"]):
            continue
        for c in post.get("comments", {}).get("data", []):
            cid = c["id"]
            if cid in done or (c.get("from") or {}).get("id") == pid:
                continue
            text = c.get("message", "")
            done[cid] = "skip"
            if not text.strip() or SPAM.search(text):
                continue
            reply = ai_reply(cfg, post.get("message", ""), text)
            if reply:
                call("POST", f"{cid}/comments", token, message=reply)
                done[cid] = "fb"
                print(f"[{cfg['name']}] FB reply to {cid}: {reply}")


def handle_instagram(cfg, token, info, done):
    ig = info.get("ig_id")
    if not ig:
        return
    data = call("GET", f"{ig}/media", token, limit=25,
                fields="id,caption,timestamp,comments.limit(50){id,text,username,timestamp}")
    me = call("GET", ig, token, fields="username").get("username")
    for m in data.get("data", []):
        if not recent(m["timestamp"]):
            continue
        for c in m.get("comments", {}).get("data", []):
            cid = c["id"]
            if cid in done or c.get("username") == me:
                continue
            text = c.get("text", "")
            done[cid] = "skip"
            if not text.strip() or SPAM.search(text):
                continue
            reply = ai_reply(cfg, m.get("caption", ""), text)
            if reply:
                call("POST", f"{cid}/replies", token, message=f"@{c.get('username')} {reply}")
                done[cid] = "ig"
                print(f"[{cfg['name']}] IG reply to {cid}: {reply}")


def main():
    pages = json.loads((ROOT / "config/pages.json").read_text())
    STATE.parent.mkdir(exist_ok=True)
    done = json.loads(STATE.read_text()) if STATE.exists() else {}
    for slug, cfg in pages.items():
        if not cfg.get("auto_reply"):
            continue
        try:
            token = token_for(cfg)
            info = page_info(token)
        except GraphError as e:
            print(f"[{slug}] skipped: {e}")
            continue
        for fn in (handle_facebook, handle_instagram):
            try:
                fn(cfg, token, info, done)
            except GraphError as e:
                print(f"[{slug}] {fn.__name__} error: {e}")
    # keep the state file small
    if len(done) > 5000:
        done = dict(list(done.items())[-3000:])
    STATE.write_text(json.dumps(done, indent=0))


if __name__ == "__main__":
    main()
