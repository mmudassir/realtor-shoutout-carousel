#!/usr/bin/env python3
"""Render a three slide Instagram shoutout carousel and refuse to pass it until it is clean.

Usage: python3 render.py spec.json --out out/
Exit code 1 when any check fails. Nothing should be posted from a failed run.
"""
import argparse, base64, html, io, json, os, sys
from PIL import Image

W, H = 1080, 1350
MARGIN = 72
# Instagram draws over these corners in the app: the 1/3 slide counter and the tag icon.
IG_COUNTER = (880, 0, W, 130)
IG_TAG = (0, 1260, 120, H)
GRID_CROP = 34  # the profile grid trims a 4:5 post to 3:4, about 34px a side
BODY_FLOOR = 40  # px; smaller content text is unreadable at phone size
HEADLINE_WORDS, BODY_WORDS = 8, 30
CONTENT = ".h,.body,.ask,.sub,.bn,.br,.reason,.bd"
CHROME = ".tm,.lane,.gr,.sig,.prog,.duo,.hl,.site,.bs,.os"


def data_uri(path, height):
    im = Image.open(path).convert("RGBA")
    im = im.crop(im.getbbox())
    im = im.resize((max(1, int(im.width * height / im.height)), height), Image.LANCZOS)
    b = io.BytesIO()
    im.save(b, "PNG")
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


def esc(s):
    return html.escape(s or "")


def headline(title, mark):
    t = esc(title)
    if mark:
        t = t.replace(esc(mark), f"<mark>{esc(mark)}</mark>", 1)
    return t.replace("\n", "<br>")


def css(c):
    return f"""*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#ccc;font-family:'DM Sans',-apple-system,'Helvetica Neue',sans-serif}}
.c{{width:{W}px;height:{H}px;position:relative;overflow:hidden;background:{c['ground']};color:{c['ink']}}}
.tm{{position:absolute;top:60px;left:{MARGIN}px;height:120px}}
.lane{{position:absolute;top:140px;right:{MARGIN}px;display:flex;align-items:center;gap:16px;font-family:'Courier New',monospace;font-size:26px;white-space:nowrap}}
.lane .tag{{background:{c['ink']};color:{c['ground']};padding:8px 16px 8px 14px;border-radius:6px;font-weight:700;letter-spacing:3px;border-left:8px solid {c['accent']}}}
.lane .num{{letter-spacing:2px;color:{c['muted']}}}
.gr{{position:absolute;top:222px;left:{MARGIN}px;right:{MARGIN}px;height:8px;background:{c['accent']}}}
.flow{{position:absolute;top:290px;left:{MARGIN}px;right:110px;bottom:298px;display:flex;flex-direction:column;gap:48px}}
.flow.who{{top:584px;gap:12px}}
.h{{font-size:92px;font-weight:800;line-height:1.3;letter-spacing:-2px;text-wrap:balance}}
mark{{background:{c['accent']};color:{c['ink']};padding:0 12px;white-space:nowrap;box-decoration-break:clone;-webkit-box-decoration-break:clone}}
.body,.sub{{font-size:40px;line-height:1.55;text-wrap:pretty}}
.ask{{font-size:48px;font-weight:700}}
.pbg{{position:absolute;top:240px;left:0;right:0;height:320px;background:linear-gradient(180deg,{c['panel']} 60%,{c['ground']});display:flex;align-items:center;justify-content:center}}
.av{{width:240px;height:240px;border-radius:50%;background:{c['avatar']};display:flex;align-items:center;justify-content:center;font-size:88px;font-weight:700;overflow:hidden}}
.av img{{width:100%;height:100%;object-fit:cover}}
.bn{{font-size:56px;font-weight:700;line-height:1.2}}
.br{{font-size:40px;color:{c['muted']}}}
.reason{{font-size:40px;font-weight:600;line-height:1.4;margin-top:8px;border-left:6px solid {c['accent']};padding-left:20px}}
.bd{{font-size:40px;line-height:1.5;margin-top:8px}}
.sig{{position:absolute;top:1050px;left:{MARGIN}px;font-size:32px;font-weight:600}}
.prog{{position:absolute;top:1114px;left:{MARGIN}px;display:flex;gap:16px;align-items:center;height:24px}}
.pip{{width:20px;height:20px;border:4px solid {c['ink']}}}.pip.on{{width:64px;background:{c['ink']}}}
.arr{{font-size:34px;line-height:24px;margin-left:12px}}
.duo{{position:absolute;top:1012px;right:{MARGIN}px;height:164px}}
.hl{{position:absolute;top:1176px;left:{MARGIN}px;right:{MARGIN}px;height:2px;background:{c['ink']}}}
.site{{position:absolute;top:1190px;left:{MARGIN}px;font-family:'Courier New',monospace;font-size:28px;letter-spacing:4px}}
.bs{{position:absolute;top:1228px;left:{MARGIN}px;font-family:'Courier New',monospace;font-size:22px;color:{c['muted']}}}
.os{{position:absolute;top:1192px;right:{MARGIN}px;height:68px}}"""


def build(spec, base):
    b = spec["brand"]
    c = b["colors"]
    a = lambda k, h: data_uri(os.path.join(base, b[k]), h)
    tm, os_, duo = a("logo_top", 120), a("logo_bottom", 68), a("duo", 164)
    slides = spec["slides"]
    n = len(slides)
    out = []
    for i, s in enumerate(slides, 1):
        pips = "".join(f'<div class="pip{" on" if k == i else ""}"></div>' for k in range(1, n + 1))
        arrow = '<span class="arr">&#8594;</span>' if i < n else ""
        if s["type"] == "who":
            face = (f'<img src="{data_uri(os.path.join(base, s["photo"]), 240)}">' if s.get("photo")
                    else esc(s.get("initials", "")))
            mid = (f'<div class="pbg"><div class="av">{face}</div></div><div class="flow who">'
                   f'<div class="bn">{esc(s["name"])}</div><div class="br">{esc(s["role"])}</div>'
                   f'<div class="reason">{esc(s["reason"])}</div>'
                   f'<div class="bd">{"<br>".join(esc(x) for x in s["lines"])}</div></div>')
        else:
            parts = [f'<div class="h">{headline(s["title"], s.get("mark"))}</div>']
            if s.get("ask"):
                parts.append(f'<div class="ask">{esc(s["ask"])}</div>')
            if s.get("body"):
                parts.append(f'<div class="{"sub" if s.get("ask") else "body"}">{esc(s["body"])}</div>')
            mid = '<div class="flow">' + "".join(parts) + "</div>"
        out.append(f'''<div class="c"><img class="tm" src="{tm}"><div class="lane"><span class="tag">{esc(b["lane_label"])}</span><span class="num">0{i} / 0{n}</span></div>
<div class="gr"></div>{mid}<div class="sig">{esc(b["signature"])}</div><div class="prog">{pips}{arrow}</div>
<img class="duo" src="{duo}"><div class="hl"></div><div class="site">{esc(b["site"])}</div>
<div class="bs">{esc(b["tagline"])}</div><img class="os" src="{os_}"></div>''')
    return f"<html><head><meta charset='utf-8'><style>{css(c)}</style></head><body>{''.join(out)}</body></html>"


MEASURE_JS = """([content, chrome]) => [...document.querySelectorAll('.c')].map(card => {
  const o = card.getBoundingClientRect();
  const box = e => { const r = e.getBoundingClientRect();
    return {n: e.className, t: r.top - o.top, b: r.bottom - o.top, l: r.left - o.left, r: r.right - o.left,
            fs: parseFloat(getComputedStyle(e).fontSize), text: e.innerText || ''}; };
  const content_ = [...card.querySelectorAll(content)].map(box);
  const chrome_ = [...card.querySelectorAll(chrome)].map(box);
  const marks = [...card.querySelectorAll('mark')].map(m => m.getClientRects().length);
  const orphans = [];
  card.querySelectorAll('.h,.body,.sub,.reason,.ask').forEach(el => {
    const words = el.innerText.trim().split(/\\s+/); if (words.length < 3) return;
    const range = document.createRange(); const tops = [];
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT); let node;
    while ((node = walker.nextNode())) { const re = /\\S+/g; let m;
      while ((m = re.exec(node.data))) { range.setStart(node, m.index); range.setEnd(node, m.index + m[0].length);
        tops.push(Math.round(range.getBoundingClientRect().top)); } }
    const last = tops[tops.length - 1]; const onLast = tops.filter(t => Math.abs(t - last) < 4).length;
    if (onLast === 1 && new Set(tops).size > 1) orphans.push(el.className);
  });
  const pbg = card.querySelector('.pbg'); const extra = pbg ? [box(pbg)] : [];
  return {content: content_, chrome: chrome_, extra, marks, orphans};
})"""


def hit(a, b):
    return a["l"] < b["r"] and b["l"] < a["r"] and a["t"] < b["b"] and b["t"] < a["b"]


def zone(a, z):
    return a["l"] < z[2] and z[0] < a["r"] and a["t"] < z[3] and z[1] < a["b"]


def check(spec, measured):
    problems, report = [], []
    first_chrome = None
    for i, (s, m) in enumerate(zip(spec["slides"], measured), 1):
        p = lambda msg: problems.append(f"slide {i}: {msg}")
        els = m["content"] + m["chrome"] + m["extra"]
        # 1 every element pair, zero overlaps
        for x in range(len(els)):
            for y in range(x + 1, len(els)):
                if hit(els[x], els[y]):
                    p(f"overlap {els[x]['n']} x {els[y]['n']}")
        # 2 vertical math, top to bottom with a positive gap
        order = sorted(m["content"], key=lambda e: e["t"])
        for a, b in zip(order, order[1:]):
            if b["t"] - a["b"] <= 0:
                p(f"no gap between {a['n']} and {b['n']}")
        sig = next(e for e in m["chrome"] if e["n"] == "sig")
        if order and sig["t"] - order[-1]["b"] < 40:
            p(f"content ends {round(order[-1]['b'])}, only {round(sig['t'] - order[-1]['b'])}px above the signature")
        report.append(f"slide {i}: " + " | ".join(f"{e['n']} {round(e['t'])}-{round(e['b'])}" for e in sorted(els, key=lambda e: e['t'])))
        # 3 safe areas: margins, Instagram overlays, profile grid crop
        for e in m["content"] + m["chrome"]:
            if e["l"] < MARGIN - 1 or e["r"] > W - MARGIN + 1:
                p(f"{e['n']} outside the {MARGIN}px side margin")
            if zone(e, IG_COUNTER):
                p(f"{e['n']} under the Instagram slide counter (top right)")
            if zone(e, IG_TAG):
                p(f"{e['n']} under the Instagram tag icon (bottom left)")
            if i == 1 and (e["l"] < GRID_CROP or e["r"] > W - GRID_CROP):
                p(f"{e['n']} cut by the profile grid crop")
        # 4 cohesion: chrome sits in exactly the same place on every slide
        geo = {e["n"]: (round(e["t"]), round(e["l"])) for e in m["chrome"] if e["n"] != "prog"}
        if first_chrome is None:
            first_chrome = geo
        elif geo != first_chrome:
            p("footer or header chrome moved against slide 1")
        # 5 text floor and word limits
        for e in m["content"]:
            if e["fs"] < BODY_FLOOR and e["n"] not in ("h",):
                p(f"{e['n']} text {e['fs']}px, under the {BODY_FLOOR}px floor")
        if s.get("title") and len(s["title"].split()) > HEADLINE_WORDS:
            p(f"headline is {len(s['title'].split())} words, limit {HEADLINE_WORDS}")
        for k in ("body", "reason"):
            if s.get(k) and len(s[k].split()) > BODY_WORDS:
                p(f"{k} is {len(s[k].split())} words, limit {BODY_WORDS}")
        if not s.get("alt"):
            p("missing alt text")
        # 6 tidy: highlight on one line, no lonely last word
        if any(n > 1 for n in m["marks"]):
            p("highlight split across lines")
        for o in m["orphans"]:
            p(f"lonely last word in {o}")
    return problems, report


def stress(spec):
    s = json.loads(json.dumps(spec))
    for sl in s["slides"]:
        if sl.get("body"):
            sl["body"] = sl["body"] + " " + sl["body"]
            sl["body"] = " ".join(sl["body"].split()[:BODY_WORDS])
        if sl.get("name"):
            sl["name"] = sl["name"] + " Junior"
        if sl.get("lines"):
            sl["lines"] = [x + "llll" for x in sl["lines"]]
    return s


def render(spec, base, out, page, tag=""):
    page.set_content(build(spec, base))
    page.evaluate("document.fonts.ready")
    measured = page.evaluate(MEASURE_JS, [CONTENT, CHROME])
    shots = []
    for i, el in enumerate(page.query_selector_all(".c"), 1):
        path = os.path.join(out, f"{tag}slide-{i:02d}.jpg")
        el.screenshot(path=path, type="jpeg", quality=92)
        shots.append(path)
    return measured, shots


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--out", default="out")
    args = ap.parse_args()
    spec = json.load(open(args.spec))
    base = os.path.dirname(os.path.abspath(args.spec))
    os.makedirs(args.out, exist_ok=True)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        page = br.new_page(viewport={"width": W + 40, "height": H * len(spec["slides"]) + 80})
        measured, shots = render(spec, base, args.out, page)
        problems, report = check(spec, measured)
        smeasured, _ = render(stress(spec), base, args.out, page, tag="stress-")
        sproblems, _ = check(stress(spec), smeasured)
        problems += [f"worst content, {x}" for x in sproblems]
        br.close()
    for f in os.listdir(args.out):
        if f.startswith("stress-"):
            os.remove(os.path.join(args.out, f))
    ims = [Image.open(p) for p in shots]
    sheet = Image.new("RGB", (len(ims) * 360 + (len(ims) + 1) * 20, 490), "#dddddd")
    for k, im in enumerate(ims):
        sheet.paste(im.resize((360, 450)), (20 + k * 380, 20))
    sheet.save(os.path.join(args.out, "contact-sheet.png"))
    grid = ims[0].crop((GRID_CROP, 0, W - GRID_CROP, H)).resize((240, 320))
    grid.save(os.path.join(args.out, "cover-grid.png"))
    manifest = {"slides": [{"file": os.path.basename(p), "bytes": os.path.getsize(p), "alt": s.get("alt", "")}
                           for p, s in zip(shots, spec["slides"])],
                "problems": problems, "vertical_math": report}
    json.dump(manifest, open(os.path.join(args.out, "manifest.json"), "w"), indent=2)
    print("\n".join(report))
    if problems:
        print("\nFAIL")
        print("\n".join(" - " + x for x in problems))
        sys.exit(1)
    print("\nPASS: overlaps, vertical math, safe areas, cohesion, type floor, tidy, worst content")


if __name__ == "__main__":
    main()
