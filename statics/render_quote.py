"""Mon Mechanic daily quote card — clean minimal, 1080x1350 (4:5).
Usage: python3 render_quote.py <post.json> <out.jpg>
post.json: {
  "lines": ["কাউকে খুশি করতে গিয়ে", "নিজেকে <em>হারিয়ে</em> ফেলো না।"],   # 2–6 short lines, one <em> accent
  "lead": "optional small line above the quote (e.g. 'যাকে মনে পড়ছে, তাকে ট্যাগ করো')",
  "theme": "paper" | "mint" | "ink"      (rotate)
}
"""
import json, sys, pathlib, asyncio, subprocess
from playwright.async_api import async_playwright

HERE = pathlib.Path(__file__).resolve().parent
F = HERE / "node_modules/@fontsource"

def font(fam, file, w, style="normal"):
    return f"@font-face{{font-family:{fam};font-weight:{w};font-style:{style};src:url('file://{F}/{file}')}}"

CSS = "".join([
    font("Serif", "noto-serif-bengali/files/noto-serif-bengali-bengali-600-normal.woff2", 600),
    font("Serif", "noto-serif-bengali/files/noto-serif-bengali-bengali-700-normal.woff2", 700),
    font("Ital", "tiro-bangla/files/tiro-bangla-bengali-400-italic.woff2", 400, "italic"),
    font("Hind", "hind-siliguri/files/hind-siliguri-bengali-500-normal.woff2", 500),
    font("Anek", "anek-bangla/files/anek-bangla-bengali-700-normal.woff2", 700),
]) + """
:root{--teal:#0F4A44;--teal2:#1E8A7A;--y:#FFC531;--paper:#FBF8F2;--mint:#E3F2EE;--ink:#0F2E2B}
*{margin:0;box-sizing:border-box}
body{width:1080px;height:1350px;overflow:hidden}
.c{width:1080px;height:1350px;position:relative;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:0 110px;text-align:center}
.paper{background:var(--paper);color:var(--ink)}
.mint{background:var(--mint);color:var(--ink)}
.ink{background:var(--teal);color:#F4FBF9}
.mark{font:400 150px/0.6 Ital;color:var(--teal2);opacity:.35;height:70px}
.ink .mark{color:var(--y);opacity:.6}
.q{font:700 66px/1.6 Serif;letter-spacing:-.005em}
.q.s{font-size:58px}.q.xs{font-size:52px}
.q em{font-style:normal;color:var(--teal2);position:relative}
.ink .q em{color:var(--y)}
.lead{font:500 30px Hind;color:#6B7D79;margin-bottom:44px;letter-spacing:.01em}
.ink .lead{color:#9FC4BD}
.rule{width:64px;height:4px;border-radius:4px;background:var(--y);margin-top:56px}
.foot{position:absolute;bottom:64px;left:0;right:0;display:flex;justify-content:center;align-items:center;gap:14px;font:700 30px Anek;color:var(--teal)}
.ink .foot{color:#F4FBF9}
.foot i{width:14px;height:14px;border-radius:50%;background:var(--y);display:inline-block}
.foot span{font:500 24px Hind;color:#7F928E;margin-left:6px}
.ink .foot span{color:#9FC4BD}
"""

def html(p):
    lines = p["lines"]; n = sum(len(l) for l in lines)
    size = "" if n < 110 else ("s" if n < 160 else "xs")
    lead = f'<div class="lead">{p["lead"]}</div>' if p.get("lead") else ""
    body = "<br>".join(lines)
    return f"""<html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="c {p.get('theme','paper')}">{lead}<div class="mark">“</div><div class="q {size}">{body}</div><div class="rule"></div>
<div class="foot"><i></i>মন মেকানিক<span>@mon.mechanic1</span></div></div></body></html>"""

async def main(src, out):
    p = json.loads(pathlib.Path(src).read_text())
    tmp = pathlib.Path(out).with_suffix(".html"); tmp.write_text(html(p))
    async with async_playwright() as pw:
        b = await pw.chromium.launch(); pg = await b.new_page(viewport={"width":1080,"height":1350})
        await pg.goto(f"file://{tmp.resolve()}"); await pg.wait_for_timeout(400)
        png = pathlib.Path(out).with_suffix(".png"); await pg.screenshot(path=str(png)); await b.close()
    tmp.unlink()
    subprocess.run(["python3","-c",f"from PIL import Image;Image.open('{png}').convert('RGB').save('{out}',quality=90)"],check=True)
    png.unlink()

if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], sys.argv[2]))
