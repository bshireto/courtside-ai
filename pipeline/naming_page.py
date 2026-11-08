"""Player-naming decision map (interactive HTML) built from players.py `ask` tiles.

  python naming_page.py  -> <game>/player-naming-decision-map.html
One card per tile: 3 screenshots of one tracked person + a name field (suggestions = names already typed
and players known from earlier games) + Mixed / Skip. "Generate Summary" gives the paste-back block that
players.py learn understands (via parse in the session). Styles/topbar come from the decision-map template.
"""
import base64, io, json, os, re, sys
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bbconfig

TEMPLATE = os.path.expanduser(r"~\.claude-personal\skills\decision-map\template.html")
tpl = open(TEMPLATE, encoding="utf-8").read()
style = re.search(r"<style>.*?</style>", tpl, re.S).group(0)
logo = re.search(r"<svg aria-label=\"Investing.com\".*?</svg>", tpl, re.S).group(0)

tiles = json.load(open(bbconfig.data("naming_tiles.json")))
dets = json.load(open(bbconfig.data("people_dets.json")))
known_path = os.path.join(bbconfig.PIPELINE, "players", "known.json")
known = sorted(json.load(open(known_path))) if os.path.exists(known_path) else []
known = sorted(set(known) | {bbconfig.CFG["user"]["name"]})
if not bbconfig.CFG.get("naming_suggest", True):  # different players than earlier games: no pre-filled names (Barak, 07.11.2026)
    known = []


def crop_b64(i):
    d = dets[i]
    im = Image.open(os.path.join(bbconfig.F5, f"{d['k']:05d}.jpg")).convert("RGB")
    x0, y0, x1, y1 = d["box"]
    w, h = x1 - x0, y1 - y0
    c = im.crop((int(x0 - w * .25), int(y0 - h * .12), int(x1 + w * .25), int(y1 + h * .06)))
    c = c.resize((int(c.width * 220 / c.height), 220), Image.LANCZOS)
    b = io.BytesIO(); c.save(b, "JPEG", quality=80)
    return base64.b64encode(b.getvalue()).decode()


cards = []
for t in tiles:
    best = sorted(t["members"], key=lambda i: -(dets[i]["box"][3] - dets[i]["box"][1]))
    if t.get("samples", 3) > 3:  # several samples of the same person, spread over time (and so over videos)
        byt = sorted(t["members"], key=lambda i: dets[i]["t"])
        m = t["samples"]
        picks = [byt[int(j * (len(byt) - 1) / (m - 1))] for j in range(m)]
    else:
        picks = [best[0], best[len(best) // 3], best[2 * len(best) // 3]]
    imgs = "".join(f'<img src="data:image/jpeg;base64,{crop_b64(i)}" alt="">' for i in picks)
    team = t["team"]
    n = t["n"]
    kit = "No pinnie" if team == "plain" else f"{team.title()} pinnie"
    where = ", ".join(sorted({tr.split(":")[0] for tr in t["tracks"]}))  # camera setup / game window names
    cards.append(f"""
<article class="card nm" data-decision="{n}" id="d{n}">
  <div class="card-head"><div class="card-num">{n}</div><h3 data-title>Tile {n} · {where} · {kit} · {t['secs'] // 60}m{t['secs'] % 60:02d}s on camera</h3></div>
  <div class="nm-row">
    <div class="nm-imgs team-{team}">{imgs}</div>
    <div class="nm-in">
      <div class="ask">Who is this?</div>
      <input class="nm-name" id="name{n}" list="names" placeholder="Type a name" autocomplete="off">
      <div class="nm-quick">
        <button type="button" class="btn-ghost nm-q" data-v="mixed">Mixed (two people)</button>
        <button type="button" class="btn-ghost nm-q" data-v="skip">Don't know</button>
      </div>
      <textarea id="n{n}" placeholder="Note (optional)" rows="1"></textarea>
    </div>
  </div>
</article>""")

extra_css = """
<style>
.nm-row{display:flex;gap:24px;align-items:flex-start;flex-wrap:wrap}
.nm-imgs{display:flex;gap:8px;padding:8px;border-radius:6px;background:var(--surface-muted, #F4F5F6)}
.nm-imgs img{height:220px;border-radius:4px;display:block}
.nm-imgs.team-orange{box-shadow:inset 0 0 0 3px #FF6B00}
.nm-imgs.team-lime{box-shadow:inset 0 0 0 3px #9BC53D}
.nm-imgs.team-plain{box-shadow:inset 0 0 0 3px #9AA1AB}
.nm-in{flex:1;min-width:240px;display:flex;flex-direction:column;gap:10px}
.nm-name{font:inherit;font-size:18px;padding:10px 12px;border:1px solid var(--border-default, #D5D8DC);border-radius:6px}
.nm-name.filled{border-color:#007C32;box-shadow:0 0 0 1px #007C32}
.nm-quick{display:flex;gap:8px;flex-wrap:wrap}
.nm-q.on{background:#181C21;color:#fff}
.card.nm textarea{min-height:0}
</style>"""

script = """
<script>
const KEY = 'bb-naming-' + document.title;
const cardsEl = () => [...document.querySelectorAll('.card[data-decision]')];
function refreshNames(){
  const s = new Set(KNOWN);
  document.querySelectorAll('.nm-name').forEach(i => { const v = i.value.trim(); if (v && v !== 'mixed' && v !== 'skip') s.add(v); });
  document.getElementById('names').innerHTML = [...s].sort().map(n => `<option value="${n}">`).join('');
}
function save(){ try{ const o={}; document.querySelectorAll('.nm-name').forEach(i=>o[i.id]=i.value); localStorage.setItem(KEY, JSON.stringify(o)); }catch(e){} }
function load(){ try{ const o=JSON.parse(localStorage.getItem(KEY)||'{}'); Object.entries(o).forEach(([k,v])=>{const i=document.getElementById(k); if(i) i.value=v;}); }catch(e){} }
function paint(){
  document.querySelectorAll('.nm-name').forEach(i => {
    i.classList.toggle('filled', !!i.value.trim());
    const card = i.closest('.card');
    card.querySelectorAll('.nm-q').forEach(b => b.classList.toggle('on', b.dataset.v === i.value.trim()));
  });
  const ds = cardsEl(), done = ds.filter(c => c.querySelector('.nm-name').value.trim()).length;
  document.getElementById('progLabel').textContent = `${done} / ${ds.length} named`;
  document.getElementById('progFill').style.width = (done / ds.length * 100) + '%';
}
document.addEventListener('input', e => { if (e.target.classList.contains('nm-name')) { refreshNames(); paint(); save(); } });
document.addEventListener('click', e => {
  const b = e.target.closest('.nm-q'); if (!b) return;
  const i = b.closest('.card').querySelector('.nm-name');
  i.value = (i.value.trim() === b.dataset.v) ? '' : b.dataset.v;
  refreshNames(); paint(); save();
});
function generateSummary(){
  const lines = ["Player naming — Decision Summary", "=".repeat(40), ""];
  for (const c of cardsEl()){
    const id = c.dataset.decision, v = c.querySelector('.nm-name').value.trim(), note = document.getElementById('n'+id).value.trim();
    lines.push(`Decision ${id}: Tile ${id}`);
    lines.push(`  Choice: ${v || 'skip'}`);
    if (note) lines.push(`  Note: ${note}`);
    lines.push("");
  }
  const g = document.getElementById('generalNote').value.trim();
  if (g){ lines.push("General feedback:"); lines.push("  " + g); lines.push(""); }
  lines.push("=== End ===");
  document.getElementById('outputPre').textContent = lines.join("\\n");
  const box = document.getElementById('outputBox'); box.style.display = 'block'; box.scrollIntoView({behavior:'smooth'});
}
function copyOutput(){
  navigator.clipboard.writeText(document.getElementById('outputPre').textContent).then(()=>{
    const b = document.getElementById('copyBtn'); b.textContent = "Copied"; setTimeout(()=>{ b.textContent = "Copy to Clipboard"; }, 2000);
  });
}
load(); refreshNames(); paint();
</script>"""

date = bbconfig.CFG.get("date", "")
html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Player Naming · {date}</title>{style}{extra_css}</head><body>
<div class="topbar"><div class="topbar-in">{logo}
  <div class="topbar-title">Player naming — decision map</div>
  <div class="progress"><div class="progress-track"><div class="progress-fill" id="progFill"></div></div>
  <div class="progress-label" id="progLabel">0 / 0 named</div></div>
  <button class="btn-sm" onclick="generateSummary()">Generate Summary</button></div></div>
<header class="hero"><div class="hero-in">
  <div class="eyebrow">Basketball recap · {date}</div>
  <h1>Who is who</h1>
  <p class="sub">Each tile is one player the camera followed without a break (orange frame = orange pinnie, green = lime).
  Type the name, reusing the same name for every tile of the same person. Use Mixed if a tile shows two different people.
  Names become each player's stats card, and the command will recognise them automatically next game.</p>
  <div class="pills"><span class="pill"><strong>{len(tiles)}</strong> tiles</span><span class="pill">Est. <strong>5 min</strong></span>
  <span class="pill brand">Known players <strong>{len(known)}</strong></span></div>
</div></header>
<div class="wrap">
<datalist id="names"></datalist>
{''.join(cards)}
<section class="general"><h3>General feedback</h3><p>Anything else, e.g. A player who never appears in the tiles.</p>
<textarea id="generalNote" placeholder="Free-form comments..."></textarea></section>
<button class="btn-primary" onclick="generateSummary()">Generate Summary</button>
<div class="output" id="outputBox"><h3>Paste this back to Claude</h3><pre id="outputPre"></pre>
<button class="btn-ghost" id="copyBtn" onclick="copyOutput()">Copy to Clipboard</button></div>
</div>
<script>const KNOWN = {json.dumps(known)};</script>{script}
</body></html>"""
out = os.path.join(bbconfig.GAME_DIR, "player-naming-decision-map.html")
open(out, "w", encoding="utf-8").write(html)
print(out, round(len(html) / 1e6, 1), "MB")
