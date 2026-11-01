# Mon Mechanic — daily static quote post (from 2 Nov 2026)

One static a day, 10:00 pm Dhaka, Facebook + Instagram, fully automatic (Fahad: no approval).
Goal: lines people **share** or **tag someone** on. Reference style (Fahad, 1 Nov): simple Bangla
quote cards about people, self-respect and dua-like hope — but clean and minimal, our brand.

## Copy
- Original lines only, written fresh. Never attribute a line to a real person, scholar or book,
  never invent hadith/Quran text or "— someone said". No religious rulings, no politics.
- 2–5 short lines, max ~140 characters. One phrase wrapped in `<em>` (the emotional turn).
- Natural, warm Bangla (তুমি form, like the reference). No cringe, no hate toward any group,
  no gender-blaming ("মেয়েরা/ছেলেরা এমনই"), nothing that glorifies self-harm or revenge.
- Rotate pillars (never the same pillar two days running):
  1. বন্ধুত্ব — tag-a-friend lines
  2. আত্মসম্মান — self-respect, people-pleasing, boundaries
  3. পরিবার — মা/বাবা/ভাইবোন
  4. সম্পর্ক — care, missing someone, loyalty (not toxic)
  5. মনের শান্তি — overthinking, letting go, hope
  6. জীবনের শিক্ষা — struggle, patience, small wins
- Optional `lead` (small line above) = the share/tag trigger, e.g. "যাকে মনে পড়লো, তাকে ট্যাগ করো",
  "যার জন্য সত্যি, তাকে পাঠিয়ে দাও". Use on roughly half the posts, not every day.
- Caption: 1 short line expanding the feeling + a tag/share ask + 3–5 hashtags incl.
  #monmechanic #মনমেকানিক.

## Design (render_quote.py — don't restyle)
1080×1350, themes rotate paper → mint → ink. Look at the JPG before queueing: no overflow,
Bangla joins correct, em accent visible.

## Run
1. Read log.md; pick tomorrow's pillar + theme; check the line isn't close to anything in the last 60 days.
2. Write posts/<date>.json → `cd statics && npm i && python3 render_quote.py posts/<date>.json ../media/mon-mechanic/<date>_Q.jpg`.
3. queue/mon-mechanic/<date>_Q.json: {"publish_at":"<date>T22:00:00+06:00","image":"media/mon-mechanic/<date>_Q.jpg","caption":"…"}.
4. Append to log.md: date | pillar | theme | first line. Commit + push.

examples: samples/example_paper.jpg, samples/example_ink.jpg
