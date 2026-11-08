"""Build ../docs/offense-review-outputs-decision-map.html from the decision-map skill template.

Inputs (optional, used when present): results/report.json (fixes, cues, one_thing, targets), drills.json (session card),
results/run_stats.json ({"full_verify":{"agents":..,"minutes":..}, ...}), work/qa/review_shot.jpg (screenshot of the review),
../docs/assets/treat_*.jpg (the seven treatment stills), work/pose/angles_c077.json (joint confidences).
"""
import base64, io, json, os, re
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(HERE, "..", "docs")
ASSETS = os.path.join(DOCS, "assets")
TEMPLATE = os.path.expanduser("~/.claude-personal/skills/decision-map/template.html")
if not os.path.exists(TEMPLATE):
    TEMPLATE = os.path.expanduser("~/.claude/skills/decision-map/template.html")
OUT = os.path.join(DOCS, "offense-review-outputs-decision-map.html")


def esc(s):
    import html
    return html.escape("" if s is None else str(s), quote=False)


def img(path, max_w=880, quality=80, crop=None):
    im = Image.open(path).convert("RGB")
    if crop:
        im = im.crop(crop)
    if im.width > max_w:
        im = im.resize((max_w, int(im.height * max_w / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def load_json(p, default=None):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return default


report = load_json(os.path.join(HERE, "results", "report.json"), {})
drills = load_json(os.path.join(HERE, "drills.json"), {})
stats = load_json(os.path.join(HERE, "results", "run_stats.json"), {})
pose = load_json(os.path.join(HERE, "work", "pose", "angles_c077.json"), {})
fixes = sorted(report.get("priority_fixes", []), key=lambda f: f["rank"])
targets = report.get("next_game_targets", [])
one_thing = report.get("one_thing", "")
shot_path = os.path.join(HERE, "work", "qa", "review_shot.jpg")
has_shot = os.path.exists(shot_path)
review_img = img(shot_path, max_w=760, quality=72) if has_shot else None
caption_img = img(os.path.join(ASSETS, "treat_caption_bar.jpg"), max_w=760, quality=74)
pose_img = img(os.path.join(ASSETS, "treat_pose.jpg"), max_w=760, quality=74)

# ------------------------------------------------------------------ run numbers for D4
A = stats.get("full_verify", {"agents": 51, "minutes": 95})
B = stats.get("shots_only", {"agents": 14, "minutes": 25})
C = stats.get("full_no_verify", {"agents": 31, "minutes": 55})
maxa = max(A["agents"], B["agents"], C["agents"]); maxm = max(A["minutes"], B["minutes"], C["minutes"])


def bar(name, val, mx, unit, cls=""):
    return (f'<div class="bar-row"><div class="bar-name">{esc(name)}</div><div class="bar-track"><div class="bar {cls}" '
            f'style="width:{int(val / mx * 100)}%"></div></div><div class="bar-val num">{val} {unit}</div></div>')


# ------------------------------------------------------------------ option / card helpers
def option(name, letter, title, what, bad, rec=False, tags=()):
    tg = "".join(f'<span class="tag {c}">{esc(t)}</span>' for t, c in tags)
    return f"""<label class="option{' recommended' if rec else ''}">
  <input type="radio" name="{name}" value="{letter} — {esc(title)}">
  <div>
    <div class="option-t">{letter} — {esc(title)}{' <span class="badge">Recommended</span>' if rec else ''}</div>
    <div class="option-d">{esc(what)}</div>
    <span class="downside"><b>What's bad:</b> {esc(bad)}</span>
    {f'<div class="option-meta">{tg}</div>' if tg else ''}
  </div>
</label>"""


def note(n, placeholder):
    return f'<div class="note"><label for="n{n}">Notes or changes for decision {n}</label><textarea id="n{n}" placeholder="{esc(placeholder)}"></textarea></div>'


def card(n, title, ask, body, preview=None):
    cls = "card with-preview" if preview else "card"
    inner = f'<div class="card-body"><div>{body}</div>{preview}</div>' if preview else f'<div class="card-body">{body}</div>'
    return f"""<article class="{cls}" id="d{n}" data-decision="{n}">
  <div class="card-head"><div class="card-n">{n}</div><h2 class="card-title" data-title>{esc(title)}</h2></div>
  <div class="ask">{esc(ask)}</div>
  {inner}
</article>"""


cards = []
tldr = []

# ================================================================== D1 main deliverable
cue_lines = "".join(f'<div class="ui-row"><span>Fix {f["rank"]}</span><b>{esc(f["cue"])}</b></div>' for f in fixes) or '<div class="ui-row"><span>Fix 1</span><b>cue</b></div>'
target_lines = "".join(f'<div class="ui-row"><span>{esc(t["metric"])}</span><b class="num">{esc(t["this_game"])} → {esc(t["target"])}</b></div>' for t in targets[:4])
phone_card = f"""<div class="frame phone"><div class="frame-chrome"><span class="frame-notch"></span></div>
<div class="frame-screen" style="font-size:12px;line-height:1.4">
  <div style="font-size:10px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--pumpkin-orange)">Next game · one thing</div>
  <div style="font-weight:600;margin:4px 0 8px">{esc(one_thing or 'The single change to carry into the next game.')}</div>
  <div class="ui-tile">{cue_lines}</div>
  <div class="ui-tile" style="margin-top:8px">{target_lines or '<div class="ui-row"><span>Targets</span><b>4 metrics</b></div>'}</div>
</div></div>"""
def short(s, n=58):
    s = re.split(r"[.:;]", s)[0].strip()
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + "…"


# The pane is 340 px wide: the review is shown as its real text (headline, fixes, line), not as a shrunken page.
# The thumbnail and the stills open full-size in the lightbox; the real files are linked.
fix_rows = "".join(f'<div class="ui-row"><span style="color:var(--text-tertiary);flex-shrink:0">Fix {f["rank"]}</span><b style="font-weight:600;text-align:right">{esc(short(f["what"]))}</b></div>' for f in fixes) or '<div class="ui-row"><span>Fix 1</span><b>the first fix</b></div>'
review_thumb = img(shot_path, max_w=320, quality=70, crop=(0, 0, 880, 560)) if has_shot else None
review_mock = f"""<div class="frame"><div class="frame-chrome"><i></i><i></i><i></i><div class="frame-url">Barak_Offense_Review_2026-10-07.html</div></div>
<div class="frame-screen" style="font-size:12.5px;line-height:1.45">
  <div style="font-size:10px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--pumpkin-orange)">The short version</div>
  <div style="font-weight:600;font-size:13px;margin:4px 0 8px">{esc(report.get("headline", "The headline of the review."))}</div>
  <div class="ui-tile">{fix_rows}</div>
  <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:8px"><span class="tag">12 pts</span><span class="tag">5/13 FG</span><span class="tag pos">eFG 46%</span><span class="tag">13 shots graded</span><span class="tag">27 possessions</span></div>
  {f'<img class="zoomable" src="{review_thumb}" data-full="assets/review_full.jpg" alt="The review page. Click to read it full-size." style="display:block;width:100%;height:auto;margin-top:10px;border:1px solid var(--border-default);border-radius:var(--r-1)"><div style="font-size:11px;color:var(--text-tertiary);margin-top:4px">Thumbnail of the page: click it to read it full-size.</div>' if review_thumb else ''}
</div></div>"""
clip_block = f'<div style="margin-top:10px"><img class="zoomable" src="{caption_img}" data-full="assets/treat_caption_bar.jpg" alt="A coaching clip: live play with the caption bar. Click to enlarge." style="display:block;width:100%;height:auto;border-radius:var(--r-1)"><div style="font-size:12px;color:var(--text-tertiary);margin-top:6px">3-5 clips like this, 12-20 s each: live with a caption, slow replay, freeze frame with the cue. Click the frame to enlarge.</div></div>'
link_review = '<a href="../analysis_2026-10-07/Barak_Offense_Review_2026-10-07.html" target="_blank">Open the real review</a>'
link_clip = '<a href="assets/coaching_clip_example_fix1_c05.mp4" target="_blank">Play a real clip (fix 1)</a>'
d1_preview = f"""<aside class="live" data-live="d1">
  <div class="label">Live Preview</div>
  <div class="live-stage">
    <div class="pv is-active" data-opt="A">{review_mock}{clip_block}<div class="live-open">{link_review}{link_clip}</div></div>
    <div class="pv" data-opt="B">{review_mock}<div style="font-size:12px;color:var(--text-tertiary);margin-top:8px">No video. The teaching moments stay as still frames inside the page.</div><div class="live-open">{link_review}</div></div>
    <div class="pv" data-opt="C">{clip_block.replace('margin-top:10px', 'margin-top:0')}<div style="font-size:12px;color:var(--text-tertiary);margin-top:8px">No written review. Stats, shot chart and drills do not exist in this option.</div><div class="live-open">{link_clip}</div></div>
    <div class="pv" data-opt="D">{phone_card}<div style="font-size:12px;color:var(--text-tertiary);margin-top:8px">One phone screen, read before the next game. Nothing to scroll.</div></div>
  </div>
  <div class="live-hint">Pick an option — this updates.</div>
</aside>"""
d1_body = f"""<p class="narrative">After every game he hands over the reel and gets something back. This game: 27 possessions, 13 shots, 3 fixes. The research is clear on the shape: strengths first, at most three teaching points, 3-5 clips per point, one cue at a time, and the clips are what change behaviour. The written page is where the numbers, the shot chart and the drills live.</p>
<div class="viz"><div class="viz-title">What each option gives him after a game</div>
<table class="matrix">
<tr><th>What he gets</th><th class="rec-col">A — Review + clips</th><th>B — Review only</th><th>C — Clips only</th><th>D — Cue card</th></tr>
<tr><td>Sees the mistake move, not a sentence about it</td><td class="good rec-col">Yes, slow replay</td><td class="mid">Still frames</td><td class="good">Yes</td><td class="bad">No</td></tr>
<tr><td>Numbers, shot chart, drills in one place</td><td class="good rec-col">Yes</td><td class="good">Yes</td><td class="bad">No</td><td class="bad">No</td></tr>
<tr><td>Fits in 2 minutes before the next game</td><td class="mid rec-col">The summary box does</td><td class="mid">Summary box</td><td class="mid">Watch 3 clips</td><td class="good">Yes</td></tr>
<tr><td>Time to produce after the analysis</td><td class="mid rec-col">~15 min</td><td class="good">~2 min</td><td class="mid">~12 min</td><td class="good">~1 min</td></tr>
</table>
<div class="viz-cap">Green is better on that row. The highlighted column is what I recommend. The cue card in D is also included inside A and B as the dark summary box at the top.</div></div>
<div class="label">Where This Lives</div>
<div class="where"><b>analysis_2026-10-07/build_report.py</b> — assembles the HTML review<br><b>analysis_2026-10-07/make_coaching_clip.py</b> — renders one captioned clip from a spec<br><b>analysis_2026-10-07/make_clip_specs.py</b> — picks the moments and writes the specs</div>
<div class="label">Pick One</div>
<div class="options">
{option('d1', 'A', 'HTML review plus 3-5 captioned coaching clips', 'The page you can open now, plus short clips of the teaching moments: live, slow replay, freeze frame with the cue. Captions come from the verified report only.', 'Two things to open, and the clips add about 15 minutes of rendering per game.', rec=True, tags=[('what the research recommends', 'pos'), ('~15 min extra', '')])}
{option('d1', 'B', 'HTML review only', 'The same page with still frames for the teaching moments. No video.', 'A still frame does not show the hitch, the drift or the late contest; he would scrub the reel himself to see them.', tags=[('fastest', 'pos')])}
{option('d1', 'C', 'Captioned clips only', 'A 2-3 minute coaching video and nothing else.', 'The shot chart, the counts, the drills and the targets have no home; next game there is nothing to compare against.', tags=[('no numbers', 'neg')])}
{option('d1', 'D', 'Phone cue card only', 'One screen: the one thing, three cues, four targets.', 'He never sees the evidence, so the cues are easy to argue with and easy to forget.', tags=[('lightest', '')])}
</div>
{note(1, 'e.g. A, but cap the clips at three')}"""
cards.append(card(1, "The main thing he gets after every game", "Which package should every game produce: review page, clips, both, or a cue card?", d1_body, d1_preview))
tldr.append(("The main thing he gets after every game", "A", "Review page plus 3-5 captioned clips"))

# ================================================================== D2 close-up camera
court_svg = """<svg viewBox="0 0 640 360" width="100%" style="max-width:640px;display:block;margin:0 auto" role="img" aria-label="court with camera positions">
  <rect x="20" y="20" width="600" height="320" rx="6" fill="#F7F7F8" stroke="#D9DCDF"/>
  <!-- half court, basket at the right -->
  <rect x="440" y="110" width="150" height="140" fill="#F2E3DD" stroke="#D9DCDF"/>
  <line x1="590" y1="20" x2="590" y2="340" stroke="#BDBFC2" stroke-width="2"/>
  <path d="M 590 62 A 170 170 0 0 0 590 298" fill="none" stroke="#fff" stroke-width="4"/>
  <path d="M 590 62 A 170 170 0 0 0 590 298" fill="none" stroke="#BDBFC2" stroke-width="2"/>
  <circle cx="440" cy="180" r="34" fill="none" stroke="#BDBFC2" stroke-width="2"/>
  <circle cx="570" cy="180" r="7" fill="none" stroke="#FF6B00" stroke-width="3"/>
  <!-- shooter at the top of the arc -->
  <circle cx="405" cy="180" r="9" fill="#181C21"/><text x="405" y="206" font-size="11" text-anchor="middle" fill="#5B616E" font-family="Inter,Arial">shooter, top of the arc</text>
  <!-- camera 1: existing wide, near sideline mid-court -->
  <g id="cam1"><rect x="236" y="318" width="26" height="16" rx="3" fill="#181C21"/><polygon points="262,320 276,314 276,338 262,332" fill="#181C21"/>
    <path d="M 249 318 L 380 196 M 249 318 L 590 150" stroke="#181C21" stroke-width="1" stroke-dasharray="4 3" opacity=".5"/>
    <text x="249" y="352" font-size="11" text-anchor="middle" fill="#181C21" font-weight="700" font-family="Inter,Arial">1 · wide phone (today)</text></g>
  <!-- camera 2: form session close-up, side-on to the shot on the shooting-hand side, 2-4 m -->
  <g id="cam2"><rect x="394" y="262" width="22" height="14" rx="3" fill="#007C32"/><polygon points="405,262 399,251 411,251" fill="#007C32"/>
    <path d="M 405 262 L 405 192" stroke="#007C32" stroke-width="1.5" stroke-dasharray="4 3"/>
    <text x="405" y="294" font-size="11" text-anchor="middle" fill="#007C32" font-weight="700" font-family="Inter,Arial">2 · close-up, side-on, shooting-hand side, 2-4 m</text>
    <text x="405" y="308" font-size="10" text-anchor="middle" fill="#5B616E" font-family="Inter,Arial">form session only · lens 1.1-1.5 m high · 60 fps, 240 for jump timing</text></g>
  <!-- camera 3: second phone every game, far corner high -->
  <g id="cam3"><rect x="582" y="30" width="22" height="14" rx="3" fill="#FF6B00"/><polygon points="582,32 571,28 571,46 582,42" fill="#FF6B00"/>
    <path d="M 582 37 L 420 170" stroke="#FF6B00" stroke-width="1.5" stroke-dasharray="4 3"/>
    <text x="520" y="56" font-size="11" text-anchor="end" fill="#8A3A00" font-weight="700" font-family="Inter,Arial">3 · second phone every game, far corner, high</text></g>
</svg>"""
d2_body = f"""<p class="narrative">From the sideline phone a player is 100-160 pixels tall. Decisions, footwork, balance, jump and a one- or two-hand finish are readable; the guide-hand thumb, the wrist and the elbow line are not. The July close-up found the two-hand push and the elbow flare. The question is how to keep watching the fine mechanics without filming every game twice.</p>
<div class="viz"><div class="viz-title">Where each camera stands</div>{court_svg}
<div class="viz-cap">Black is the camera he already uses. Green is a phone on a small tripod for a 10-minute form session, side-on to the shot on the shooting-hand side, lens at hip height, 2-4 m away (the research's recommendation). Orange is a second phone at every game.</div></div>
<div class="viz"><div class="viz-title">What each option can and cannot see</div>
<table class="matrix">
<tr><th>Readable</th><th class="rec-col">A — Wide + form session</th><th>B — Second phone every game</th><th>C — Wide only</th></tr>
<tr><td>Shot selection, decisions, spacing</td><td class="good rec-col">Yes</td><td class="good">Yes</td><td class="good">Yes</td></tr>
<tr><td>Footwork, balance, drift, one vs two hands</td><td class="good rec-col">Yes</td><td class="good">Yes</td><td class="good">Yes</td></tr>
<tr><td>Guide hand, elbow line, set point, hitch</td><td class="good rec-col">Every 2-3 weeks, in practice</td><td class="mid">Only when he shoots near that corner</td><td class="bad">Never</td></tr>
<tr><td>Extra work on game night</td><td class="good rec-col">None</td><td class="bad">Second tripod, second file, syncing</td><td class="good">None</td></tr>
</table></div>
<div class="label">Where This Lives</div>
<div class="where"><b>shot_analysis.html</b> — the July close-up form analysis, the template for a form session<br><b>camera_position_guide.html</b> — the existing guide for the wide phone</div>
<div class="label">Pick One</div>
<div class="options">
{option('d2', 'A', 'Keep the wide phone, add a 10-minute close-up form session every 2-3 weeks', 'Games stay as they are. Every few weeks he films 20 shots, one per clip, from a tripod 2-4 m away, side-on to the shot on the shooting-hand side, lens 1.1-1.5 m high, 60 fps (240 when jump timing matters), and the mechanics review runs on that like the July analysis.', 'Practice form and game form differ; the session shows the shape, the games show whether it holds.', rec=True, tags=[('no change on game night', 'pos'), ('one tripod', '')])}
{option('d2', 'B', 'Second phone at every game, far corner, high', 'A second file per game, aimed at the top of the key where most of his shots come from.', 'Someone has to set it up and collect it every week; the far corner still leaves the ball 200-300 pixels tall at best.', tags=[('weekly effort', 'neg')])}
{option('d2', 'C', 'Wide phone only', 'Nothing changes. Mechanics are judged from the wide footage at the level it allows.', 'The guide-hand and elbow fixes from July can never be checked; the review keeps saying "consistent with July".', tags=[('zero effort', '')])}
</div>
{note(2, 'e.g. A, but film the session at 120 fps')}"""
cards.append(card(2, "A close-up camera for shooting mechanics", "Should the fine mechanics come from a periodic form session, a second phone every game, or not at all?", d2_body))
tldr.append(("A close-up camera for shooting mechanics", "A", "Wide phone + a form session every 2-3 weeks"))

# ================================================================== D3 what to track
five = [("eFG%", "27%", "46%", "Shooting efficiency with threes counted 1.5x"), ("Points per shot", "0.50", "0.92", "What a shot is worth"),
        ("Shots worth taking", "", "", "Share of shots graded 3 or more out of 5, before the result"), ("Holds of 2 s or more at the top", "", "", "How often the offense waits on him"),
        ("Passes that led to a shot", "3 ast", "2 ast", "Assists and hockey assists per touch")]
sbs = report.get("shot_by_shot", [])
if sbs:
    keep = sum(1 for s in sbs if s.get("quality_1to5", 0) >= 3)
    five[2] = ("Shots worth taking", "", f"{keep} of {len(sbs)}", five[2][3])
tend = report.get("tendencies", [])
hold = next((t for t in tend if "check" in t["tendency"].lower() and "held" in (t.get("numbers", "") or "").lower()), None)
if hold:
    m = re.match(r"\s*(\d+ of \d+)", hold.get("numbers", "") or "")
    five[3] = ("Check-ball catches still held after 4 s", "", m.group(1) if m else hold.get("numbers", ""), "How often the offense waits on him off the check")
rows = "".join(f'<tr><td>{esc(m)}<div style="font-size:12px;color:var(--text-tertiary)">{esc(d)}</div></td><td class="num">{esc(a) or "—"}</td><td class="num">{esc(b) or "—"}</td><td class="good rec-col">Yes</td><td class="{"good" if i < 2 else "bad"}">{"Yes" if i < 2 else "No"}</td><td class="good">Yes</td></tr>' for i, (m, d, a, b) in enumerate([(f[0], f[3], f[1], f[2]) for f in five]))
d3_body = f"""<p class="narrative">Two games so far: 2 of 12 then 5 of 13 from the field. With 13 shots a game the percentages swing wildly, so the research says track the things that are stable game to game: shot quality, where the shots come from, how long he holds, and what a shot is worth. Each option is a different number of columns in a table that grows by one row per game.</p>
<div class="viz"><div class="viz-title">The table that grows by one row per game: which columns exist under each option</div>
<table class="matrix">
<tr><th>Metric</th><th>23.09</th><th>07.10</th><th class="rec-col">A — Five metrics + trend</th><th>B — Box score only</th><th>C — Full play-type tagging</th></tr>
{rows}
<tr><td>Play type of every possession (11 types)<div style="font-size:12px;color:var(--text-tertiary)">Isolation, pick and roll, spot-up, cut, hand-off, transition...</div></td><td class="num">—</td><td class="num">—</td><td class="bad rec-col">No</td><td class="bad">No</td><td class="good">Yes</td></tr>
<tr><td>Extra tagging work per game</td><td></td><td></td><td class="good rec-col">None, already in the records</td><td class="good">None</td><td class="bad">27 possessions re-tagged</td></tr>
</table>
<div class="viz-cap">The first two columns are the two games so far. Dashes are numbers the previous game was not analysed deeply enough to have; from this game on they exist.</div></div>
<div class="label">Where This Lives</div>
<div class="where"><b>analysis_2026-10-07/results/report.json</b> — next_game_targets and tendencies, the source of the five metrics<br><b>recap_2026-10-07/output/</b> — the stats card the pipeline already produces</div>
<div class="label">Pick One</div>
<div class="options">
{option('d3', 'A', 'Five metrics and a trend line across games', 'eFG%, points per shot, share of shots worth taking, holds of 2 seconds or more, passes that led to a shot. One small table at the top of every review, one row per game, with the target from the previous review next to it.', 'Five numbers from 13 shots stay noisy for the first 5-6 games; the trend is the point, not any single game.', rec=True, tags=[('already produced', 'pos')])}
{option('d3', 'B', 'Box score only', 'Points, field goals, threes, assists, like the stats card today.', 'It cannot tell a good 2 of 12 from a bad 5 of 13, which is exactly the thing this game showed.', tags=[('exists today', '')])}
{option('d3', 'C', 'Full play-type tagging, the way pro scouting services do it', 'Every possession tagged with one of 11 play types and points per possession per type.', 'In a 4-on-4 pickup game most of his possessions fall into two types; 27 tags per game for a chart that barely moves.', tags=[('most work', 'neg')])}
</div>
{note(3, 'e.g. A, plus assists')}"""
cards.append(card(3, "What to track from game to game", "Which numbers should carry over from one review to the next?", d3_body))
tldr.append(("What to track from game to game", "A", "Five metrics plus a trend, one row per game"))

# ================================================================== D4 depth per game
d4_body = f"""<p class="narrative">This game's analysis used one reviewer per possession, three pattern passes, one head-coach pass and a skeptic that re-watched the frames behind every claim. The skeptic changed real things: counts were corrected and two claims were downgraded. The question is whether every game gets the full treatment or a lighter one.</p>
<div class="viz"><div class="viz-title">Reviewer agents and wall-clock time per game</div>
<div class="bars">
{bar('A — full + verify, agents', A['agents'], maxa, 'agents', 'pos')}{bar('B — shots only, agents', B['agents'], maxa, 'agents', 'c4')}{bar('C — full, no verify, agents', C['agents'], maxa, 'agents', 'c2')}
</div><div style="height:10px"></div><div class="bars">
{bar('A — full + verify, time', A['minutes'], maxm, 'min', 'pos')}{bar('B — shots only, time', B['minutes'], maxm, 'min', 'c4')}{bar('C — full, no verify, time', C['minutes'], maxm, 'min', 'c2')}
</div>
<div class="viz-cap">Time is wall-clock while the analysis runs in the background; he does nothing during it. Agent counts are from this game's run.</div></div>
<div class="viz"><div class="viz-title">What runs under each option</div>
<div class="flow">
<div class="node">Contact sheets<small>automatic</small></div><div class="arr">&rarr;</div>
<div class="node">One reviewer per possession<small>A and C: 27 · B: 13 (shots only)</small></div><div class="arr">&rarr;</div>
<div class="node">Three pattern passes<small>A and C</small></div><div class="arr">&rarr;</div>
<div class="node">Head-coach report<small>all options</small></div><div class="arr">&rarr;</div>
<div class="node good">Skeptic re-watches every claim<small>A only</small></div><div class="arr">&rarr;</div>
<div class="node brand">Review + clips</div>
</div>
<div class="viz-cap">Green is the step that catches wrong counts before he reads them. B drops the 14 possessions without a shot, which is where the passing, rebounding and spacing findings came from.</div></div>
<div class="label">Where This Lives</div>
<div class="where"><b>analysis_2026-10-07/workflows/clip_analysis.js</b> — the full pipeline (clips, lenses, report, verify)<br><b>analysis_2026-10-07/make_sheets.py</b>, <b>make_briefs.py</b> — the sheets and briefs the reviewers read</div>
<div class="label">Pick One</div>
<div class="options">
{option('d4', 'A', 'Full review with the skeptic pass, every game', 'All 27 possessions, the three pattern passes, the report, and a skeptic that re-watches the frames behind every strength, weakness, tendency and fix. Verdicts show next to each claim in the review.', f'About {A["minutes"]} minutes of background time per game and the most agents.', rec=True, tags=[('what this game got', 'pos'), (f'{A["agents"]} agents', '')])}
{option('d4', 'B', 'Shots only', 'Only the possessions with a shot (13 this game) get a reviewer; the report is about shot selection and mechanics.', 'Passing, rebounding, spacing and the hold-time habit disappear from the review; two of the three fixes from this game would not exist.', tags=[('fastest', 'pos'), (f'{B["agents"]} agents', '')])}
{option('d4', 'C', 'Full review, no skeptic pass', 'Everything in A except the re-watch.', 'Counts and claims go to him unchecked; this game the skeptic corrected several.', tags=[(f'{C["agents"]} agents', '')])}
</div>
{note(4, 'e.g. A for now, B when the game was short')}"""
cards.append(card(4, "How deep the analysis goes each game", "Full review with a skeptic pass, shots only, or full without the skeptic?", d4_body))
tldr.append(("How deep the analysis goes each game", "A", "Full review with the skeptic pass"))

# ================================================================== D5 drill plan format
session = drills.get("session", [])
sess_rows = "".join(f'<div class="ui-row"><span class="num">{esc(s["min"])} min</span><b style="font-weight:500;text-align:right;max-width:70%">{esc(s["what"])}</b></div>' for s in session) or \
            '<div class="ui-row"><span>5 min</span><b>warm-up form shots</b></div><div class="ui-row"><span>8 min</span><b>pull-ups, make count</b></div><div class="ui-row"><span>7 min</span><b>catch and go</b></div><div class="ui-row"><span>5 min</span><b>finishing</b></div>'
phone_session = f"""<div class="frame phone"><div class="frame-chrome"><span class="frame-notch"></span></div>
<div class="frame-screen" style="font-size:12px;line-height:1.4">
  <div style="font-size:10px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--pumpkin-orange)">25-minute session · after game 07.10</div>
  <div class="ui-tile" style="margin-top:6px">{sess_rows}</div>
  <div style="font-size:11px;color:var(--text-tertiary);margin-top:8px">Track the make counts, not the minutes.</div>
</div></div>"""
d5_preview = f"""<aside class="live" data-live="d5">
  <div class="label">Live Preview</div>
  <div class="live-stage">
    <div class="pv is-active" data-opt="A">{phone_session}<div style="font-size:12px;color:var(--text-tertiary);margin-top:8px">The full drill table with sources stays in the review; this is the card he takes to the court.</div></div>
    <div class="pv" data-opt="B"><div class="frame"><div class="frame-chrome"><i></i><i></i><i></i><div class="frame-url">review.html#drills</div></div><div class="frame-screen"><div class="ui-bar w-50 dark"></div><div class="ui-tile" style="margin-top:8px"><div class="ui-row"><span>Drill</span><b>How · reps · cue</b></div><div class="ui-row"><span>Drill</span><b>How · reps · cue</b></div><div class="ui-row"><span>Drill</span><b>How · reps · cue</b></div></div></div></div><div style="font-size:12px;color:var(--text-tertiary);margin-top:8px">A table in the review page only. Nothing phone-sized.</div></div>
    <div class="pv" data-opt="C"><div class="frame"><div class="frame-chrome"><i></i><i></i><i></i><div class="frame-url">weekly-checklist.html</div></div><div class="frame-screen"><div class="ui-bar w-70 dark"></div><div class="ui-tile" style="margin-top:8px"><div class="ui-row"><span>Mon</span><b>form 50 makes</b></div><div class="ui-row"><span>Wed</span><b>pull-ups 30 makes</b></div><div class="ui-row"><span>Fri</span><b>game</b></div></div></div></div><div style="font-size:12px;color:var(--text-tertiary);margin-top:8px">A separate weekly document with tick boxes.</div></div>
  </div>
  <div class="live-hint">Pick an option — this updates.</div>
</aside>"""
d5_body = f"""<p class="narrative">The review maps 2-3 drills to each fix, with reps, a cue and a source. The question is what he carries to the court. The research is blunt about adult amateurs: short sessions, make counts instead of minutes, one cue at a time, and the plan must fit on a phone.</p>
<div class="viz"><div class="viz-title">How each format gets used in a week</div>
<div class="steps">
<div class="step"><div class="step-n">1</div><div><div class="step-t">Game night</div><div class="step-d">Reel handed over, analysis runs in the background.</div></div></div>
<div class="step"><div class="step-n">2</div><div><div class="step-t">Next day: he reads the review</div><div class="step-d">Fixes, shot chart, drills table. Same in every option.</div></div></div>
<div class="step now"><div class="step-n">3</div><div><div class="step-t">A practice session during the week</div><div class="step-d">A: opens the session card on his phone. B: scrolls the review table on the court. C: opens the weekly checklist document.</div></div></div>
<div class="step"><div class="step-n">4</div><div><div class="step-t">Next game</div><div class="step-d">The one cue, then a new reel.</div></div></div>
</div>
<div class="viz-cap">Orange marks the only step this decision changes.</div></div>
<div class="label">Where This Lives</div>
<div class="where"><b>analysis_2026-10-07/drills.json</b> — the curated drills and the 25-minute session<br><b>results/research.md</b> section 4 — the drill library with sources</div>
<div class="label">Pick One</div>
<div class="options">
{option('d5', 'A', 'Drill table in the review plus a phone-size session card', 'The review keeps the full table with sources. A second, phone-sized card lists the 25-minute session with make counts, one per fix.', 'One more file per game, and the session card goes stale if he skips two weeks.', rec=True, tags=[('phone-sized', 'pos')])}
{option('d5', 'B', 'Drill table in the review only', 'Everything stays on the review page.', 'Scrolling a long page on the court between reps; make counts are not tracked anywhere.', tags=[('no extra file', '')])}
{option('d5', 'C', 'A separate weekly checklist document', 'A standing document with the sessions of the week and tick boxes, updated after each review.', 'A third artefact to maintain; the research says the plan should change with the review, not live apart from it.', tags=[('most upkeep', 'neg')])}
</div>
{note(5, 'e.g. A, as an image I can send to WhatsApp')}"""
cards.append(card(5, "How the drill plan reaches the court", "Table in the review, a phone session card as well, or a weekly checklist document?", d5_body, d5_preview))
tldr.append(("How the drill plan reaches the court", "A", "Review table plus a phone session card"))

# ================================================================== D6 automated measurements
JOINTS = ["nose", "left eye", "right eye", "left ear", "right ear", "left shoulder", "right shoulder", "left elbow", "right elbow",
          "left wrist", "right wrist", "left hip", "right hip", "left knee", "right knee", "left ankle", "right ankle"]
conf = pose.get("joint_conf", [])
good = sum(1 for c in conf if c >= 0.75)
jbars = "".join(bar(j, round(c * 100), 100, '%', 'pos' if c >= 0.75 else 'neg') for j, c in zip(JOINTS, conf))
r_elbow = pose.get("r_elbow"); r_knee = pose.get("r_knee"); l_knee = pose.get("l_knee")
d6_body = f"""<p class="narrative">A pose model was run on the release frame of his open three (clip 18), on a 2x enlarged crop. Body joints are found with high confidence; face joints and the left wrist are not, so a left-elbow angle cannot be printed. The angles it does give are approximate: a side view from 15 m, no calibration.</p>
<div class="viz"><div class="viz-title">What the model is sure about on a 130-pixel player</div>
<div class="stats">
<div class="stat pos"><div class="stat-label">Joints found</div><div class="stat-value num">{good} / 17</div><div class="stat-sub">confidence 0.75 or more</div></div>
<div class="stat"><div class="stat-label">Right elbow at release</div><div class="stat-value num">{f"{r_elbow:.0f}°" if r_elbow else "n/a"}</div><div class="stat-sub">approximate, side view</div></div>
<div class="stat"><div class="stat-label">Knees at release</div><div class="stat-value num">{f"{r_knee:.0f}° / {l_knee:.0f}°" if r_knee and l_knee else "n/a"}</div><div class="stat-sub">right / left, already straight</div></div>
<div class="stat neg"><div class="stat-label">Left wrist</div><div class="stat-value num">{f"{conf[9]*100:.0f}%" if len(conf) > 9 else "n/a"}</div><div class="stat-sub">too unsure to print an angle</div></div>
</div>
<div style="height:14px"></div>
<div class="bars">{jbars}</div>
<div class="viz-cap">Green is a joint the overlay can use; red is shown as "n/a". The research puts the useful range of single-camera pose estimation at elbow and knee angles and jump timing, not hands or fingers.</div></div>
<div class="viz"><div class="viz-title">What the overlay looks like today</div><img class="zoomable" src="{pose_img}" data-full="assets/treat_pose.jpg" alt="The pose overlay on the release frame of clip 18. Click to enlarge." style="display:block;width:100%;height:auto;border-radius:var(--r-1)"><div class="viz-cap">Rendered from the same frame. The numbers in the corner are what option A would show, labelled approximate. Click the image to see it full-size.</div></div>
<div class="label">Where This Lives</div>
<div class="where"><b>analysis_2026-10-07/make_treatments.py</b> — the pose overlay renderer (YOLO11 pose on a 2x crop)<br><b>analysis_2026-10-07/work/pose/angles_c077.json</b> — the measured angles and joint confidences</div>
<div class="label">Pick One</div>
<div class="options">
{option('d6', 'A', 'Pose overlay on each shot now, every number labelled approximate', 'A small panel per shot in the review: elbow and knee angles at the release, jump timing, with "n/a" where the model is unsure.', 'Approximate numbers invite over-reading; a 137° elbow from the side says little about the elbow flare the July close-up found.', tags=[('exists today', 'pos'), ('approximate', 'neg')])}
{option('d6', 'B', 'Pose measurements only on the close-up form session footage', 'Nothing on the wide game footage. When the form session from decision 2 exists, the model runs on a 600-pixel player and the angles mean something.', 'No numbers until the first form session; game reviews stay judged by eye.', rec=True, tags=[('honest numbers', 'pos')])}
{option('d6', 'C', 'No automated measurements', 'Mechanics stay a judgement by eye in the records and the report.', 'The July findings are never measured again, only described.', tags=[('simplest', '')])}
</div>
{note(6, 'e.g. B, but keep the knee angles on game shots')}"""
cards.append(card(6, "Automated body measurements from the footage", "Should the review print pose-model angles from the wide footage now, only from close-up sessions, or not at all?", d6_body))
tldr.append(("Automated body measurements from the footage", "B", "Only on close-up form-session footage"))

# ================================================================== D7 creative gallery: treatment
TREATS = [
    ("A", "caption_bar", "Caption bar", "Live play with one sentence at the bottom, then a slow replay. What the test clip already does.", "Plain; nothing points at the body part, the eye has to find it."),
    ("B", "freeze_ring", "Freeze + ring + arrow", "The replay stops on the key frame; a ring marks the shooter and an arrow names what happened.", "Needs a hand-placed ring per clip; wrong placement looks worse than none."),
    ("C", "coach_card", "Coach card", "A dark card in the corner: fix number, title, cue, the count behind it.", "Covers a fifth of the frame; reads like a slide, not like film."),
    ("D", "split", "Wide + follow split", "Wide view for the decision on the left, a tracked close window on the right, side by side.", "Each half is small; the follow window jumps when the tracker loses him."),
    ("E", "telestration", "Telestration on the floor", "A shaded zone and an arrow drawn on the court: where the space was, where to go.", "Only works for decision moments; nothing to draw on a mechanics clip."),
    ("F", "before_after", "July practice vs October game", "Practice release next to the game release, same moment of the shot.", "The two angles differ, so it suggests more than it proves."),
    ("G", "pose", "Pose skeleton", "The model's skeleton drawn on the shooter with the measured angles.", "Approximate numbers on a 130-pixel player; see decision 6."),
]
gopts = []
for letter, key, name, body, bad in TREATS:
    src = img(os.path.join(ASSETS, f"treat_{key}.jpg"), max_w=640, quality=74)
    rec = letter == "A"
    gopts.append(f"""<div class="gopt{' recommended' if rec else ''}">
  <label class="gopt-pick"><input type="radio" name="d7" value="{letter} — {esc(name)}"><span class="gopt-letter">{letter}</span><span class="gopt-name">{esc(name)}</span>{' <span class="badge">Recommended</span>' if rec else ''}</label>
  <div class="gopt-body" style="padding:0;overflow:hidden"><img class="zoomable" src="{src}" data-full="assets/treat_{key}.jpg" alt="{esc(name)}. Click to enlarge." style="display:block;width:100%;height:auto"><div style="padding:10px 12px;font-size:13.5px">{esc(body)}</div></div>
  <span class="downside"><b>What's bad:</b> {esc(bad)}</span>
  <label class="gopt-also"><input type="checkbox" data-shortlist="d7" value="{letter}"> Also use this</label>
</div>""")
d7_body = f"""<p class="narrative">Seven ways to draw on a coaching clip, each rendered from the same open three in clip 18 so they compare fairly. The research favours clips that show one thing, name it in a few words and pause on it. Pick the base treatment; tick the ones to layer on top where they fit. Click any tile to see it full-size.</p>
<div class="label">Pick One — 7 Rendered Treatments</div>
<div class="gallery">
{''.join(gopts)}
</div>
<p class="gallery-hint">Pick the base treatment for every clip. Tick "Also use this" on any others worth layering where they fit; they come back as a shortlist, not as your pick.</p>
{note(7, 'e.g. A as the base, B on the mechanics clips')}"""
cards.append(card(7, "The look of the coaching clips", "Which on-screen treatment should the coaching clips use as their base?", d7_body))
tldr.append(("The look of the coaching clips", "A", "Caption bar, with freeze + ring where it helps"))

# ================================================================== assemble
t = open(TEMPLATE, encoding="utf-8").read()
head_end = t.index('<div class="wrap">') + len('<div class="wrap">')
tail_start = t.index('<!-- ===================== GENERAL FEEDBACK')
head, tail = t[:head_end], t[tail_start:]
TOPIC = "Offense review outputs"
head = head.replace("{{TOPIC}} — Decision Map", f"{TOPIC} — Decision Map").replace("{{TOPIC}} — decision map", f"{TOPIC} — decision map").replace("{{PROJECT}} · {{DATE}}", "Basketball · offense review · 09.10.2026")
head = head.replace("{{One or two sentences: what this round covers, and what happens after he pastes the\n      summary back. Name the topic boundary explicitly — nothing outside it belongs in this file.}}",
                    "What the recurring per-game offense review should produce and how deep it should go, decided once so every future game runs the same way. "
                    "Outside this map: the content of this game's review itself and the recap pipeline.")
head = head.replace('<span class="pill"><strong>{{N}}</strong> decisions</span>', '<span class="pill"><strong>7</strong> decisions</span>')
head = head.replace('<span class="pill">Est. review <strong>{{X}} min</strong></span>', '<span class="pill">Est. review <strong>15 min</strong></span>')
head = head.replace('<span class="pill brand">Round <strong>{{R}}</strong></span>', '<span class="pill brand">Round <strong>1</strong></span>')
tail = tail.replace('"{{TOPIC}} — Decision Summary"', f'"{TOPIC} — Decision Summary"')
tldr_html = ['<section class="tldr"><h2>At a Glance — What I\'m Recommending</h2>']
for i, (q, letter, rec) in enumerate(tldr, 1):
    tldr_html.append(f'<div class="tldr-row"><div class="tldr-n">{i}</div><div class="tldr-q">{esc(q)}</div><div class="tldr-rec"><b>{letter}</b> {esc(rec)}</div><a href="#d{i}">Open</a></div>')
tldr_html.append("</section>")
html = head + "\n\n" + "\n".join(tldr_html) + "\n\n" + "\n\n".join(cards) + "\n\n" + tail
assert "{{" not in html.split("<script>")[0], re.findall(r"\{\{.*?\}\}", html)[:5]
os.makedirs(DOCS, exist_ok=True)
open(OUT, "w", encoding="utf-8").write(html)
print("wrote", OUT, f"{os.path.getsize(OUT) / 1e6:.2f} MB", "review screenshot:", "yes" if has_shot else "placeholder")
