"""ESP carousel builder.

Usage: python3 build.py briefs/<name>.json
Renders every slide in the brief to out/<id>/NN.jpg at 1080x1350 (4:5),
plus a contact sheet out/<id>/sheet.jpg for review.

Brief format (see briefs/08-early-access.json):
  slides[].layout  cover | feature | cta
  slides[].theme   navy | light | tint
  headline         wrap words in *asterisks* to colour them Brand Blue
  screen           a file in assets/screens/ shown in a browser frame
  app_url          OPTIONAL text for the browser address bar. Leave it out:
                   the app link stays hidden until Abi says to reveal it.
  callout          optional label over the screen (bottom left)
  chips            optional list of 2-4 short feature cards instead of a screen
"""
import base64, html, json, pathlib, re, sys
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).parent
W, H = 1080, 1350
# Green Room palette (Brand Guide v3): Brand Blue #1B4DB1, Navy #0A1F3C
BRAND = {"navy": "#0A1F3C", "blue": "#1B4DB1", "tint": "#EEF3FC", "white": "#FFFFFF",
         "ink": "#0A1F3C", "muted": "#4F5966", "sky": "#8DB0F2"}

def b64(path):
    return base64.b64encode(path.read_bytes()).decode()

def font_face(name, file, weight):
    fmt = "opentype" if file.endswith(".otf") else "truetype"
    return (f"@font-face{{font-family:'{name}';src:url(data:font/{fmt};base64,"
            f"{b64(ROOT/'assets/fonts'/file)}) format('{fmt}');font-weight:{weight};}}")

FONTS = "".join([
    font_face("Jakarta", "PlusJakartaSans-Medium.ttf", 500),
    font_face("Jakarta", "PlusJakartaSans-Bold.ttf", 700),
    font_face("Jakarta", "PlusJakartaSans-ExtraBold.ttf", 800),
    font_face("Inter", "Inter-Medium.otf", 500),
    font_face("Inter", "Inter-SemiBold.otf", 600),
])

LOGO_SVG = (ROOT / "assets/logo.svg").read_text()
LOGO_SVG = re.sub(r"<metadata>.*?</metadata>", "", LOGO_SVG, flags=re.S)

def logo(theme):
    svg = LOGO_SVG
    if theme == "navy":  # white wordmark on dark slides, light-blue mark
        svg = svg.replace('fill="#021a37"', 'fill="#FFFFFF"').replace('fill="#0155a8"', f'fill="{BRAND["sky"]}"')
    else:  # recolour the logo file's old palette to Green Room
        svg = svg.replace('fill="#021a37"', f'fill="{BRAND["navy"]}"').replace('fill="#0155a8"', f'fill="{BRAND["blue"]}"')
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()

def rich(text):
    """*words* -> highlighted span."""
    esc = html.escape(text.replace("'", "\u2019"), quote=False)
    return re.sub(r"\*(.+?)\*", r'<span class="hl">\1</span>', esc)

def screen(name, fit="wide", url=""):
    p = ROOT / "assets/screens" / name
    mime = "image/png" if p.suffix == ".png" else "image/jpeg"
    cls = "browser narrow" if fit == "narrow" else "browser"
    return (f'<div class="{cls}"><div class="bar"><i></i><i></i><i></i>'
            + (f'<span>{html.escape(url)}</span>' if url else '') + '</div>'
            f'<img src="data:{mime};base64,{b64(p)}" alt=""></div>')

CSS = f"""
{FONTS}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:{W}px;height:{H}px}}
.slide{{width:{W}px;height:{H}px;position:relative;overflow:hidden;font-family:Inter,sans-serif;
  display:flex;flex-direction:column;padding:72px 80px 0}}
.light{{background:{BRAND['white']};color:{BRAND['ink']}}}
.tint{{background:{BRAND['tint']};color:{BRAND['ink']}}}
.navy{{background:{BRAND['navy']};color:{BRAND['white']}}}
.top{{display:flex;justify-content:space-between;align-items:center;height:64px}}
.top img{{height:84px}}
.count{{font:600 26px Inter;opacity:.55;letter-spacing:.02em}}
.kicker{{margin-top:64px;font:700 26px Jakarta;letter-spacing:.08em;text-transform:uppercase;color:{BRAND['blue']}}}
.navy .kicker{{color:{BRAND['sky']}}}
h1{{font:800 84px/1.04 Jakarta;letter-spacing:-.02em;margin-top:22px;text-wrap:balance}}
.hl{{color:{BRAND['blue']}}}
.navy .hl{{color:{BRAND['sky']}}}
p.body{{font:500 34px/1.4 Inter;margin-top:28px;max-width:880px;opacity:.82}}
.pill{{align-self:flex-start;margin-top:72px;font:700 26px Jakarta;padding:12px 26px;border-radius:999px;
  background:{BRAND['blue']};color:#fff}}
.cover h1{{font-size:104px;margin-top:30px}}
.stage{{flex:1;position:relative;margin-top:48px}}
.browser{{position:absolute;left:0;right:-80px;top:0;border-radius:18px 0 0 0;overflow:hidden;
  background:#fff;box-shadow:0 30px 80px rgba(2,25,56,.22);border:2px solid rgba(2,25,56,.08)}}
.browser.narrow{{right:auto;left:50%;transform:translateX(-50%);width:520px;border-radius:18px 18px 0 0}}
.bar{{height:52px;background:#F3F5F9;display:flex;align-items:center;gap:12px;padding:0 22px;border-bottom:1px solid #E3E8EF}}
.bar i{{width:14px;height:14px;border-radius:50%;background:#D5DCE6;display:block}}
.bar span{{margin-left:18px;font:500 20px Inter;color:#7A879A}}
.browser img{{display:block;width:100%;height:auto}}
.foot{{position:absolute;left:0;right:0;bottom:0;height:96px;display:flex;align-items:center;
  justify-content:space-between;padding:0 80px;background:{BRAND['navy']};color:#fff;font:600 28px Inter;z-index:5}}
.navy .foot{{background:{BRAND['blue']}}}
.foot b{{font:700 28px Jakarta}}
.swipe{{position:absolute;right:80px;bottom:132px;font:700 28px Jakarta;color:{BRAND['sky']};z-index:6}}
.cta{{justify-content:flex-start}}
.cta h1{{font-size:120px;margin-top:220px}}
.button{{align-self:flex-start;margin-top:56px;background:#fff;color:{BRAND['navy']};font:800 40px Jakarta;
  padding:26px 44px;border-radius:16px}}
.callout{{position:absolute;left:28px;bottom:150px;background:{BRAND['navy']};color:#fff;font:700 30px Jakarta;
  padding:18px 28px;border-radius:14px;box-shadow:0 16px 40px rgba(2,25,56,.3);z-index:4}}
.chips{{display:grid;grid-template-columns:1fr 1fr;gap:28px;margin-top:80px}}
.chip{{background:#fff;border:2px solid rgba(2,25,56,.1);border-radius:20px;padding:64px 40px;font:800 42px Jakarta;
  display:flex;flex-direction:column;gap:22px;box-shadow:0 14px 40px rgba(2,25,56,.08)}}
.chip .dot{{font:700 24px Inter;color:{BRAND['blue']};letter-spacing:.06em}}
.note{{margin-top:auto;margin-bottom:150px;font:600 28px Inter;opacity:.6}}
"""

def slide_html(s, i, n, cta):
    t = s.get("theme", "light")
    parts = [f'<div class="slide {t} {s["layout"]}">',
             f'<div class="top"><img src="{logo(t)}" alt="EventSpacePro"><span class="count">{i}/{n}</span></div>']
    if s.get("pill"): parts.append(f'<div class="pill">{html.escape(s["pill"])}</div>')
    if s.get("kicker"): parts.append(f'<div class="kicker">{html.escape(s["kicker"])}</div>')
    parts.append(f'<h1>{rich(s["headline"])}</h1>')
    if s.get("body"): parts.append(f'<p class="body">{html.escape(s["body"].replace(chr(39), chr(8217)), quote=False)}</p>')
    if s.get("button"): parts.append(f'<div class="button">{html.escape(s["button"])}</div>')
    if s.get("note"): parts.append(f'<div class="note">{html.escape(s["note"])}</div>')
    if s.get("screen"):
        call = f'<div class="callout">{html.escape(s["callout"])}</div>' if s.get("callout") else ""
        parts.append(f'<div class="stage">{screen(s["screen"], s.get("screen_fit","wide"), s.get("app_url", ""))}{call}</div>')
    if s.get("chips"):
        parts.append('<div class="chips">' + "".join(
            f'<div class="chip"><span class="dot">{k+1:02d}</span>{html.escape(c)}</div>' for k, c in enumerate(s["chips"])) + '</div>')
    if s.get("swipe"): parts.append('<div class="swipe">Swipe →</div>')
    parts.append(f'<div class="foot"><span>eventspacepro.com</span><b>{html.escape(cta)} →</b></div></div>')
    return f'<!DOCTYPE html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>{"".join(parts)}</body></html>'

def main(brief_path):
    brief = json.loads(pathlib.Path(brief_path).read_text())
    out = ROOT / "out" / brief["id"]; out.mkdir(parents=True, exist_ok=True)
    n = len(brief["slides"]); files = []
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        pg = b.new_page(viewport={"width": W, "height": H})
        for i, s in enumerate(brief["slides"], 1):
            pg.set_content(slide_html(s, i, n, brief.get("footer_cta", "Early access now open")), wait_until="load")
            pg.evaluate("document.fonts.ready")
            f = out / f"{i:02d}.jpg"; pg.screenshot(path=str(f), type="jpeg", quality=92); files.append(f)
        b.close()
    from PIL import Image
    thumbs = [Image.open(f).resize((360, 450)) for f in files]
    sheet = Image.new("RGB", (360 * len(thumbs) + 20 * (len(thumbs) + 1), 490), "#CCD3DE")
    for k, t in enumerate(thumbs): sheet.paste(t, (20 + k * 380, 20))
    sheet.save(out / "sheet.jpg", quality=88)
    print("rendered", len(files), "slides ->", out)

if __name__ == "__main__":
    main(sys.argv[1])
