"""Assemble the self-contained HTML offense review from the workflow results.

Inputs (all in this folder):
  results/report.json    aggregated scouting report (REPORT_SCHEMA)
  results/records.json   27 per-possession records (CLIP_SCHEMA)
  results/verdicts.json  skeptic verdicts on the report's claims
  results/lenses.json    the three lens syntheses (for the appendix)
  drills.json            curated drill plan: {"fixes":[{"rank":1,"drills":[{"name","how","reps","cue","source","url"}]}],
                          "session":[{"min":5,"what":"..."}], "notes":"..."}
  clip_map.json, shot_chart.json, shot_chart.jpg, work/frames/*.jpg
Output: Barak_Offense_Review_2026-10-07.html
"""
import json, os, re
from PIL import Image
import htmlkit as K

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.join(HERE, "..", "recap_2026-10-07")
R = lambda *p: os.path.join(HERE, "results", *p)
report = json.load(open(R("report.json"), encoding="utf-8"))
records = {r["clip"]: r for r in json.load(open(R("records.json"), encoding="utf-8"))}
verdicts = json.load(open(R("verdicts.json"), encoding="utf-8"))
drills = json.load(open(os.path.join(HERE, "drills.json"), encoding="utf-8"))
clips = json.load(open(os.path.join(HERE, "clip_map.json"), encoding="utf-8"))
chart = json.load(open(os.path.join(HERE, "shot_chart.json"), encoding="utf-8"))
tl = json.load(open(os.path.join(GAME, "data", "user_timeline_v2.json"), encoding="utf-8"))["frames"]
tl.sort(key=lambda f: f["t"])
esc = K.esc


def fmt(t):
    m = int(t // 60)
    return f"{m}:{t - 60 * m:04.1f}"


def clip_of_reel(rt):
    for c in clips:
        if c["reel_start"] - 0.05 <= rt <= c["reel_end"] + 0.05:
            return c
    return None


def box_at(src_t, max_dt=0.9):
    best, bd = None, 1e9
    for f in tl:
        d = abs(f["t"] - src_t)
        if d < bd:
            bd, best = d, f
        if f["t"] > src_t + max_dt:
            break
    return best["box"] if best and bd <= max_dt else None


def frame_img(rt, W=880, H=495, max_w=880):
    """Crop a 16:9 window around Barak at reel time rt (falls back to the court crop)."""
    k = int(round(rt * 10)) + 1
    p = os.path.join(HERE, "work", "frames", f"{k:05d}.jpg")
    if not os.path.exists(p):
        return None
    c = clip_of_reel(rt)
    b = box_at(c["src_start"] + (rt - c["reel_start"])) if c else None
    if b:
        cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2 - 30
        x0 = int(max(0, min(1920 - W, cx - W / 2))); y0 = int(max(0, min(1080 - H, cy - H / 2)))
        return K.img_b64(p, max_w=max_w, crop=(x0, y0, x0 + W, y0 + H))
    return K.img_b64(p, max_w=max_w, crop=(380, 150, 1920, 1016))


def verdict_for(text_prefix, key):
    """Find the skeptic verdict whose claim starts with the given prefix and contains key."""
    for v in verdicts:
        if v["claim"].startswith(text_prefix) and key[:40] in v["claim"]:
            return v
    return None


def vbadge(v):
    if not v:
        return ""
    return f'<span class="verdict {v["verdict"]}" title="{esc(v.get("evidence", ""))}">{esc(v["verdict"].replace("_", " "))}</span>'


def frames_block(items, cls_by_kind=True):
    out = ['<div class="frames">']
    for it in items:
        src = frame_img(it["reel_time"])
        if not src:
            continue
        cls = ("pos" if it.get("kind") == "positive" else "neg") if cls_by_kind else ""
        tag = "What to keep" if it.get("kind") == "positive" else "What to change"
        out.append(f'<div class="frame-card {cls}"><img src="{src}" alt=""><div class="frame-cap"><b>{tag} · clip {it.get("clip", "")} · {fmt(it["reel_time"])}</b>{esc(it["caption"])}</div></div>')
    out.append("</div>")
    return "".join(out)


# ----- stats
stats = {"pts": 12, "fgm": 5, "fga": 13, "tpm": 2, "tpa": 5, "twom": 3, "twoa": 8, "ast": 2, "min": 28}
prev = {"pts": 6, "fgm": 2, "fga": 12, "tpm": 2, "tpa": 5, "twom": 0, "twoa": 7, "ast": 3, "min": 25}
efg = (stats["fgm"] + 0.5 * stats["tpm"]) / stats["fga"]
efg_prev = (prev["fgm"] + 0.5 * prev["tpm"]) / prev["fga"]
pps = (2 * stats["twom"] + 3 * stats["tpm"]) / stats["fga"]
pps_prev = (2 * prev["twom"] + 3 * prev["tpm"]) / prev["fga"]

tally = {}
for v in verdicts:
    tally[v["verdict"]] = tally.get(v["verdict"], 0) + 1

body = []

# ----- TL;DR
fixes = sorted(report["priority_fixes"], key=lambda f: f["rank"])
tm = report["teaching_moments"]
sc = report["stat_context"]
cut = sc.find("Calls I made")
sc_main, sc_more = (sc[:cut].strip(), sc[cut:].strip()) if cut > 0 else (sc, "")
used_moments = set()


def pick_moments(evidence_clips, kind, n):
    """Teaching moments for a fix/strength: walk its evidence clips in order, prefer the asked kind, never reuse a moment."""
    out = []
    for want in ((kind,), ("positive", "corrective")):
        for c in evidence_clips:
            for m in tm:
                key = (m["clip"], m["reel_time"])
                if m["clip"] == c and m["kind"] in want and key not in used_moments and len(out) < n:
                    out.append(m); used_moments.add(key)
        if len(out) >= n:
            break
    return out


def long_text(text, limit=520, label="Read the rest"):
    if len(text) <= limit:
        return esc(text)
    head = text[:limit].rsplit(" ", 1)[0]
    return f'{esc(head)}&hellip; <details class="more" style="margin-top:8px"><summary>{label}</summary><div class="more-body">{esc(text)}</div></details>'


body.append(f"""<section class="tldr" id="top">
<h2>The short version</h2>
<p>{esc(report["headline"])}</p>
<p class="muted">{esc(sc_main)}</p>
{f'<details class="more"><summary>Where the head coach overruled the reviewers</summary><div class="more-body">{esc(sc_more)}</div></details>' if sc_more else ''}
<div class="label" style="color:#BDBFC2;margin-top:14px">The one thing to carry into the next game</div>
<p>{esc(report["one_thing"])}</p>
<div class="label" style="color:#BDBFC2;margin-top:14px">Three fixes, in order of impact</div>
{"".join(f'<div class="tldr-row"><div class="tldr-n">{f["rank"]}</div><div class="tldr-q">{esc(f["what"])}<small>Cue: {esc(f["cue"])}</small></div></div>' for f in fixes)}
</section>""")

# ----- stats card
def stat(label, val, sub="", cls=""):
    return f'<div class="stat {cls}"><div class="stat-label">{label}</div><div class="stat-value num">{val}</div><div class="stat-sub">{sub}</div></div>'

body.append(f"""<section class="card" id="stats">
<h2>The line</h2>
<p class="lead">Three of the four games, every make checked at the rim by the pipeline. The previous game (23.09) is shown for context, not as a trend: two games is a small sample.</p>
<div class="stats">
{stat("Points", stats["pts"], f"prev {prev['pts']}")}
{stat("Field goals", f"{stats['fgm']}/{stats['fga']}", f"{stats['fgm']/stats['fga']*100:.0f}% · prev {prev['fgm']}/{prev['fga']}")}
{stat("Threes", f"{stats['tpm']}/{stats['tpa']}", f"{stats['tpm']/stats['tpa']*100:.0f}% · prev {prev['tpm']}/{prev['tpa']}", "pos")}
{stat("Twos", f"{stats['twom']}/{stats['twoa']}", f"{stats['twom']/stats['twoa']*100:.0f}% · prev {prev['twom']}/{prev['twoa']}", "neg")}
{stat("Assists", stats["ast"], f"prev {prev['ast']}")}
{stat("eFG%", f"{efg*100:.0f}%", f"prev {efg_prev*100:.0f}% · (FGM + 0.5·3PM) / FGA", "accent")}
{stat("Points per shot", f"{pps:.2f}", f"prev {pps_prev:.2f}", "accent")}
</div>
<div class="viz"><div class="viz-title">Two games, 25 shots: the threes are carrying the scoring</div>
<div class="bars">
<div class="bar-row"><div class="bar-name">Threes, both games</div><div class="bar-track"><div class="bar pos" style="width:40%"></div></div><div class="bar-val num">4 / 10 · 40%</div></div>
<div class="bar-row"><div class="bar-name">Twos, both games</div><div class="bar-track"><div class="bar neg" style="width:20%"></div></div><div class="bar-val num">3 / 15 · 20%</div></div>
<div class="bar-row"><div class="bar-name">Points per three attempted</div><div class="bar-track"><div class="bar pos" style="width:60%"></div></div><div class="bar-val num">1.20</div></div>
<div class="bar-row"><div class="bar-name">Points per two attempted</div><div class="bar-track"><div class="bar neg" style="width:20%"></div></div><div class="bar-val num">0.40</div></div>
</div>
<div class="viz-cap">Each three attempt has produced three times the points of each two attempt. With 25 shots the percentages are noisy, but the shot-by-shot table below shows why the twos are hard ones.</div></div>
</section>""")

# ----- priority fixes
fx = ['<section class="card" id="fixes"><h2>Three fixes, ranked by impact</h2><p class="lead">Each fix has one cue to think about on the court, a picture of what good looks like, and the frames it comes from. The drills section maps each fix to practice.</p>']
for f in fixes:
    v = verdict_for("PRIORITY FIX", f["what"])
    ev = pick_moments(f["evidence_clips"], "corrective", 2)
    fx.append(f"""<div class="fix"><div class="fix-n">{f["rank"]}</div><div>
<h3>{esc(f["what"])} {vbadge(v)}</h3>
<p class="why">{esc(f["why_it_matters_most"])}</p>
<div class="cue">Cue: {esc(f["cue"])}</div>
<p><strong>What good looks like.</strong> {esc(f["what_good_looks_like"])}</p>
<p class="why">Seen in possessions {", ".join(str(c) for c in f["evidence_clips"])}.</p>
{frames_block(ev) if ev else ""}
</div></div>""")
fx.append("</section>")
body.append("".join(fx))

# ----- strengths
st = ['<section class="card" id="strengths"><h2>What is already working</h2><p class="lead">Keep these. They are the base the fixes build on.</p>']
# one positive frame per strength: strengths with the fewest candidate moments pick first, and each picks the moment
# the fewest other strengths want, so a clip is not spent on a strength that had alternatives.
pos_moments = [m for m in tm if m["kind"] == "positive"]
cands = {}
for i, s in enumerate(report["strengths"]):
    cands[i] = [m for c in s["evidence_clips"] for m in pos_moments if m["clip"] == c and (m["clip"], m["reel_time"]) not in used_moments]
demand = {}
for ms in cands.values():
    for m in ms:
        demand[(m["clip"], m["reel_time"])] = demand.get((m["clip"], m["reel_time"]), 0) + 1
strength_frame = {}
for i in sorted(cands, key=lambda i: len(cands[i])):
    free = [m for m in cands[i] if (m["clip"], m["reel_time"]) not in used_moments]
    if free:
        m = min(free, key=lambda m: demand[(m["clip"], m["reel_time"])])
        strength_frame[i] = m; used_moments.add((m["clip"], m["reel_time"]))
for i, s in enumerate(report["strengths"]):
    v = verdict_for("STRENGTH", s["title"])
    ev = [strength_frame[i]] if i in strength_frame else []
    st.append(f'<h3>{esc(s["title"])} {vbadge(v)}</h3><p>{esc(s["detail"])} <span class="tag">possessions {", ".join(str(c) for c in s["evidence_clips"])}</span></p>{frames_block(ev) if ev else ""}')
st.append("</section>")
body.append("".join(st))

# ----- shots
sbs = sorted(report["shot_by_shot"], key=lambda s: s["reel_time"])
order = {c["id"]: c["n"] for c in chart}
rows = []
keep = sum(1 for s in sbs if s["verdict"] == "keep")
cut = sum(1 for s in sbs if s["verdict"] == "cut")
made_keep = sum(1 for s in sbs if s["verdict"] == "keep" and s["result"].lower().startswith("ma"))
for s in sbs:
    vc = {"keep": "good", "keep_but_improve": "mid", "cut": "bad"}[s["verdict"]]
    res = s["result"]
    rc = "good" if res.lower().startswith("ma") else "bad"
    rows.append(f'<tr><td class="c num">{order.get(s["shot_id"], "")}</td><td class="num">{fmt(s["reel_time"])}</td><td>{esc(s["zone"])}</td><td>{esc(s["type"])}</td><td>{esc(s["contest"])}</td><td class="c num">{s.get("dribbles", "")}</td><td class="c {rc}">{esc(res)}</td><td class="c num">{s["quality_1to5"]}</td><td class="c {vc}">{esc(s["verdict"].replace("_", " "))}</td><td>{esc(s["note"])}</td></tr>')
shot_img = K.img_b64(os.path.join(HERE, "shot_chart.jpg"), max_w=1400, quality=82)
body.append(f"""<section class="card" id="shots">
<h2>All 13 shots</h2>
<p class="lead">Dots are the feet at the release, on the real court with the players removed. Numbers follow the order in the game. The table grades each shot as a coach would: was it a shot worth taking, before knowing whether it went in.</p>
<div class="viz"><img src="{shot_img}" alt="shot chart"><div class="viz-cap">Green filled = make, red ring = miss. The white line is the 3-point arc as painted on this court. Shots from the same spot are nudged right so the numbers stay readable.</div></div>
<div class="stats">
{stat("Shots worth taking", keep, f"{made_keep} of them went in")}
{stat("Keep, but improve", len(sbs) - keep - cut, "right idea, wrong execution")}
{stat("Shots to cut", cut, "the efficiency is hiding here", "neg")}
</div>
<table class="t"><tr><th>#</th><th>Reel</th><th>Zone</th><th>Type</th><th>Contest</th><th>Dribbles</th><th>Result</th><th>Quality 1-5</th><th>Verdict</th><th>Note</th></tr>{"".join(rows)}</table>
</section>""")

# ----- tendencies + weaknesses
tnd = ['<section class="card" id="tendencies"><h2>Tendencies and what they cost</h2><p class="lead">Counted from the 27 possessions. A skeptic agent re-watched the frames behind every claim; its verdict is shown next to each one.</p><div class="viz"><div class="viz-title">Counted tendencies</div><div class="bars">']
full_tend = []
for t in report["tendencies"]:
    v = verdict_for("TENDENCY", t["tendency"])
    m = re.search(r"(\d+)\s*(?:of|/)\s*(\d+)", t.get("numbers", "") or "")
    pct = int(int(m.group(1)) / max(1, int(m.group(2))) * 100) if m else 0
    short = re.split(r"[.:;]", t["tendency"])[0].strip()
    if len(short) > 64:
        short = short[:64].rsplit(" ", 1)[0] + "…"
    nums = t.get("numbers", "") or ""
    first = re.split(r";", nums)[0].strip()
    tnd.append(f'<div class="bar-row"><div class="bar-name" title="{esc(t["tendency"])}">{esc(short)}</div><div class="bar-track"><div class="bar c2" style="width:{pct}%"></div></div><div class="bar-val num">{esc(first)} {vbadge(v)}</div></div>')
    full_tend.append(f'<li><strong>{esc(t["tendency"])}</strong> <span class="tag">{esc(nums)}</span> <span class="tag">possessions {", ".join(str(c) for c in t["evidence_clips"])}</span> {vbadge(v)}</li>')
tnd.append('</div><div class="viz-cap">Bar length is the first count in each tendency; the full counts are in the list below. Hover a verdict to read what the skeptic saw.</div></div>')
tnd.append(f'<details class="more"><summary>The ten tendencies in full, with every count</summary><div class="more-body"><ul>{"".join(full_tend)}</ul></div></details>')
tnd.append("<h3>Weaknesses, with how often they showed up</h3>")
for w in report["weaknesses"]:
    v = verdict_for("WEAKNESS", w["title"])
    tnd.append(f'<h4>{esc(w["title"])} {vbadge(v)}</h4><p>{esc(w["detail"])} <span class="tag warn">{esc(w["how_often"])}</span> <span class="tag">possessions {", ".join(str(c) for c in w["evidence_clips"])}</span></p>')
    if v and v["verdict"] in ("partly", "refuted") and v.get("corrected_claim"):
        tnd.append(f'<div class="callout"><strong>Skeptic correction.</strong> {long_text(v["corrected_claim"], 420, "Read the full correction")}</div>')
tnd.append("</section>")
body.append("".join(tnd))

# ----- teaching moments
body.append(f"""<section class="card" id="moments">
<h2>Teaching moments</h2>
<p class="lead">The frames a coach would pause on, with the caption they would say. These are also the shot list for a captioned coaching video.</p>
{frames_block(sorted(tm, key=lambda m: m["reel_time"]))}
</section>""")

# ----- drills
dr = ['<section class="card" id="drills"><h2>Drills mapped to the three fixes</h2><p class="lead">From the research report (coaching sources linked). Reps are starting points; the make-count is the thing to track, not minutes.</p>']
for f in drills["fixes"]:
    fix = next((x for x in fixes if x["rank"] == f["rank"]), None)
    dr.append(f'<h3>Fix {f["rank"]}: {esc(fix["what"] if fix else "")}</h3><table class="t"><tr><th>Drill</th><th>How</th><th>Reps / target</th><th>Cue</th><th>Source</th></tr>')
    for d in f["drills"]:
        src = f'<a href="{esc(d.get("url", ""))}" target="_blank">{esc(d.get("source", ""))}</a>' if d.get("url") else esc(d.get("source", ""))
        dr.append(f'<tr><td><strong>{esc(d["name"])}</strong></td><td>{esc(d["how"])}</td><td>{esc(d.get("reps", ""))}</td><td>{esc(d.get("cue", ""))}</td><td>{src}</td></tr>')
    dr.append("</table>")
dr.append('<h3>A 25-minute solo session</h3><table class="t"><tr><th>Minutes</th><th>What</th></tr>')
for s in drills["session"]:
    dr.append(f'<tr><td class="num">{esc(s["min"])}</td><td>{esc(s["what"])}</td></tr>')
dr.append("</table>")
if drills.get("notes"):
    dr.append(f'<p class="callout">{esc(drills["notes"])}</p>')
dr.append("</section>")
body.append("".join(dr))

# ----- targets
body.append(f"""<section class="card" id="targets">
<h2>Next game targets</h2>
<table class="t"><tr><th>Metric</th><th>This game</th><th>Target</th></tr>
{"".join(f'<tr><td>{esc(t["metric"])}</td><td class="num">{esc(t["this_game"])}</td><td class="num"><strong>{esc(t["target"])}</strong></td></tr>' for t in report["next_game_targets"])}
</table></section>""")

# ----- possession log
rows = []
for c in clips:
    r = records.get(c["i"])
    if not r:
        continue
    sh = r["shot"]
    what = r["narrative"]
    dq = {"good": "good", "acceptable": "mid", "questionable": "bad", "poor": "bad", "n/a": ""}[r["decision_quality"]]
    xq = {"good": "good", "acceptable": "mid", "poor": "bad", "n/a": ""}[r["execution_quality"]]
    rows.append(f'<tr><td class="c num">{c["i"]}</td><td class="num">{fmt(c["reel_start"])}</td><td>{esc(r["play_start"].replace("_", " "))}</td><td>{esc(what)}</td><td class="c {dq}">{esc(r["decision_quality"])}</td><td class="c {xq}">{esc(r["execution_quality"])}</td><td>{esc(r["improvement_cue"])}</td></tr>')
body.append(f"""<section class="card" id="possessions">
<h2>Possession by possession</h2>
<p class="lead">All 27 possessions in the reel, in order. Reel time is where to scrub to in the offense reel.</p>
<details class="more" open><summary>Open the log (27 rows)</summary><div class="more-body">
<table class="t"><tr><th>#</th><th>Reel</th><th>Starts with</th><th>What happened</th><th>Decision</th><th>Execution</th><th>Cue</th></tr>{"".join(rows)}</table>
</div></details></section>""")

# ----- method
tally_txt = ", ".join(f"{k.replace('_', ' ')} {v}" for k, v in sorted(tally.items()))
body.append(f"""<section class="card" id="method">
<h2>How this was produced, and what it cannot see</h2>
<div class="two"><div>
<h3>Method</h3>
<ul>
<li>The offense reel (5:16, 27 possessions) was decoded at 10 frames per second. For each possession, wide court sheets at 2 fps, zoomed sheets following the tracked player at 5 fps, and 10 fps strips around every release were built.</li>
<li>One reviewer agent per possession read every sheet and filled a fixed record: what happened, decision, execution, mechanics, better option, cue. The pipeline's ball-tracking notes were given as a prior and checked against the frames.</li>
<li>Three synthesis passes (shot selection, mechanics, off-ball) looked for patterns; a head-coach pass wrote this report.</li>
<li>A skeptic agent then re-watched the cited frames behind every strength, weakness, tendency and fix. Tally: {esc(tally_txt)}.</li>
</ul></div><div>
<h3>Limits of one wide camera</h3>
<ul>
<li>Players are 100-160 px tall. Hand and finger mechanics (guide-hand thumb, wrist snap) are not readable; one-hand vs two-hand finish, jump, balance, drift, arc and footwork are.</li>
<li>The dark object top-left hides the check-ball spot in several possessions; hold times there are estimates.</li>
<li>13 shots is a small sample. The shot-quality grades matter more than the percentages.</li>
</ul></div></div>
<p class="foot">Folder: analysis_2026-10-07 (sheets/, briefs/, results/, clips/). Source reel: recap_2026-10-07/output/Barak_Offense_Reel_master.mp4.</p>
</section>""")

nav = [("top", "Summary"), ("stats", "Line"), ("fixes", "Fixes"), ("strengths", "Strengths"), ("shots", "Shots"), ("tendencies", "Tendencies"), ("moments", "Moments"), ("drills", "Drills"), ("targets", "Targets"), ("possessions", "Log"), ("method", "Method")]
html = K.page("Barak - offense review 07.10.2026", "Pickup run · 07.10.2026 · offense reel review", "Offense review: what to keep, what to change",
              f"<strong>12 points on 13 shots, 2 assists, 28 minutes.</strong> Every one of the 27 possessions in the reel reviewed frame by frame; every claim re-checked against the frames by a second pass.",
              [("27 possessions", False), ("13 shots", False), ("3 games", False), (f"{len(verdicts)} claims verified", True)], "\n".join(body), nav)
out = os.path.join(HERE, "Barak_Offense_Review_2026-10-07_en.html")
open(out, "w", encoding="utf-8").write(html)
print("wrote", out, f"{os.path.getsize(out)/1e6:.1f} MB")
