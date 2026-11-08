"""Phone-size practice card (Hebrew, OKC colours): one page with three tabs (alone / with a partner / inside a game)
plus a PNG of each tab to keep on the phone.

  python build_session_card.py
Inputs: practice.json (drills and 25-minute plans, plain Hebrew), scope.json (the three instructions).
Outputs: ../review_2026-10-07/Barak_Session_Card_2026-10-07.html and ../review_2026-10-07/session_cards/{solo,partner,game}.png
"""
import json, os, subprocess
import htmlkit as K

HERE = os.path.dirname(os.path.abspath(__file__))
esc = K.esc
practice = json.load(open(os.path.join(HERE, "practice.json"), encoding="utf-8"))
scope = json.load(open(os.path.join(HERE, "scope.json"), encoding="utf-8"))
MODE = {"solo": "לבד", "partner": "עם פרטנר", "game": "בתוך משחק"}

CSS = """
:root{--navy:#002D62;--thunder:#007AC1;--sunset:#EF3B24;--sun:#FDBB30;--ink:#10213A;--muted:#4A5568;--line:#E3E9F1;--well:#F4F6FA}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:"Heebo","Segoe UI",Arial,sans-serif;background:#DDE5EF;color:var(--ink);font-size:16px;line-height:1.5;-webkit-font-smoothing:antialiased}
.phone{max-width:430px;margin:0 auto;background:#fff;min-height:100vh}
.head{background:var(--navy);color:#fff;padding:18px 18px 16px}
.eyebrow{font-size:11.5px;font-weight:700;letter-spacing:.06em;color:var(--sun)}
.head h1{font-size:21px;font-weight:700;line-height:1.3;margin:4px 0 10px}
.one{background:rgba(255,255,255,.1);border-inline-start:4px solid var(--sunset);border-radius:6px;padding:10px 12px;font-size:15px;line-height:1.5}
.one b{display:block;font-size:11.5px;letter-spacing:.05em;color:var(--sun);margin-bottom:3px}
.tabs{display:flex;gap:6px;padding:12px 14px 0;background:#fff;position:sticky;top:0;z-index:5}
.tabs button{flex:1;border:1px solid var(--line);background:var(--well);border-radius:9999px;padding:9px 6px;font:inherit;font-size:15px;font-weight:700;color:var(--muted);cursor:pointer}
.tabs button.on{background:var(--thunder);border-color:var(--thunder);color:#fff}
.pane{display:none;padding:12px 14px 22px}
.pane.on{display:block}
.sub{font-size:14px;color:var(--muted);margin-bottom:10px}
h2{font-size:13px;font-weight:700;letter-spacing:.05em;color:var(--thunder);margin:16px 0 8px}
.step{display:grid;grid-template-columns:58px 1fr;gap:10px;padding:10px 0;border-top:1px solid var(--line);align-items:start}
.step:first-of-type{border-top:0}
.min{background:var(--navy);color:#fff;border-radius:6px;text-align:center;font-weight:700;font-size:14px;padding:5px 0;font-variant-numeric:tabular-nums;direction:ltr}
.step p{font-size:15.5px;line-height:1.5}
.drill{border:1px solid var(--line);border-radius:6px;padding:11px 12px;margin-bottom:9px}
.drill h3{font-size:16px;font-weight:700;margin-bottom:4px}
.drill .fix{display:inline-block;background:var(--well);border-radius:9999px;font-size:11.5px;font-weight:700;color:var(--muted);padding:1px 8px;margin-inline-start:6px}
.drill p{font-size:15px;line-height:1.5;color:var(--ink)}
.reps{margin-top:6px;font-size:14px;color:var(--muted)}
.cue{margin-top:7px;background:#FFF4D6;border:1px solid #FDDC8A;border-radius:6px;padding:6px 10px;font-weight:700;font-size:15px;color:#5A3E00}
.rule{display:grid;grid-template-columns:30px 1fr;gap:10px;padding:11px 0;border-top:1px solid var(--line)}
.rule:first-of-type{border-top:0}
.rule i{width:28px;height:28px;border-radius:9999px;background:var(--sunset);color:#fff;font-style:normal;font-weight:700;display:flex;align-items:center;justify-content:center;font-size:14px}
.rule p{font-size:16px;line-height:1.5}
.foot{font-size:12.5px;color:var(--muted);padding:0 14px 20px}
"""


def steps(items):
    return "".join(f'<div class="step"><div class="min">{esc(s["min"])}</div><p>{esc(s["what"])}</p></div>' for s in items)


def drill_cards(mode):
    out = []
    for d in practice[mode]["drills"]:
        tag = f'<span class="fix">{esc(practice["items"][d["for"]])}</span>' if d.get("for") else ""
        out.append(f'<div class="drill"><h3>{esc(d["name"])}{tag}</h3><p>{esc(d["how"])}</p>'
                   f'<div class="reps">{esc(d.get("count", ""))}</div><div class="cue">{esc(d.get("cue", ""))}</div></div>')
    return "".join(out)


def pane(mode):
    md = practice[mode]
    h = [f'<p class="sub">{esc(md["sub"])}</p>']
    if md.get("plan"):
        h.append(f'<h2>האימון, 25 דקות</h2>{steps(md["plan"])}')
    if md.get("rules"):
        h.append("<h2>הכללים שלך במשחק</h2>" + "".join(f'<div class="rule"><i>{i}</i><p>{esc(x)}</p></div>' for i, x in enumerate(md["rules"], 1)))
        h.append("<h2>משפט לעצמך, לכל אחד משלושת הדברים</h2>" + "".join(
            f'<div class="drill"><h3>{esc(practice["items"][k])}</h3><div class="cue">{esc(v)}</div></div>' for k, v in practice["cues"].items()))
    h.append(f'<h2>{"אחרי המשחק" if mode == "game" else "התרגילים בפירוט"}</h2>{drill_cards(mode)}')
    return "".join(h)


panes = {k: pane(k) for k in MODE}
three = "".join(f'<div style="margin-top:6px"><b style="display:inline;color:var(--sun);font-size:15px">{i}.</b> {esc(it["do"])}</div>' for i, it in enumerate(scope["top"]["items"], 1))
html = f"""<!DOCTYPE html>
<html lang="he" dir="rtl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ברק · כרטיס אימון אחרי משחק 07.10</title>
<style>@import url("https://fonts.googleapis.com/css2?family=Heebo:wght@400;500;700&display=swap");{CSS}</style></head>
<body><div class="phone">
<div class="head"><div class="eyebrow">כרטיס אימון · אחרי משחק 07.10.2026</div><h1>מה לתרגל עד המשחק הבא</h1>
<div class="one"><b>שלושה דברים למשחק הבא</b>{three}</div></div>
<div class="tabs">{"".join(f'<button data-tab="{k}" class="{"on" if k == "solo" else ""}">{v}</button>' for k, v in MODE.items())}</div>
{"".join(f'<div class="pane {"on" if k == "solo" else ""}" id="pane-{k}">{v}</div>' for k, v in panes.items())}
<p class="foot">נספרת רק חזרה שנעשתה נכון. הסרטונים של כל אחד מהדברים נמצאים בסקירה.</p>
</div>
<script>
function show(t){{document.querySelectorAll('.tabs button').forEach(b=>b.classList.toggle('on',b.dataset.tab===t));
document.querySelectorAll('.pane').forEach(p=>p.classList.toggle('on',p.id==='pane-'+t));}}
document.querySelectorAll('.tabs button').forEach(b=>b.addEventListener('click',()=>show(b.dataset.tab)));
const q=new URLSearchParams(location.search).get('tab'); if(q) show(q);
</script></body></html>"""
REVIEW_DIR = os.path.join(HERE, "..", "review_2026-10-07")      # the clean folder Barak opens
os.makedirs(REVIEW_DIR, exist_ok=True)
out = os.path.join(REVIEW_DIR, "Barak_Session_Card_2026-10-07.html")
open(out, "w", encoding="utf-8").write(html)
print("wrote", out)

# PNG per tab (phone width, 3x)
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
os.makedirs(os.path.join(REVIEW_DIR, "session_cards"), exist_ok=True)
if os.path.exists(CHROME):
    from PIL import Image
    import numpy as np
    for tab in MODE:
        png = os.path.join(REVIEW_DIR, "session_cards", f"{tab}.png")
        url = "file:///" + out.replace("\\", "/").replace(" ", "%20") + f"?tab={tab}"
        # headless Chrome will not go narrower than ~500 css px, so render at 600 and cut the 430-px card out of the middle
        subprocess.run([CHROME, "--headless=new", "--window-size=600,4200", "--force-device-scale-factor=2", "--hide-scrollbars",
                        f"--screenshot={png}", "--virtual-time-budget=5000", url], capture_output=True)
        if os.path.exists(png):
            im = Image.open(png).convert("RGB")
            x0 = (im.width - 860) // 2
            im = im.crop((x0, 0, x0 + 860, im.height)); a = np.asarray(im)
            rows = np.where((a.astype(int).sum(axis=2) < 255 * 3 - 40).any(axis=1))[0]      # last row that is not blank white
            im.crop((0, 0, im.width, min(im.height, rows.max() + 36))).save(png)
            print("wrote", png, Image.open(png).size)
