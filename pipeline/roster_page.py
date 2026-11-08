"""Player-naming decision map from a hand-built roster (one card per REAL person).

  python roster_page.py  -> <game>/player-naming-decision-map.html  (+ data/photo_P<id>.png per player)
Use this instead of players.py ask + naming_page.py when the tracker tiles come out mixed (crowded half court:
tracker ids jump between people). data/roster.json: [{"id", "suggest", "desc", "team", "games", "picks": [[t, idx], ...]}]
where idx is the person's position, left to right, among the tracked boxes at second t (WORK/roster/roster_frame.py
prints that numbered sheet). The summary block uses the same "Decision n / Choice: name" format as naming_page.py.
"""
import base64, io, json, os, re, sys
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bbconfig

TEMPLATE = os.path.expanduser(r"~\.claude-personal\skills\decision-map\template.html")
tpl = open(TEMPLATE, encoding="utf-8").read()
style = re.search(r"<style>.*?</style>", tpl, re.S).group(0)
logo = re.search(r"<svg aria-label=\"Investing.com\".*?</svg>", tpl, re.S).group(0)
roster = json.load(open(bbconfig.data("roster.json"), encoding="utf-8"))
rows = {}
for line in open(bbconfig.data("tracks.jsonl")):
    r = json.loads(line)
    rows[r["k"]] = r


def person(t, idx, pad=0.22):
    k = int(round(t * 5)) + 1
    ps = sorted([p for p in rows[k]["p"] if p[5] - p[3] >= 80 and p[1] >= 0.35], key=lambda p: p[2])
    x0, y0, x1, y1 = ps[idx][2:6]
    w, h = x1 - x0, y1 - y0
    im = Image.open(os.path.join(bbconfig.F5, f"{k:05d}.jpg")).convert("RGB")
    return im.crop((int(x0 - w * pad), int(y0 - h * 0.10), int(x1 + w * pad), int(y1 + h * 0.05)))


def b64(c, hgt=260):
    c = c.resize((max(1, int(c.width * hgt / c.height)), hgt), Image.LANCZOS)
    b = io.BytesIO(); c.save(b, "JPEG", quality=84)
    return base64.b64encode(b.getvalue()).decode()


cards = []
for p in roster:
    n = p["id"]
    crops = [(t, person(t, i)) for t, i in p["picks"]]
    ph = crops[0][1]
    ph.resize((450, int(450 * ph.height / ph.width)), Image.LANCZOS).save(bbconfig.data(f"photo_P{n}.png"))
    imgs = "".join(
        f'<figure><img src="data:image/jpeg;base64,{b64(c)}" alt="">'
        f'<figcaption>{(bbconfig.setup_of(t) or "?").replace("G", "Game ")} · {int(t // 60)}:{int(t % 60):02d}</figcaption></figure>'
        for t, c in crops)
    kit = "orange" if "orange" in p["team"] else "lime"
    ask = "Is this you?" if p["suggest"] else "Who is this?"
    cards.append(f"""
<article class="card nm" data-decision="{n}" id="d{n}">
  <div class="card-head"><div class="card-num">{n}</div><h3 data-title>Player {n}</h3></div>
  <p class="nm-desc">{p['desc']}</p>
  <div class="nm-tags"><span class="tag">Team {p['team']}</span><span class="tag">Games {p['games']}</span></div>
  <div class="nm-row">
    <div class="nm-imgs team-{kit}">{imgs}</div>
    <div class="nm-in">
      <div class="ask">{ask}</div>
      <input class="nm-name" id="name{n}" list="names" placeholder="Type a name" autocomplete="off" value="{p['suggest']}">
      <div class="nm-quick">
        <button type="button" class="btn-ghost nm-q" data-v="skip">Don't know</button>
      </div>
      <textarea id="n{n}" placeholder="Note (optional)" rows="1"></textarea>
    </div>
  </div>
</article>""")

extra_css = """
<style>
.nm-desc{margin:0 0 8px;color:var(--text-primary, #181C21)}
.nm-tags{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px}
.nm-row{display:flex;gap:24px;align-items:flex-start;flex-wrap:wrap}
.nm-imgs{display:flex;gap:8px;padding:8px;border-radius:6px;background:var(--surface-muted, #F4F5F6)}
.nm-imgs figure{margin:0}
.nm-imgs img{height:260px;border-radius:4px;display:block}
.nm-imgs figcaption{font-size:12px;color:var(--text-secondary, #5B616E);margin-top:4px;font-variant-numeric:tabular-nums}
.nm-imgs.team-orange{box-shadow:inset 0 0 0 3px #FF6B00}
.nm-imgs.team-lime{box-shadow:inset 0 0 0 3px #9BC53D}
.nm-in{flex:1;min-width:240px;display:flex;flex-direction:column;gap:10px}
.nm-name{font:inherit;font-size:18px;padding:10px 12px;border:1px solid var(--border-default, #D5D8DC);border-radius:6px}
.nm-name.filled{border-color:#007C32;box-shadow:0 0 0 1px #007C32}
.nm-quick{display:flex;gap:8px;flex-wrap:wrap}
.nm-q.on{background:#181C21;color:#fff}
.card.nm textarea{min-height:0}
</style>"""

script = """
<script>
const KEY = 'bb-roster-' + document.title;
const cardsEl = () => [...document.querySelectorAll('.card[data-decision]')];
function refreshNames(){
  const s = new Set(KNOWN);
  document.querySelectorAll('.nm-name').forEach(i => { const v = i.value.trim(); if (v && v !== 'skip') s.add(v); });
  document.getElementById('names').innerHTML = [...s].sort().map(n => `<option value="${n}">`).join('');
}
function save(){ try{ const o={}; document.querySelectorAll('.nm-name').forEach(i=>o[i.id]=i.value); localStorage.setItem(KEY, JSON.stringify(o)); }catch(e){} }
function load(){ try{ const o=JSON.parse(localStorage.getItem(KEY)||'{}'); Object.entries(o).forEach(([k,v])=>{const i=document.getElementById(k); if(i) i.value=v;}); }catch(e){} }
function paint(){
  document.querySelectorAll('.nm-name').forEach(i => {
    i.classList.toggle('filled', !!i.value.trim());
    i.closest('.card').querySelectorAll('.nm-q').forEach(b => b.classList.toggle('on', b.dataset.v === i.value.trim()));
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
  const lines = ["Player naming - Decision Summary", "=".repeat(40), ""];
  for (const c of cardsEl()){
    const id = c.dataset.decision, v = c.querySelector('.nm-name').value.trim(), note = document.getElementById('n'+id).value.trim();
    lines.push(`Decision ${id}: Player ${id}`);
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

known_path = os.path.join(bbconfig.PIPELINE, "players", "known.json")
known = sorted(json.load(open(known_path))) if os.path.exists(known_path) else []
known = sorted(set(known) | {bbconfig.CFG["user"]["name"]})
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
  <p class="sub">One card per player, with photos from the games he played. Type each name once. Card 1 is my guess for you:
  change it if I picked the wrong player. Names go on the stats cards and in the Top 10 captions.</p>
  <div class="pills"><span class="pill"><strong class="num">{len(roster)}</strong> players</span><span class="pill">Est. <strong class="num">2 min</strong></span>
  <span class="pill brand">4 on 4 · <strong class="num">4</strong> games</span></div>
</div></header>
<div class="wrap">
<datalist id="names"></datalist>
{''.join(cards)}
<section class="general"><h3>General Feedback</h3><p>Anything else, for example a player I missed or a wrong team.</p>
<textarea id="generalNote" placeholder="Free-form comments..."></textarea></section>
<button class="btn-primary" onclick="generateSummary()">Generate Summary</button>
<div class="output" id="outputBox"><h3>Paste This Back to Claude</h3><pre id="outputPre"></pre>
<button class="btn-ghost" id="copyBtn" onclick="copyOutput()">Copy to Clipboard</button></div>
</div>
<script>const KNOWN = {json.dumps(known)};</script>{script}
</body></html>"""
out = os.path.join(bbconfig.GAME_DIR, "player-naming-decision-map.html")
open(out, "w", encoding="utf-8").write(html)
print(out, round(len(html) / 1e6, 2), "MB")
