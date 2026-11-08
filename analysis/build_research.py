"""Render results/research.md -> ../docs/research-offense-video-analysis.html (self-contained)."""
import os, re, json
import htmlkit as K

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(HERE, "..", "docs")
os.makedirs(DOCS, exist_ok=True)
md = open(os.path.join(HERE, "results", "research.md"), encoding="utf-8").read()
body_html = K.md_to_html(md)
# anchors for the top nav: numbered h2 sections
secs = re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', body_html)
nav = []
for i, (hid, title) in enumerate(secs):
    t = re.sub(r"<.*?>", "", title)
    t = re.sub(r"^\d+\.\s*", "", t)
    nav.append((hid, t[:26]))
verd = {}
try:
    for v in json.load(open(os.path.join(HERE, "results", "research_verdicts.json"), encoding="utf-8")):
        verd[v["verdict"]] = verd.get(v["verdict"], 0) + 1
except Exception:
    pass
vtxt = ", ".join(f"{k} {n}" for k, n in sorted(verd.items())) or "see report"
body = f'<section class="card md">{body_html}</section>'
html = K.page("Research: analysing an amateur offense reel", "Basketball analysis · research · 09.10.2026",
              "How to analyse one player's offense reel, and what to give him back",
              "Seven research angles, each load-bearing claim fact-checked by an independent agent, a gap-fill round, then one synthesis. "
              f"<strong>Fact-check tally: {K.esc(vtxt)}.</strong> Claims marked (unverified) could not be confirmed against their source.",
              [("7 angles", False), ("claims fact-checked", False), ("single wide camera", True)], body, nav)
out = os.path.join(DOCS, "research-offense-video-analysis.html")
open(out, "w", encoding="utf-8").write(html)
print("wrote", out, f"{os.path.getsize(out)/1e3:.0f} KB")
