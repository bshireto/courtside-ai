"""Top 10 approval page (decision-map format): one card per proposed basket + alternates, each with its clip.

  python top10_page.py  -> <game>/top10-decision-map.html
Reads data/top10_proposal.json: [{"id", "rank" (1-10 or null for an alternate), "caption", "sub", "time", "name", "assist",
"points", "play"}] and expects output/top10_preview/<id>.mp4 + .jpg next to the page (cut them first).
Recommended choices are pre-selected, so approving the list as proposed is: watch, Generate Summary, paste back.
The summary keeps the standard "Decision n / Choice / Note" block.
"""
import html, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bbconfig

TEMPLATE = os.path.expanduser(r"~\.claude-personal\skills\decision-map\template.html")
tpl = open(TEMPLATE, encoding="utf-8").read()
style = re.search(r"<style>.*?</style>", tpl, re.S).group(0)
logo = re.search(r"<svg aria-label=\"Investing.com\".*?</svg>", tpl, re.S).group(0)
items = json.load(open(bbconfig.data("top10_proposal.json"), encoding="utf-8"))
date = bbconfig.CFG.get("date", "")
e = html.escape
top = [x for x in items if x.get("rank")]
alts = [x for x in items if not x.get("rank")]


def card(n, x):
    ranked = bool(x.get("rank"))
    who = x["name"] + (f", assist {x['assist']}" if x.get("assist") else "")
    title = f"#{x['rank']} · {x['caption']}" if ranked else f"Alternate · {x['caption']}"
    ask = f"Keep this basket at number {x['rank']}?" if ranked else "Add this basket to the Top 10?"
    if ranked:
        opts = f"""
        <label class="option recommended"><input type="radio" name="d{n}" value="A — Keep at #{x['rank']}" checked data-in="1">
          <div><div class="option-t">A — Keep It at #{x['rank']} <span class="badge">Recommended</span></div>
          <div class="option-d">Stays in the countdown with the caption "{e(x['caption'])}".</div>
          <span class="downside"><b>What's bad:</b> nothing changes; an alternate you like more stays out.</span></div></label>
        <label class="option"><input type="radio" name="d{n}" value="B — Drop it" data-in="0">
          <div><div class="option-t">B — Drop It</div>
          <div class="option-d">Leaves the countdown; the baskets below it move up one place.</div>
          <span class="downside"><b>What's bad:</b> you need to add one alternate, or the countdown has 9.</span></div></label>"""
    else:
        opts = f"""
        <label class="option recommended"><input type="radio" name="d{n}" value="A — Leave out" checked data-in="0">
          <div><div class="option-t">A — Leave It Out <span class="badge">Recommended</span></div>
          <div class="option-d">It still appears in the every-basket recap, just not in the countdown.</div>
          <span class="downside"><b>What's bad:</b> a basket you may rate higher than my picks is not featured.</span></div></label>
        <label class="option"><input type="radio" name="d{n}" value="B — Add to the Top 10" data-in="1">
          <div><div class="option-t">B — Add It to the Top 10</div>
          <div class="option-d">Goes into the countdown; write the rank you want in the note, or I slot it at the bottom.</div>
          <span class="downside"><b>What's bad:</b> one of the ten above has to go, or the countdown has 11.</span></div></label>"""
    return f"""
<article class="card" id="d{n}" data-decision="{n}">
  <div class="card-head"><div class="card-n">{n}</div><h2 class="card-title" data-title>{e(title)}</h2></div>
  <div class="ask">{ask}</div>
  <p class="narrative">{e(x['play'] or '')}</p>
  <div class="viz">
    <div class="viz-title"><span class="num">{x['time']}</span> · {e(who)} · {x['points']} points</div>
    <video class="clip" controls preload="none" playsinline poster="output/top10_preview/{x['id']}.jpg" src="output/top10_preview/{x['id']}.mp4"></video>
    <div class="viz-cap">Press play. The clip is the same cut the countdown uses, without the slow-motion replay.</div>
  </div>
  <div class="label">Pick One</div>
  <div class="options">{opts}
  </div>
  <div class="note"><label for="n{n}">Notes or changes for this basket</label>
  <textarea id="n{n}" placeholder="e.g. move to #2, or change the caption to ..."></textarea></div>
</article>"""


cards = "".join(card(i + 1, x) for i, x in enumerate(top + alts))
rows = "".join(f"""
  <div class="tldr-row"><div class="tldr-n">{x['rank']}</div><div class="tldr-q"><span class="num">{x['time']}</span> · {e(x['name'])}{' · assist ' + e(x['assist']) if x.get('assist') else ''}</div>
  <div class="tldr-rec"><b>{e(x['caption'])}</b></div><a href="#d{i + 1}">Open</a></div>""" for i, x in enumerate(top))

extra_css = """
<style>
.clip{width:100%;max-width:880px;display:block;border-radius:6px;background:#181C21;aspect-ratio:16/9}
.count-pill{font-variant-numeric:tabular-nums}
.count-pill.bad{color:#D91400;font-weight:700}
.sect{margin:40px 0 8px;font-size:22px;font-weight:700}
.sect-sub{color:var(--text-secondary, #5B616E);margin:0 0 16px}
</style>"""

script = """
<script>
function getDecisions(){
  return [...document.querySelectorAll('.card[data-decision]')].map(card=>({
    id: card.dataset.decision, title: (card.querySelector('[data-title]')?.textContent || '').trim(), noteId: 'n' + card.dataset.decision }));
}
function countIn(){ return [...document.querySelectorAll('input[type=radio]:checked')].filter(r => r.dataset.in === '1').length; }
function updateProgress(){
  const n = countIn();
  const lab = document.getElementById('progLabel');
  lab.textContent = `${n} in the Top 10`;
  lab.classList.toggle('bad', n !== 10);
  document.getElementById('progFill').style.width = Math.min(100, n * 10) + '%';
  document.getElementById('countNote').textContent = n === 10 ? '' : (n < 10 ? `Only ${n} baskets selected: add ${10 - n} more or leave it and I fill from the alternates.` : `${n} baskets selected: drop ${n - 10} or tell me which to cut.`);
}
document.addEventListener('change', e => { if (e.target.type === 'radio') updateProgress(); });
function generateSummary(){
  const lines = ["Top 10 - Decision Summary", "=".repeat(40), ""];
  for (const d of getDecisions()){
    const sel = document.querySelector(`input[name="d${d.id}"]:checked`);
    const note = document.getElementById(d.noteId).value.trim();
    lines.push(`Decision ${d.id}: ${d.title}`);
    lines.push(`  Choice: ${sel ? sel.value : "(not selected)"}`);
    if (note) lines.push(`  Note: ${note}`);
    lines.push("");
  }
  const g = document.getElementById('generalNote').value.trim();
  if (g){ lines.push("General feedback:"); lines.push("  " + g); lines.push(""); }
  lines.push("=== End ===");
  document.getElementById('outputPre').textContent = lines.join("\\n");
  const box = document.getElementById('outputBox'); box.style.display = 'block'; box.scrollIntoView({behavior:'smooth', block:'start'});
}
function copyOutput(){
  navigator.clipboard.writeText(document.getElementById('outputPre').textContent).then(()=>{
    const b = document.getElementById('copyBtn'); b.textContent = "Copied"; setTimeout(()=>{ b.textContent = "Copy to Clipboard"; }, 2000);
  });
}
updateProgress();
</script>"""

page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Top 10 · {date}</title>{style}{extra_css}</head><body>
<div class="topbar"><div class="topbar-in">{logo}
  <div class="topbar-title">Top 10 — decision map</div>
  <div class="progress"><div class="progress-track"><div class="progress-fill" id="progFill"></div></div>
  <div class="progress-label count-pill" id="progLabel">10 in the Top 10</div></div>
  <button class="btn-sm" onclick="generateSummary()">Generate Summary</button></div></div>
<header class="hero"><div class="hero-in">
  <div class="eyebrow">Basketball recap · {date}</div>
  <h1>Top 10 — decision map</h1>
  <p class="sub">My proposed countdown, ranked team play first, then individual skill. Every basket here was checked frame by frame at the rim.
  My picks are already selected: watch the clips, change only what you disagree with, then generate the summary and paste it back. I render the countdown after that.</p>
  <div class="pills"><span class="pill"><strong class="num">{len(top)}</strong> proposed</span><span class="pill"><strong class="num">{len(alts)}</strong> alternates</span>
  <span class="pill">Est. review <strong class="num">4 min</strong></span></div>
</div></header>
<div class="wrap">
<section class="tldr"><h2>At a Glance — The Proposed Countdown</h2>{rows}
</section>
<p class="sect-sub" id="countNote"></p>
<h2 class="sect">The Proposed Top 10</h2><p class="sect-sub">Number 1 is the best play. The video counts down from 10 to 1.</p>
{"".join(card(i + 1, x) for i, x in enumerate(top))}
<h2 class="sect">Alternates</h2><p class="sect-sub">Good baskets that just missed. Add any you rate higher.</p>
{"".join(card(len(top) + i + 1, x) for i, x in enumerate(alts))}
<section class="general"><h3>General Feedback</h3><p>Anything else, for example a basket that is not on this page at all.</p>
<textarea id="generalNote" placeholder="Free-form comments..."></textarea></section>
<button class="btn-primary" onclick="generateSummary()">Generate Summary</button>
<div class="output" id="outputBox"><h3>Paste This Back to Claude</h3><pre id="outputPre"></pre>
<button class="btn-ghost" id="copyBtn" onclick="copyOutput()">Copy to Clipboard</button></div>
</div>{script}
</body></html>"""
out = os.path.join(bbconfig.GAME_DIR, "top10-decision-map.html")
open(out, "w", encoding="utf-8").write(page)
print(out, round(len(page) / 1e3), "KB")
