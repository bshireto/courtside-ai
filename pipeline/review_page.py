"""Build a local review page so the player confirms his own shots / assists before stats are rendered.

  python review_page.py data/review_items.json review/
review_items.json: [{"id", "kind": "shot"|"assist", "t0", "t1", "rim_t", "hoop", "guess", "note"}]
Writes review/<id>_wide.mp4, review/<id>_rim.mp4 and review/index.html.
"""
import json, os, subprocess, sys, html
from concurrent.futures import ThreadPoolExecutor

VIDEO = r"~\Downloads\VID20260923193236.mp4"
RIMCROP = {"A": (1130, 330, 1450, 570), "Bnear": (1450, 100, 1800, 360), "Bfar": (890, 520, 1070, 655)}
items = json.load(open(sys.argv[1]))
out = sys.argv[2]
os.makedirs(out, exist_ok=True)


def clip(it):
    w = os.path.join(out, f"{it['id']}_wide.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{it['t0']:.2f}", "-t", f"{it['t1'] - it['t0']:.2f}", "-i", VIDEO,
                    "-vf", "scale=960:-2", "-c:v", "libx264", "-crf", "28", "-preset", "veryfast", "-an", "-movflags", "+faststart", w], check=True)
    if it.get("rim_t") is not None:
        x0, y0, x1, y1 = RIMCROP[it["hoop"]]
        r = os.path.join(out, f"{it['id']}_rim.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{it['rim_t'] - 1.0:.2f}", "-t", "2.2", "-i", VIDEO,
                        "-vf", f"crop={x1 - x0}:{y1 - y0}:{x0}:{y0},scale=640:-2:flags=lanczos,setpts=3*PTS",
                        "-r", "30", "-c:v", "libx264", "-crf", "24", "-preset", "veryfast", "-an", "-movflags", "+faststart", r], check=True)
    return it["id"]


with ThreadPoolExecutor(4) as ex:
    list(ex.map(clip, items))


def fmt(t):
    return f"{int(t // 60)}:{int(t % 60):02d}"


cards = []
for it in items:
    rim = f'<figure><video src="{it["id"]}_rim.mp4" controls muted loop playsinline preload="metadata"></video><figcaption>Rim close-up, 1/3 speed</figcaption></figure>' if it.get("rim_t") is not None else ""
    if it["kind"] == "shot":
        q = f"""<div class="q"><span>Result</span>{''.join(f'<label><input type="radio" name="{it["id"]}_r" value="{v}" {"checked" if v == it["guess"] else ""}>{v}</label>' for v in ("make", "miss", "not my shot"))}</div>
<div class="q"><span>Shot</span>{''.join(f'<label><input type="radio" name="{it["id"]}_p" value="{v}" {"checked" if v == it.get("pts") else ""}>{v}</label>' for v in ("2", "3"))}</div>"""
    else:
        q = f"""<div class="q"><span>Assist?</span>{''.join(f'<label><input type="radio" name="{it["id"]}_r" value="{v}" {"checked" if v == it["guess"] else ""}>{v}</label>' for v in ("assist", "no"))}</div>"""
    cards.append(f"""<section class="card" data-id="{it['id']}"><h2>{it['id'].upper()} &middot; {fmt(it['t0'] + 2)} <em>{html.escape(it['kind'])}</em></h2>
<p class="note">{html.escape(it['note'])}</p><div class="vids"><figure><video src="{it['id']}_wide.mp4" controls muted playsinline preload="metadata"></video><figcaption>Wide</figcaption></figure>{rim}</div>{q}</section>""")

page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Shot Review</title><style>
:root{{--bg:#101318;--card:#181c22;--ink:#e9edf2;--mut:#9aa4b0;--line:#2a313a;--acc:#ff7a1a}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,Segoe UI,sans-serif}}
main{{max-width:1100px;margin:0 auto;padding:24px 16px 120px}} h1{{margin:0 0 4px}} .sub{{color:var(--mut);margin:0 0 24px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px;margin:0 0 16px}}
h2{{margin:0 0 4px;font-size:17px}} h2 em{{color:var(--acc);font-style:normal;font-size:13px;margin-left:6px;text-transform:uppercase}}
.note{{color:var(--mut);margin:0 0 10px}} .vids{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:10px}}
figure{{margin:0}} video{{width:100%;border-radius:6px;background:#000}} figcaption{{color:var(--mut);font-size:12px}}
.q{{display:flex;gap:14px;align-items:center;margin-top:10px;flex-wrap:wrap}} .q span{{width:64px;color:var(--mut)}}
label{{display:flex;gap:6px;align-items:center;padding:6px 12px;border:1px solid var(--line);border-radius:9999px;cursor:pointer}}
footer{{position:fixed;left:0;right:0;bottom:0;background:#0b0d11ee;border-top:1px solid var(--line);padding:12px 16px;display:flex;gap:12px;justify-content:center}}
button{{background:var(--acc);color:#111;border:0;border-radius:6px;padding:10px 18px;font-weight:700;cursor:pointer}}
textarea{{width:100%;min-height:90px;background:#0b0d11;color:var(--ink);border:1px solid var(--line);border-radius:6px;margin-top:12px}}
</style></head><body><main><h1>Confirm your shots and assists</h1>
<p class="sub">Pre-filled with my best guess. Fix anything wrong, then press Copy Answers and paste the result back in chat.</p>
{''.join(cards)}
<textarea id="out" placeholder="Answers appear here"></textarea></main>
<footer><button id="copy">Copy Answers</button></footer>
<script>
const KEY='shot-review-2026-09-23';
function collect(){{const o={{}};document.querySelectorAll('.card').forEach(c=>{{const id=c.dataset.id;const r=c.querySelector(`input[name="${{id}}_r"]:checked`);const p=c.querySelector(`input[name="${{id}}_p"]:checked`);o[id]=[r?r.value:'?',p?p.value:''].filter(Boolean).join(' ');}});return o;}}
try{{const s=JSON.parse(localStorage.getItem(KEY)||'{{}}');Object.entries(s).forEach(([n,v])=>{{const el=document.querySelector(`input[name="${{n}}"][value="${{v}}"]`);if(el)el.checked=true;}});}}catch(e){{}}
document.addEventListener('change',e=>{{try{{const s=JSON.parse(localStorage.getItem(KEY)||'{{}}');s[e.target.name]=e.target.value;localStorage.setItem(KEY,JSON.stringify(s));}}catch(err){{}}}});
document.getElementById('copy').onclick=()=>{{const t=Object.entries(collect()).map(([k,v])=>k+': '+v).join('\\n');const ta=document.getElementById('out');ta.value=t;ta.select();try{{navigator.clipboard.writeText(t);}}catch(e){{document.execCommand('copy');}}}};
</script></body></html>"""
open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(page)
print("items", len(items))
