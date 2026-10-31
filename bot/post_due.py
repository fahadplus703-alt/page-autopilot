"""Publish every queued Reel whose publish_at time has passed.

Queue item: queue/<page-slug>/<anything>.json
{
  "publish_at": "2026-11-01T09:00:00+06:00",
  "video": "media/mon-mechanic/2026-11-01_0900.mp4",
  "cover": "media/mon-mechanic/2026-11-01_0900.jpg",     (optional, Instagram cover)
  "caption": "...",
  "post_to": ["facebook", "instagram"]                   (optional, defaults to the page config)
}
Posted items move to posted/<page-slug>/ with the returned ids; failures stay queued with an "errors" list.
"""
import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from graph import call, page_info, token_for, GraphError  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
REPO = os.environ.get("GITHUB_REPOSITORY", "fahadplus703-alt/page-autopilot")
BRANCH = os.environ.get("MEDIA_BRANCH", "main")


def raw_url(rel):
    return f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{rel}"


def post_facebook_reel(info, token, video_url, caption):
    pid = info["page_id"]
    start = call("POST", f"{pid}/video_reels", token, upload_phase="start")
    vid = start["video_id"]
    import requests
    up = requests.post(start["upload_url"], headers={"Authorization": f"OAuth {token}", "file_url": video_url},
                       timeout=120)
    if up.status_code >= 400:
        raise GraphError(f"FB reel upload failed: {up.text[:300]}")
    call("POST", f"{pid}/video_reels", token, upload_phase="finish", video_id=vid,
         video_state="PUBLISHED", description=caption)
    return vid


def post_instagram_reel(info, token, video_url, caption, cover_url=None):
    ig = info["ig_id"]
    if not ig:
        raise GraphError("no Instagram business account linked to this page")
    params = dict(media_type="REELS", video_url=video_url, caption=caption, share_to_feed="true")
    if cover_url:
        params["cover_url"] = cover_url
    container = call("POST", f"{ig}/media", token, **params)["id"]
    for _ in range(60):  # up to ~10 minutes of processing
        st = call("GET", container, token, fields="status_code,status")
        if st.get("status_code") == "FINISHED":
            break
        if st.get("status_code") == "ERROR":
            raise GraphError(f"IG processing error: {st.get('status')}")
        time.sleep(10)
    else:
        raise GraphError("IG processing timed out")
    return call("POST", f"{ig}/media_publish", token, creation_id=container)["id"]


def main():
    pages = json.loads((ROOT / "config/pages.json").read_text())
    now = datetime.now(timezone.utc)
    posted_any = False
    for slug, cfg in pages.items():
        qdir = ROOT / "queue" / slug
        if not qdir.exists():
            continue
        items = sorted(qdir.glob("*.json"))
        due = []
        for f in items:
            item = json.loads(f.read_text())
            if datetime.fromisoformat(item["publish_at"]) <= now:
                due.append((f, item))
        if not due:
            continue
        try:
            token = token_for(cfg)
            info = page_info(token)
        except GraphError as e:
            print(f"[{slug}] cannot post: {e}")
            continue
        for f, item in due:
            results, errors = item.get("results", {}), []
            video_url = raw_url(item["video"])
            cover_url = raw_url(item["cover"]) if item.get("cover") else None
            for net in item.get("post_to", cfg["post_to"]):
                if net in results:
                    continue
                try:
                    if net == "facebook":
                        results[net] = post_facebook_reel(info, token, video_url, item["caption"])
                    elif net == "instagram":
                        results[net] = post_instagram_reel(info, token, video_url, item["caption"], cover_url)
                    print(f"[{slug}] {f.name} -> {net} ok ({results[net]})")
                except GraphError as e:
                    errors.append(f"{now.isoformat()} {net}: {e}")
                    print(f"[{slug}] {f.name} -> {net} FAILED: {e}")
            item["results"] = results
            if errors:
                item.setdefault("errors", []).extend(errors)
                item["attempts"] = item.get("attempts", 0) + 1
            targets = item.get("post_to", cfg["post_to"])
            if all(n in results for n in targets) or item.get("attempts", 0) >= 3:
                item["posted_at"] = now.isoformat()
                dest = ROOT / "posted" / slug
                dest.mkdir(parents=True, exist_ok=True)
                (dest / f.name).write_text(json.dumps(item, ensure_ascii=False, indent=2))
                f.unlink()
                # free repo space: media is no longer needed once posted everywhere
                if all(n in results for n in targets):
                    for key in ("video", "cover"):
                        p = ROOT / item[key] if item.get(key) else None
                        if p and p.exists():
                            p.unlink()
            else:
                f.write_text(json.dumps(item, ensure_ascii=False, indent=2))
            posted_any = True
    print("done" if posted_any else "nothing due")


if __name__ == "__main__":
    main()
