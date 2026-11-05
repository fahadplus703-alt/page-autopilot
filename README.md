# page-autopilot

Free auto-poster and comment replier for Ajaira Gyan, Mon Mechanic and Doodle Logic (Facebook + Instagram), running on GitHub Actions.

- `queue/<page>/*.json` — Reels waiting to post (`publish_at`, `video`, `cover`, `caption`). Checked every 15 minutes.
- `media/<page>/` — the video and cover files. Deleted automatically once posted.
- `posted/<page>/` — record of what went out, with Facebook/Instagram ids.
- Comments are answered every 10 minutes by Gemini in each page's voice; spam is skipped.

Secrets (Settings → Secrets → Actions): `AG_PAGE_TOKEN`, `MM_PAGE_TOKEN`, `DL_PAGE_TOKEN`, `GEMINI_API_KEY`.
Run **Actions → Check page connections** after adding tokens to confirm both pages and their Instagram accounts are reachable.
