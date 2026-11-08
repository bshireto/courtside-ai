"""Assemble the Hebrew offense review (OKC Thunder colours, right-to-left) from the workflow results.

Inputs (results/): report_plain.json (Hebrew report; falls back to report.json per field), records.json (+ log_he.json),
verdicts.json (+ verdicts_he.json), drills_plain.json (falls back to drills.json), glossary.json,
drives.json + drive_patterns.json + drive_verdicts.json (optional), history.json, clip_map.json, shot_chart.*, work/frames.
Output: Barak_Offense_Review_2026-10-07.html (Hebrew). Run build_report.py for the English version (_en).
"""
import json, os, re
from PIL import Image
import htmlkit as K

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.join(HERE, "..", "recap_2026-10-07")
R = lambda *p: os.path.join(HERE, "results", *p)
esc = K.esc


def load(name, default=None):
    try:
        return json.load(open(R(name), encoding="utf-8"))
    except Exception:
        return default


def load_any(path, default=None):
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return default


base = load("report.json")
report = dict(base); report.update({k: v for k, v in (load("report_plain.json") or {}).items() if v})
records = {r["clip"]: r for r in load("records.json")}
log_he = {r["clip"]: r for r in (load("log_he.json") or [])}
verdicts = load("verdicts.json") or []
verdicts_he = {v["claim"].strip()[:160]: v for v in (load("verdicts_he.json") or [])}
drills = load("drills_plain.json") or json.load(open(os.path.join(HERE, "drills.json"), encoding="utf-8"))
_dd = None
try:
    _dd = json.load(open(os.path.join(HERE, "drills_drive_he.json"), encoding="utf-8"))
except Exception:
    pass
if _dd and not any(f.get("rank") == _dd["rank"] for f in drills["fixes"]):
    drills["fixes"].append(_dd)
glossary = load("glossary.json") or []
drives = load("drives.json") or []
patterns = load("drive_patterns_final.json") or load("drive_patterns.json") or {}
DRIVE_FINAL = bool(load("drive_patterns_final.json"))
DRIVE_NOTES = {n["clip"]: n["note"] for n in (patterns.get("drive_notes") or [])}
drive_verdicts = load("drive_verdicts.json") or []
history = json.load(open(os.path.join(HERE, "history.json"), encoding="utf-8"))
SCOPE = load_any(os.path.join(HERE, "scope.json")) or {}


def DROP(key):
    """Indexes, ranks or ids that scope.json removes from the review."""
    return set(SCOPE.get(key, []))


_drop_moments = {(c_, float(t_)) for c_, t_ in SCOPE.get("drop_moments", [])}
report["teaching_moments"] = [m for m in report["teaching_moments"] if (m["clip"], float(m["reel_time"])) not in _drop_moments]
clips = json.load(open(os.path.join(HERE, "clip_map.json"), encoding="utf-8"))
chart = json.load(open(os.path.join(HERE, "shot_chart.json"), encoding="utf-8"))
made_by_id = {c["id"]: c["made"] for c in chart}
tl = json.load(open(os.path.join(GAME, "data", "user_timeline_v2.json"), encoding="utf-8"))["frames"]
tl.sort(key=lambda f: f["t"])
DRIVE_IMG = os.path.join(HERE, "work", "drives")


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


VERDICT_HE = {"confirmed": "אומת", "partly": "אומת חלקית", "refuted": "הופרך", "not_visible": "לא נראה בפריימים"}


def verdict_for(prefix, key):
    for v in verdicts:
        if v["claim"].startswith(prefix) and key[:40] in v["claim"]:
            return v
    return None


def vbadge(v):
    if not v:
        return ""
    he = verdicts_he.get(v["claim"].strip()[:160], {})
    tip = he.get("evidence_he") or v.get("evidence", "")
    return f'<span class="verdict {v["verdict"]}" title="{esc(tip)}">{VERDICT_HE.get(v["verdict"], v["verdict"])}</span>'


def correction_text(v):
    he = verdicts_he.get(v["claim"].strip()[:160], {})
    return he.get("corrected_claim_he") or v.get("corrected_claim", "")


def long_text(text, limit=520, label="להמשיך לקרוא"):
    if len(text) <= limit:
        return esc(text)
    head = text[:limit].rsplit(" ", 1)[0]
    return f'{esc(head)}&hellip; <details class="more" style="margin-top:8px"><summary>{label}</summary><div class="more-body">{esc(text)}</div></details>'


tm = report["teaching_moments"]
used_moments = set()


def pick_moments(evidence_clips, kind, n):
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


def frames_block(items):
    out = ['<div class="frames">']
    for it in items:
        src = frame_img(it["reel_time"])
        if not src:
            continue
        cls = "pos" if it.get("kind") == "positive" else "neg"
        tag = "מה לשמור" if it.get("kind") == "positive" else "מה לשנות"
        out.append(f'<div class="frame-card {cls}"><img src="{src}" alt=""><div class="frame-cap"><b>{tag} · קליפ {it.get("clip", "")} · {fmt(it["reel_time"])}</b>{esc(it["caption"])}</div></div>')
    out.append("</div>")
    return "".join(out)


def stat(label, val, sub="", cls=""):
    return f'<div class="stat {cls}"><div class="stat-label">{label}</div><div class="stat-value num">{val}</div><div class="stat-sub">{sub}</div></div>'


SIMS = load_any(os.path.join(HERE, "work", "weavy", "sims.json")) or {}


def sim_block(key):
    sm = SIMS.get(str(key))
    if not sm or not os.path.exists(os.path.join(HERE, sm["img"])):
        return ""
    return (f'<div class="viz"><div class="viz-title">{esc(sm["title"])}</div><img src="{K.img_b64(os.path.join(HERE, sm["img"]), max_w=1600, quality=84)}" alt="">'
            f'<div class="viz-cap">{esc(sm["cap"] + sm.get("cap_extra", ""))}</div></div>')


CLIP_DIR = os.path.join(HERE, "clips", "phone")
CLIPS = {
    "all": ("Barak_Coaching_Clips_2026-10-07.mp4", "כל שבעת הקליפים ברצף (1:46)"),
    "fix1": ("1_fix1_decide_on_the_catch.mp4", "תיקון 1 · קליפ 5: קיבלת פנוי ולא החלטת"),
    "keep_quick": ("2_keep_quick_shot.mp4", "מה לשמור · קליפ 3: קבלה וזריקה תוך 0.9 שניות"),
    "fix2": ("3_fix2_step_back_for_three.mp4", "תיקון 2 · קליפ 0: צעד אחד אחורה וזו שלשה"),
    "compare": ("4_compare_same_spot.mp4", "השוואה: אותו מקום, מתוך תנועה מול אחרי החזקה"),
    "keep_runner": ("5_keep_runner.mp4", "מה לשמור · קליפ 8: ה-runner"),
    "fix3": ("6_fix3_open_teammate.mp4", "תיקון 3 · קליפ 14: חבר לקבוצה לבד למעלה"),
    "drive23": ("7_drive_0424_with_simulation.mp4", "דרייב 4:24 · קליפ 23, עם הסימולציה"),
}
if SCOPE.get("clips_all_label"):
    CLIPS["all"] = (CLIPS["all"][0], SCOPE["clips_all_label"])
FIX_CLIPS = {1: ["fix1", "keep_quick"], 2: ["fix2", "compare"], 3: ["fix3"]}


def video_row(keys):
    """Video players for the given clips (files next to this page, in clips/phone)."""
    cards = []
    for k in keys:
        if SCOPE.get("clips") and k != "all" and k not in SCOPE["clips"]:
            continue
        f, title = CLIPS[k]
        if os.path.exists(os.path.join(CLIP_DIR, f)):
            cards.append(f'<figure class="vid"><video controls preload="metadata" playsinline src="clips/phone/{f}#t=0.6"></video><figcaption>{esc(title)}</figcaption></figure>')
    return f'<div class="vids">{"".join(cards)}</div>' if cards else ""



# ----- numbers
stats = {"pts": 12, "fgm": 5, "fga": 13, "tpm": 2, "tpa": 5, "twom": 3, "twoa": 8, "ast": 2}
prev = {"pts": 6, "fgm": 2, "fga": 12, "tpm": 2, "tpa": 5, "twom": 0, "twoa": 7, "ast": 3}
efg = (stats["fgm"] + 0.5 * stats["tpm"]) / stats["fga"]; efg_prev = (prev["fgm"] + 0.5 * prev["tpm"]) / prev["fga"]
pps = (2 * stats["twom"] + 3 * stats["tpm"]) / stats["fga"]; pps_prev = (2 * prev["twom"] + 3 * prev["tpm"]) / prev["fga"]
tally = {}
for v in verdicts:
    tally[v["verdict"]] = tally.get(v["verdict"], 0) + 1
fixes = [f for f in sorted(report["priority_fixes"], key=lambda f: f["rank"]) if f["rank"] not in DROP("drop_fix_ranks")]
FIXNUM = {f["rank"]: i for i, f in enumerate(fixes, 1)}
body = []

# ----- summary (dark)
sc = report["stat_context"]
cut = max(sc.find("ההכרעות שלי"), sc.find("Calls I made"))
sc_main, sc_more = (sc[:cut].strip(), sc[cut:].strip()) if cut > 0 else (sc, "")
body.append(f"""<section class="tldr" id="top">
<h2>הגרסה הקצרה</h2>
<p>{esc(report["headline"])}</p>
<p class="muted">{esc(sc_main)}</p>
{f'<details class="more"><summary>איפה המאמן הראשי הכריע בין הבודקים</summary><div class="more-body">{esc(sc_more)}</div></details>' if sc_more else ''}
<div class="label" style="color:#C9D6E5;margin-top:14px">הדבר האחד לקחת למשחק הבא</div>
<p>{esc(report["one_thing"])}</p>
<div class="label" style="color:#C9D6E5;margin-top:14px">שלושה תיקונים, לפי סדר ההשפעה</div>
{"".join(f'<div class="tldr-row"><div class="tldr-n">{f["rank"]}</div><div class="tldr-q">{esc(f["what"])}<small>משפט לעצמך: {esc(f["cue"])}</small></div></div>' for f in fixes)}
</section>""")

if SCOPE.get("top"):
    T = SCOPE["top"]
    body[-1] = (f'<section class="tldr" id="top"><h2>{esc(T["title"])}</h2>' +
                "".join(f'<div class="tldr-row"><div class="tldr-n">{i}</div><div class="tldr-q" style="font-size:18px">{esc(it["do"])}'
                        f'<small style="font-size:15px;margin-top:4px">{esc(it["why"])} <a href="{it["link"]}" style="color:var(--sun)">{esc(it["link_text"])}</a></small></div></div>'
                        for i, it in enumerate(T["items"], 1)) + "</section>")

# ----- the line
body.append(f"""<section class="card" id="stats">
<h2>השורה</h2>
<p class="lead">שלושה מתוך ארבעת המשחקים; כל סל נבדק ליד הטבעת. המשחק הקודם (23.09) מוצג בשביל ההקשר, לא כמגמה: שני משחקים הם מדגם קטן.</p>
<div class="stats">
{stat("נקודות", stats["pts"], f"במשחק הקודם {prev['pts']}")}
{stat("זריקות מהשדה", f"{stats['fgm']}/{stats['fga']}", f"{stats['fgm']/stats['fga']*100:.0f}% · קודם {prev['fgm']}/{prev['fga']}")}
{stat("שלשות", f"{stats['tpm']}/{stats['tpa']}", f"{stats['tpm']/stats['tpa']*100:.0f}% · קודם {prev['tpm']}/{prev['tpa']}", "pos")}
{stat("זריקות לשתיים", f"{stats['twom']}/{stats['twoa']}", f"{stats['twom']/stats['twoa']*100:.0f}% · קודם {prev['twom']}/{prev['twoa']}", "neg")}
{stat("אסיסטים", stats["ast"], f"קודם {prev['ast']}")}
{stat("אחוז קליעה משוקלל", f"{efg*100:.0f}%", f"קודם {efg_prev*100:.0f}% · שלשה נספרת כאחת וחצי קליעות", "accent")}
{stat("נקודות לזריקה", f"{pps:.2f}", f"קודם {pps_prev:.2f} · כמה נקודות הניב כל ניסיון", "accent")}
</div>
<div class="viz"><div class="viz-title">שני משחקים, 25 זריקות: השלשות הן שמביאות את הנקודות</div>
<div class="bars">
<div class="bar-row"><div class="bar-name">שלשות, שני המשחקים</div><div class="bar-track"><div class="bar pos" style="width:40%"></div></div><div class="bar-val num">4 מתוך 10 · 40%</div></div>
<div class="bar-row"><div class="bar-name">זריקות לשתיים, שני המשחקים</div><div class="bar-track"><div class="bar neg" style="width:20%"></div></div><div class="bar-val num">3 מתוך 15 · 20%</div></div>
<div class="bar-row"><div class="bar-name">נקודות לכל ניסיון שלשה</div><div class="bar-track"><div class="bar pos" style="width:60%"></div></div><div class="bar-val num">1.20</div></div>
<div class="bar-row"><div class="bar-name">נקודות לכל ניסיון לשתיים</div><div class="bar-track"><div class="bar neg" style="width:20%"></div></div><div class="bar-val num">0.40</div></div>
</div>
<div class="viz-cap">כל ניסיון שלשה הניב פי שלושה נקודות מכל ניסיון לשתיים. עם 25 זריקות האחוזים רועשים, אבל טבלת הזריקות למטה מראה למה הזריקות לשתיים היו קשות.</div></div>
</section>""")

if "stats" in DROP("hide_sections"):
    body.pop()

# ----- game to game (trend + carry-over)
games = [g for g in history["games"] if g.get("kind") == "game"]
form = [] if SCOPE.get("hide_form_followup") else [g for g in history["games"] if g.get("kind") == "form"]
rows = []
for m in history["metrics"]:
    if m["key"] in DROP("drop_metrics"):
        continue
    cells = "".join(f'<td class="num">{esc(g.get("metrics", {}).get(m["key"], "—"))}</td>' for g in games)
    tgt = next((g.get("targets", {}).get(m["key"], "") for g in games[::-1] if g.get("targets", {}).get(m["key"])), "")
    rows.append(f'<tr><td>{esc(m["name"])}<div style="font-size:12px;color:var(--text-tertiary)">{esc(m["explain"])}</div></td>{cells}<td class="num"><strong>{esc(tgt) or "—"}</strong></td></tr>')
STATUS = {"kept": ("נשמר", "good"), "partly": ("חלקית", "mid"), "still": ("עדיין שם", "bad"), "unknown": ("לא ניתן לבדוק", "mid")}
carry = []
for g in form:
    carry.append(f'<h3>{esc(g["label"])}</h3><table class="t"><tr><th>מה מצאנו אז</th><th>מצב במשחק הזה</th><th>סטטוס</th></tr>')
    for it in g["items"]:
        lab, cls = STATUS.get(it["status"], (it["status"], "mid"))
        carry.append(f'<tr><td>{esc(it["what"])}</td><td>{esc(it["now"])}</td><td class="c {cls}">{lab}</td></tr>')
    carry.append("</table>")
nxt = games[-1].get("fixes_for_next_review", [])
if SCOPE.get("track_next"):
    nxt = SCOPE["track_next"] + [x for x in nxt if x.startswith("דרייבים")]
body.append(f"""<section class="card" id="track">
<h2>ממשחק למשחק</h2>
<p class="lead">{esc(SCOPE.get("track_lead") or "חמישה מספרים שחוזרים בכל סקירה, שורה לכל משחק, והיעד שנקבע בסקירה הקודמת לידם. מתחת: מה שכבר עבדנו עליו, והאם זה משתפר.")}</p>
<table class="t"><tr><th>מדד</th>{"".join(f"<th>{esc(g['label'])}</th>" for g in games)}<th>יעד למשחק הבא</th></tr>{"".join(rows)}</table>
<p class="viz-cap">"לא נבדק" = המשחק ההוא לא נותח לעומק הזה; מהמשחק הזה והלאה המספרים קיימים בכל סקירה.</p>
{"".join(carry)}
<h3>מה ייבדק בסקירה הבאה</h3>
<ul>{"".join(f"<li>{esc(x)}</li>" for x in nxt)}</ul>
<p class="callout">{esc(SCOPE.get("track_callout") or "בסקירה הבאה כל אחד משלושת התיקונים מקבל סטטוס: נשמר, חלקית, או עדיין שם, עם הקליפים שמוכיחים את זה.")}</p>
</section>""")

# ----- fixes
fx = [f'<section class="card" id="fixes"><h2>{esc(SCOPE.get("fixes_title") or "שלושה תיקונים, לפי סדר ההשפעה")}</h2><p class="lead">{esc(SCOPE.get("fixes_lead") or "לכל תיקון יש משפט אחד לומר לעצמך על המגרש, תיאור של איך זה נראה כשזה טוב, והפריימים שממנו הוא נולד. חלק התרגילים ממפה כל תיקון לאימון.")}</p>']
for f in fixes:
    ft = (SCOPE.get("fix_text") or {}).get(str(f["rank"]))
    if ft:
        ev = pick_moments(f["evidence_clips"], "corrective", 2)
        fx.append(f"""<div class="fix"><div class="fix-n">{FIXNUM[f["rank"]]}</div><div>
<h3>{esc(ft["title"])}</h3>
<p><strong>מה קרה.</strong> {esc(ft["happened"])}</p>
<p><strong>מה לעשות.</strong> {esc(ft["do"])}</p>
<div class="cue">משפט לעצמך: {esc(ft["cue"])}</div>
<p><strong>איך זה נראה כשזה נעשה נכון.</strong> {esc(ft["good"])}</p>
{frames_block(ev) if ev else ""}
{video_row(FIX_CLIPS.get(f["rank"], []))}
{sim_block("fix" + str(f["rank"]))}
</div></div>""")
        continue
    v = verdict_for("PRIORITY FIX", (base["priority_fixes"][f["rank"] - 1]["what"]))
    ev = pick_moments(f["evidence_clips"], "corrective", 2)
    fx.append(f"""<div class="fix"><div class="fix-n">{f["rank"]}</div><div>
<h3>{esc(f["what"])} {vbadge(v)}</h3>
<p class="why">{esc(f["why_it_matters_most"])}</p>
<div class="cue">משפט לעצמך: {esc(f["cue"])}</div>
<p><strong>איך זה נראה כשזה טוב.</strong> {esc(f["what_good_looks_like"])}</p>
<p class="why">נראה בהתקפות {", ".join(str(c) for c in f["evidence_clips"])}.</p>
{frames_block(ev) if ev else ""}
{video_row(FIX_CLIPS.get(f["rank"], []))}
{sim_block("fix" + str(f["rank"]))}
</div></div>""")
fx.append("</section>")
body.append("".join(fx))

# ----- clips
body.append(f"""<section class="card" id="clips">
<h2>הקליפים</h2>
<p class="lead">{esc(SCOPE.get("clips_lead") or "שבעה קליפים קצרים עם כיתוב: קודם המהלך בזמן אמת, אחר כך בהילוך איטי, ואז פריים עצור עם המשפט לעצמך. הראשון מנגן את כולם ברצף. הקבצים נמצאים בתיקייה clips ליד הדף הזה.")}</p>
{video_row(["all"])}
{video_row(["fix1", "keep_quick", "fix2", "compare", "keep_runner", "fix3", "drive23"])}
</section>""")

# ----- drives
FEET = {"square": "רגליים מקבילות", "left_foot_forward": "רגל שמאל שלו קדימה", "right_foot_forward": "רגל ימין שלו קדימה", "unclear": "לא ברור"}
HAND = {"none": "ידיים למטה", "left": "יד שמאל שלו למעלה", "right": "יד ימין שלו למעלה", "both": "שתי הידיים למעלה", "unclear": "לא ברור"}
WEIGHT = {"flat": "משקל מאוזן", "back_on_heels": "משקל על העקבים", "forward": "נוטה קדימה", "moving_toward": "בתנועה לעברך", "moving_away": "בתנועה אחורה", "unclear": "לא ברור"}
SIDE = {"right": "ימין שלך", "left": "שמאל שלך", "middle": "באמצע", "none": "לא תקפת", "either": "שני הצדדים", "unclear": "לא ברור"}
ANGLE = {"tight_past_hip": "צמוד, ליד הירך שלו", "wide_loop": "רחב מדי, לולאה הצידה", "lateral": "לרוחב, לא לכיוון הסל", "into_chest": "ישר לתוך החזה שלו", "none": "—", "unclear": "לא ברור"}
OUTCOME = {"beat_defender": "עברת את המגן", "contained": "המגן נשאר מולך", "help_stopped": "מגן שני עצר אותך", "pass": "הסתיים במסירה", "shot": "הסתיים בזריקה", "turnover": "איבוד כדור", "other": "אחר"}
RIGHT = {"yes": ("החלטה נכונה", "good"), "partly": ("נכונה חלקית", "mid"), "no": ("החלטה שגויה", "bad"), "unclear": ("לא ברור", "mid")}
HELP = {"right": "בצד ימין שלך", "left": "בצד שמאל שלך", "both": "בשני הצדדים", "none": "לא הייתה עזרה במסלול", "unclear": "לא ברור"}
CONF = {"high": "גבוה", "medium": "בינוני", "low": "נמוך"}
STEP = {"explosive": "צעד ראשון נפיץ", "normal": "צעד ראשון רגיל", "slow": "צעד ראשון איטי", "none": "בלי צעד ראשון", "unclear": ""}
if drives:
    c = patterns.get("counts", {})
    dv = ['<section class="card" id="drives"><h2>הדרייבים שלך: איזה צד, איזו זווית, והיסוס לפני</h2>']
    dv.append('<p class="lead">דרייב = התקפה בכדרור לכיוון הסל. לכל דרייב בדקנו שלושה דברים ששאלת: האם תקפת את הצד שהיה פתוח, האם הזווית שעברת בה את המגן הייתה צמודה או רחבה מדי, והאם תנועת הטעיה (hesitation) החליפה את הדרייב.</p>')
    dv.append('<div class="two"><div><h4>איך קוראים את הצד הפתוח</h4><ul>'
              '<li><strong>הגוף של המגן שלך.</strong> תוקפים את הצד של היד שהוא מרים ושל הרגל שהוא מחזיק קדימה: כדי לעקוב אחריך לשם הוא חייב קודם לסובב את האגן, והיד הנמוכה שלו (זו שיכולה לחטוף את הכדור) נשארת בצד השני.</li>'
              '<li><strong>המראה.</strong> המגן עומד מולך, אז הכל הפוך: יד ימין שלו נמצאת בצד שמאל שלך.</li>'
              '<li><strong>העזרה.</strong> מגן שני שעומד במסלול סוגר את הצד גם אם המגן שלך נתן אותו. לכן בודקים שני דברים בנפרד: מה הגוף של המגן נתן, ואיפה עמדה העזרה.</li>'
              '</ul></div><div><h4>ימין ושמאל, ומה המצלמה לא רואה</h4><ul>'
              '<li>בחלק הזה ימין ושמאל הם תמיד <strong>שלך</strong>, כשאתה עם הפנים לסל. ימין שלך הוא הצד הקרוב למצלמה, שמאל שלך הוא הצד הרחוק.</li>'
              '<li>המצלמה עומדת בצד, ולכן תזוזה שלך ימינה או שמאלה כמעט לא נראית בתמונה: שחקן אחד הוא בערך 17 פיקסלים. הזוויות והמרחקים לצדדים הם הערכה, לא מדידה.</li>'
              '</ul></div></div>')
    dv.append('<p class="callout">כאן כל דרייב נבדק שוב לבד, פריים אחרי פריים, עם שאלות על הצד, הזווית וההטעיות. לכן כשיש הבדל מול הסקירה הכללית שלמעלה (למשל כמה פעמים עברת את המגן, או לאיזה צד הלכת), המספר שכאן הוא המעודכן. אחר כך בודק שני צפה שוב בפריימים שמאחורי חמשת הממצאים הראשונים ושתי העדיפויות הראשונות, והסיכום כאן נכתב מחדש לפי התיקונים שלו.</p>')
    if c:
        dv.append('<div class="stats">' + stat("דרייבים", c.get("drives", len(drives))) +
                  stat("תקפת את הצד הפתוח", f'{c.get("open_side_taken", 0)} מתוך {c.get("open_side_taken", 0) + c.get("open_side_missed", 0)}', f'{c.get("side_unclear", 0)} לא ברורים', "pos" if c.get("open_side_taken", 0) >= c.get("open_side_missed", 0) else "neg") +
                  stat("זווית צמודה", c.get("tight", 0), f'קשת רחבה {c.get("wide", 0)} · בלי לפנות לסל {c.get("lateral", 0)} · ישר אל המגן {c.get("into_chest", 0)}') +
                  stat("עם hesitation לפני", c.get("with_hesitation", 0), f'הזיז את המגן: {c.get("hesitation_that_moved_defender", 0)}') +
                  stat("עברת את המגן בבירור", c.get("beat_defender", 0), (f'ועוד {c["beat_defender_half_step"]} בחצי צעד · ' if c.get("beat_defender_half_step") else "") + f'יד ימין {c.get("right_hand", 0)} · יד שמאל {c.get("left_hand", 0)}', "accent") + "</div>")
    if patterns.get("summary"):
        dv.append(f'<p>{esc(patterns["summary"])}</p>')
    if patterns.get("priorities"):
        dv.append("<h3>מה לעבוד עליו בדרייבים</h3>")
        for i, p in enumerate(patterns["priorities"], 1):
            pb = ""
            if "second_check" in p:
                lab, cls = {"confirmed": ("אומת בבדיקה שנייה", "confirmed"), "corrected": ("תוקן בבדיקה שנייה", "partly"), "not_checked": ("לא נבדק שוב", "not_visible")}.get(p["second_check"], (p["second_check"], "not_visible"))
                pb = f' <span class="verdict {cls}">{lab}</span>'
            pchg = f'<p class="why">מה השתנה בבדיקה השנייה: {esc(p["what_changed"])}</p>' if p.get("what_changed") else ""
            dv.append(f'<div class="fix"><div class="fix-n">{i}</div><div><h3 style="margin-top:0">{esc(p["what"])}{pb}</h3><p class="why">{esc(p["why"])}</p><div class="cue">משפט לעצמך: {esc(p["cue"])}</div>{pchg}<p class="why">התקפות {", ".join(str(x) for x in p["evidence_clips"])}</p></div></div>')
    if patterns.get("rule_check"):
        dv.append(f'<p class="callout"><strong>הכלל של היד המורמת, מול הדרייבים שלך:</strong> {esc(patterns["rule_check"])}</p>')
    if patterns.get("findings"):
        dv.append('<details class="more"><summary>כל הממצאים, עם הספירות והקליפים שמאחוריהם</summary><div class="more-body"><ul>')
        dv_by_index = {x.get("index"): x for x in drive_verdicts}
        CHK = {"confirmed": ("אומת בבדיקה שנייה", "confirmed"), "corrected": ("תוקן בבדיקה שנייה", "partly"), "not_checked": ("לא נבדק שוב", "not_visible")}
        for fi, f in enumerate(patterns["findings"]):
            if "second_check" in f:
                lab, cls = CHK.get(f["second_check"], (f["second_check"], "not_visible"))
                vb = f'<span class="verdict {cls}">{lab}</span>'
                chg = f'<div style="font-size:13px;color:var(--text-tertiary);margin-top:3px">מה השתנה בבדיקה השנייה: {esc(f["what_changed"])}</div>' if f.get("what_changed") else ""
            else:
                v = dv_by_index.get(fi) if fi < 5 else None
                vb = f'<span class="verdict {v["verdict"]}" title="{esc(v.get("evidence", ""))}">{VERDICT_HE.get(v["verdict"], v["verdict"])}</span>' if v else ""
                chg = ""
            dv.append(f'<li>{esc(f["finding"])} <span class="tag">{esc(f["numbers"])}</span> <span class="tag">התקפות {", ".join(str(x) for x in f["evidence_clips"])}</span> {vb}{chg}</li>')
        dv.append("</ul></div></details>")
    dv.append('<h3>דרייב אחרי דרייב</h3><p class="lead">בכל ציור: המסלול האמיתי שלך (כתום, מהמעקב האוטומטי), אתה (עיגול כתום) והמגן (עיגול כחול) ברגע ההחלטה, והצד שהיה פתוח (חץ ירוק). לידו הפריים של רגע ההחלטה.</p>')
    for d in sorted(drives, key=lambda d: d["clip"]):
        p = os.path.join(DRIVE_IMG, f"d{d['clip']:02d}.jpg")
        dia = f'<img src="{K.img_b64(p, max_w=880, quality=80)}" alt="">' if os.path.exists(p) else ""
        fr = frame_img(d["decision_reel"])
        da = d["defender_at_decision"]
        rl, rcls = RIGHT.get(d["right_decision"], (d["right_decision"], "mid"))
        best, took = d["side_open"], d["side_attacked"]
        side_ok = "pos" if best in (took, "either") else ("neg" if best in ("right", "left") else "")
        ang_ok = "pos" if d["angle"] == "tight_past_hip" else ("neg" if d["angle"] in ("wide_loop", "lateral", "into_chest") else "")
        hes_ok = "neg" if d["hesitation_moves"] >= 2 else ""
        out_ok = "pos" if d["outcome"] == "beat_defender" else ""
        chips = (f'<span class="tag {side_ok}">תקפת: {SIDE.get(took, took)}</span>'
                 f'<span class="tag">הגוף של המגן נתן: {SIDE.get(d.get("open_by_defender", ""), "—")}</span>'
                 f'<span class="tag">עזרה: {HELP.get(d.get("help_side", ""), "—")}</span>'
                 f'<span class="tag {side_ok}">הצד הטוב בסך הכל: {SIDE.get(best, best)}</span>'
                 f'<span class="tag {ang_ok}">זווית: {ANGLE.get(d["angle"], d["angle"])}</span>'
                 f'<span class="tag {hes_ok}">הטעיות לפני: {d["hesitation_moves"]}</span>'
                 f'<span class="tag {out_ok}">נגמר: {OUTCOME.get(d["outcome"], d["outcome"])}</span>')
        dv.append(f"""<div class="fix"><div class="fix-n" style="background:var(--navy)">{d["clip"]}</div><div>
<h4 style="margin-top:0">קליפ {d["clip"]} · {fmt(d["decision_reel"])} · {esc(d["start_spot"])} <span class="tag {rcls}">{rl}</span></h4>
<p style="margin:6px 0 10px">{chips}</p>
<div class="frames" style="grid-template-columns:repeat(auto-fit,minmax(300px,1fr))">
<div class="frame-card">{dia}<div class="frame-cap"><b>המסלול על המגרש</b>כתום: המסלול שלך מהמעקב האוטומטי. ירוק: הצד הטוב. עיגול כתום: אתה ברגע ההחלטה. עיגול כחול: המגן.</div></div>
<div class="frame-card">{f'<img src="{fr}" alt="">' if fr else ''}<div class="frame-cap"><b>רגע ההחלטה · {fmt(d["decision_reel"])}</b>{esc(d["teaching_frame"]["caption"])}</div></div>
</div>
<p><strong>מה היה עדיף.</strong> {esc(d["better_choice"])}</p>
{f'<p class="callout"><strong>הערת הבודק השני.</strong> {esc(DRIVE_NOTES[d["clip"]])}</p>' if d["clip"] in DRIVE_NOTES else ""}
<div class="cue">משפט לעצמך: {esc(d["cue"])}</div>
{video_row(["drive23"]) if d["clip"] == 23 else ""}
{sim_block(d["clip"])}
<details class="more"><summary>כל הפרטים של הדרייב הזה</summary><div class="more-body">
<table class="t">
<tr><th>המגן ({esc(d["defender"])})</th><td>{FEET.get(da["feet"], da["feet"])} · {HAND.get(da["hand_up"], da["hand_up"])} · {WEIGHT.get(da["weight"], da["weight"])} · {da["distance_m"]} שחקן ממך. {esc(da["note"])}</td></tr>
<tr><th>איפה עמדה העזרה</th><td><strong>{HELP.get(d.get("help_side", ""), d.get("help_side", "—"))}</strong>. {esc(d.get("help_note", ""))}</td></tr>
<tr><th>למה זה הצד הטוב</th><td>{esc(d["side_reason"])}</td></tr>
<tr><th>הזווית</th><td><strong>{ANGLE.get(d["angle"], d["angle"])}</strong>. {esc(d["angle_note"])}</td></tr>
<tr><th>הטעיות לפני הדרייב</th><td><strong>{d["hesitation_moves"]}</strong>. {esc(d["hesitation_note"])} {STEP.get(d["first_step"], "")}{", עם שינוי קצב" if d.get("pace_change") else ", בלי שינוי קצב"}.</td></tr>
<tr><th>איך זה נגמר</th><td><strong>{OUTCOME.get(d["outcome"], d["outcome"])}</strong>. {esc(d["outcome_note"])}</td></tr>
<tr><th>מה לא נראה טוב בסרטון</th><td>{esc(d["visibility"])} <span class="tag">ביטחון: {CONF.get(d["confidence"], d["confidence"])}</span></td></tr>
</table></div></details>
</div></div>""")
    dv.append("</section>")
    body.append("".join(dv))

# ----- strengths
pos_moments = [m for m in tm if m["kind"] == "positive"]
cands = {i: [m for c in s["evidence_clips"] for m in pos_moments if m["clip"] == c and (m["clip"], m["reel_time"]) not in used_moments] for i, s in enumerate(report["strengths"]) if i not in DROP("drop_strengths")}
demand = {}
for ms in cands.values():
    for m in ms:
        demand[(m["clip"], m["reel_time"])] = demand.get((m["clip"], m["reel_time"]), 0) + 1
strength_frame = {}
for i in sorted(cands, key=lambda i: len(cands[i])):
    free = [m for m in cands[i] if (m["clip"], m["reel_time"]) not in used_moments]
    if free:
        m = min(free, key=lambda m: demand[(m["clip"], m["reel_time"])]); strength_frame[i] = m; used_moments.add((m["clip"], m["reel_time"]))
st = ['<section class="card" id="strengths"><h2>מה כבר עובד</h2><p class="lead">את אלה לשמור. הם הבסיס שהתיקונים נבנים עליו.</p>']
for i, s in enumerate(report["strengths"]):
    if i in DROP("drop_strengths"):
        continue
    v = verdict_for("STRENGTH", base["strengths"][i]["title"])
    ev = [strength_frame[i]] if i in strength_frame else []
    st.append(f'<h3>{esc(s["title"])} {vbadge(v)}</h3><p>{esc(s["detail"])} <span class="tag">התקפות {", ".join(str(c) for c in s["evidence_clips"])}</span></p>{frames_block(ev) if ev else ""}')
st.append("</section>")
body.append("".join(st))

# ----- shots
sbs = sorted(report["shot_by_shot"], key=lambda s: s["reel_time"])
order = {c["id"]: c["n"] for c in chart}
VERD = {"keep": ("לשמור", "good"), "keep_but_improve": ("לשמור ולשפר", "mid"), "cut": ("להוריד", "bad")}
rows = []
keep = sum(1 for s in sbs if s["verdict"] == "keep"); cutn = sum(1 for s in sbs if s["verdict"] == "cut")
made_keep = sum(1 for s in sbs if s["verdict"] == "keep" and made_by_id.get(s["shot_id"]))
for s in sbs:
    vl, vc = VERD[s["verdict"]]
    rc = "good" if made_by_id.get(s["shot_id"]) else "bad"
    rows.append(f'<tr><td class="c num">{order.get(s["shot_id"], "")}</td><td class="num">{fmt(s["reel_time"])}</td><td>{esc(s["zone"])}</td><td>{esc(s["type"])}</td><td>{esc(s["contest"])}</td><td class="c num">{s.get("dribbles") if s.get("dribbles") is not None else ""}</td><td class="c {rc}">{esc(s["result"])}</td><td class="c num">{s["quality_1to5"]}</td><td class="c {vc}">{vl}</td><td>{esc(s["note"])}</td></tr>')
shot_img = K.img_b64(os.path.join(HERE, "shot_chart.jpg"), max_w=1400, quality=82)
body.append(f"""<section class="card" id="shots">
<h2>כל 13 הזריקות</h2>
<p class="lead">הנקודות הן המקום של הרגליים ברגע השחרור, על המגרש האמיתי בלי השחקנים. המספרים לפי הסדר במשחק. הטבלה מדרגת כל זריקה כמו שמאמן היה עושה: האם זו הייתה זריקה ששווה לקחת, עוד לפני שידעו אם נכנסה.</p>
<div class="viz"><img src="{shot_img}" alt="מפת זריקות"><div class="viz-cap">ירוק מלא = נכנסה, טבעת אדומה = החטאה. הקו הלבן הוא קו השלוש כמו שהוא מצויר במגרש הזה. זריקות מאותו מקום הוזזו מעט כדי שהמספרים יהיו קריאים.</div></div>
<div class="stats">
{stat("זריקות ששווה לקחת", keep, f"{made_keep} מהן נכנסו")}
{stat("לשמור ולשפר", len(sbs) - keep - cutn, "רעיון נכון, ביצוע לא")}
{stat("זריקות להוריד", cutn, "כאן מתחבאת היעילות", "neg")}
</div>
<table class="t"><tr><th>#</th><th>זמן בסרטון</th><th>מאיפה</th><th>סוג</th><th>הפרעה</th><th>כדרורים</th><th>תוצאה</th><th>איכות 1-5</th><th>החלטה</th><th>הערה</th></tr>{"".join(rows)}</table>
</section>""")

if "shots" in DROP("hide_sections"):
    body.pop()

# ----- tendencies + weaknesses
tnd = ['<section class="card" id="tendencies"><h2>נטיות, ומה הן עולות</h2><p class="lead">נספר מתוך 27 ההתקפות. בודק שני (סקפטי) צפה שוב בפריימים שמאחורי כל טענה; ההכרעה שלו מופיעה ליד כל אחת. "אומת חלקית" אומר ברוב המקרים שהוא הספיק לבדוק רק חלק מהקליפים או תיקן ספירה, לא שהטענה שגויה; התיקון שלו מופיע מתחת לכל חולשה.</p><div class="viz"><div class="viz-title">נטיות שנספרו</div><div class="bars">']
full_tend = []
for i, t in enumerate(report["tendencies"]):
    if i in DROP("drop_tendencies"):
        continue
    v = verdict_for("TENDENCY", base["tendencies"][i]["tendency"])
    m = re.search(r"(\d+)\s*(?:of|/|מתוך)\s*(\d+)", (t.get("numbers", "") or "") + " " + (base["tendencies"][i].get("numbers", "") or ""))
    pct = int(int(m.group(1)) / max(1, int(m.group(2))) * 100) if m else 0
    short = re.split(r"[.:;]", t["tendency"])[0].strip()
    if len(short) > 60:
        short = short[:60].rsplit(" ", 1)[0] + "…"
    nums = t.get("numbers", "") or ""
    first = re.split(r";", nums)[0].strip()
    tnd.append(f'<div class="bar-row"><div class="bar-name" title="{esc(t["tendency"])}">{esc(short)}</div><div class="bar-track"><div class="bar c2" style="width:{pct}%"></div></div><div class="bar-val num">{esc(first)} {vbadge(v)}</div></div>')
    full_tend.append(f'<li><strong>{esc(t["tendency"])}</strong> <span class="tag">{esc(nums)}</span> <span class="tag">התקפות {", ".join(str(c) for c in t["evidence_clips"])}</span> {vbadge(v)}</li>')
tnd.append('</div><div class="viz-cap">אורך הפס הוא הספירה הראשונה בכל נטייה; כל הספירות ברשימה למטה. ריחוף על ההכרעה מראה מה הבודק ראה.</div></div>')
tnd.append(f'<details class="more"><summary>הנטיות במלואן, עם כל הספירות</summary><div class="more-body"><ul>{"".join(full_tend)}</ul></div></details>')
tnd.append("<h3>חולשות, וכמה פעמים הן הופיעו</h3>")
for i, w in enumerate(report["weaknesses"]):
    if i in DROP("drop_weaknesses"):
        continue
    v = verdict_for("WEAKNESS", base["weaknesses"][i]["title"])
    tnd.append(f'<h4>{esc(w["title"])} {vbadge(v)}</h4><p>{esc(w["detail"])} <span class="tag warn">{esc(w["how_often"])}</span> <span class="tag">התקפות {", ".join(str(c) for c in w["evidence_clips"])}</span></p>')
    if v and v["verdict"] in ("partly", "refuted") and correction_text(v):
        tnd.append(f'<div class="callout"><strong>תיקון של הבודק השני.</strong> {long_text(correction_text(v), 420, "לקרוא את התיקון המלא")}</div>')
tnd.append("</section>")
body.append("".join(tnd))

# ----- teaching moments
body.append(f"""<section class="card" id="moments">
<h2>רגעי לימוד</h2>
<p class="lead">הפריימים שמאמן היה עוצר עליהם, עם המשפט שהיה אומר. אלה גם הקליפים המלווים שבתיקייה clips.</p>
{frames_block(sorted(tm, key=lambda m: m["reel_time"]))}
</section>""")

# ----- drills by mode
MODE = {"solo": "לבד", "partner": "עם פרטנר", "game": "בתוך משחק"}
dr = ['<section class="card" id="drills"><h2>תרגילים לפי התיקונים</h2><p class="lead">תרגילים לתיקונים ולחדירות לסל, מחולקים לפי מה שיש לך באותו יום: לבד, עם פרטנר, או כלל לעצמך בתוך משחק.</p>']
modes = drills.get("modes", {})
for mode in ("solo", "partner", "game"):
    items = [(f["rank"], d) for f in drills["fixes"] for d in f["drills"] if d.get("mode", "solo") == mode and f["rank"] not in DROP("drop_fix_ranks")]
    if not items:
        continue
    dr.append(f'<h3>{MODE[mode]}</h3><p class="why">{esc(modes.get(mode, ""))}</p><table class="t"><tr><th>בשביל</th><th>תרגיל</th><th>איך</th><th>חזרות / יעד</th><th>משפט לעצמך</th><th>מקור</th></tr>')
    for rank, d in items:
        src = f'<a href="{esc(d.get("url", ""))}" target="_blank">{esc(d.get("source", ""))}</a>' if d.get("url") else esc(d.get("source", ""))
        dr.append(f'<tr><td class="c num">{esc(FIXNUM.get(rank, rank))}</td><td><strong>{esc(d["name"])}</strong></td><td>{esc(d["how"])}</td><td>{esc(d.get("reps", ""))}</td><td>{esc(d.get("cue", ""))}</td><td>{src}</td></tr>')
    dr.append("</table>")
if drills.get("game_rules"):
    dr.append('<h3>כללים לעצמך בתוך משחק</h3><ul>' + "".join(f"<li>{esc(x)}</li>" for i_, x in enumerate(drills["game_rules"]) if i_ not in DROP("drop_game_rules")) + "</ul>")
_sess0 = len(dr)
dr.append('<div class="two"><div><h3>אימון לבד, 25 דקות</h3><table class="t"><tr><th>דקות</th><th>מה</th></tr>')
for s in drills["session"]:
    dr.append(f'<tr><td class="num">{esc(s["min"])}</td><td>{esc(s["what"])}</td></tr>')
dr.append("</table></div>")
if drills.get("partner_session"):
    dr.append('<div><h3>כשמצאת פרטנר, 25 דקות</h3><table class="t"><tr><th>דקות</th><th>מה</th></tr>')
    for s in drills["partner_session"]:
        dr.append(f'<tr><td class="num">{esc(s["min"])}</td><td>{esc(s["what"])}</td></tr>')
    dr.append("</table></div>")
dr.append("</div>")
if SCOPE.get("hide_sessions"):
    del dr[_sess0:]
if drills.get("notes") and not SCOPE.get("hide_sessions"):
    dr.append(f'<p class="callout">{esc(drills["notes"])}</p>')
dr.append("</section>")
body.append("".join(dr))

# ----- targets
body.append(f"""<section class="card" id="targets">
<h2>יעדים למשחק הבא</h2>
<table class="t"><tr><th>מדד</th><th>במשחק הזה</th><th>יעד</th></tr>
{"".join(f'<tr><td>{esc(t["metric"])}</td><td class="num">{esc(t["this_game"])}</td><td class="num"><strong>{esc(t["target"])}</strong></td></tr>' for i_, t in enumerate(report["next_game_targets"]) if i_ not in DROP("drop_targets"))}
</table></section>""")

DRIVE_BY_CLIP = {d["clip"]: d for d in drives}
LOG_OVERRIDES = load("log_overrides.json") or {}
# ----- possession log
DEC = {"good": ("טובה", "good"), "acceptable": ("סבירה", "mid"), "questionable": ("מפוקפקת", "bad"), "poor": ("גרועה", "bad"), "n/a": ("—", "")}
EXE = {"good": ("טוב", "good"), "acceptable": ("סביר", "mid"), "poor": ("גרוע", "bad"), "n/a": ("—", "")}
rows = []
for c in clips:
    r = records.get(c["i"]); h = log_he.get(c["i"], {})
    if not r:
        continue
    dl, dc = DEC[r["decision_quality"]]; xl, xc = EXE[r["execution_quality"]]
    narr = h.get("narrative_he") or r["narrative"]
    dr_rec = DRIVE_BY_CLIP.get(c["i"])
    if dr_rec:
        for a_, b_ in LOG_OVERRIDES.get(str(c["i"]), []):
            narr = narr.replace(a_, b_)
    drive_tag = f' <span class="tag">דרייב: תקפת {SIDE.get(dr_rec["side_attacked"], dr_rec["side_attacked"])} · הפרטים בחלק הדרייבים</span>' if dr_rec else ""
    rows.append(f'<tr><td class="c num">{c["i"]}</td><td class="num">{fmt(c["reel_start"])}</td><td>{esc(h.get("play_start_he") or r["play_start"].replace("_", " "))}</td><td>{esc(narr)}{drive_tag}</td><td class="c {dc}">{dl}</td><td class="c {xc}">{xl}</td><td>{esc(h.get("cue_he") or r["improvement_cue"])}</td></tr>')
body.append(f"""<section class="card" id="possessions">
<h2>התקפה אחרי התקפה</h2>
<p class="lead">כל 27 ההתקפות בסרטון, לפי הסדר. הזמן הוא המקום לגלול אליו בסרטון ההתקפה.</p>
<p class="callout">ביומן הזה "ימינה" ו"שמאלה" לא תמיד מנקודת המבט שלך: המצלמה מהצד מבלבלת, והבודקים הראשונים לא תמיד הפרידו. הכיוון המדויק של כל דרייב נמצא בחלק "דרייבים", ושם ימין ושמאל הם תמיד שלך.</p>
<details class="more"><summary>לפתוח את היומן המלא (27 התקפות)</summary><div class="more-body">
<table class="t"><tr><th>#</th><th>זמן</th><th>מתחיל ב</th><th>מה קרה</th><th>החלטה</th><th>ביצוע</th><th>משפט לעצמך</th></tr>{"".join(rows)}</table>
</div></details></section>""")

# ----- glossary
if glossary:
    body.append('<section class="card" id="glossary"><h2>מילון מונחים</h2><p class="lead">המונחים שמופיעים בסקירה, בשפה פשוטה.</p><div class="two"><div><table class="t"><tr><th>מונח</th><th>מה זה אומר</th></tr>' +
                "".join(f'<tr><td><strong>{esc(g["term"])}</strong></td><td>{esc(g["meaning"])}</td></tr>' for g in glossary[: (len(glossary) + 1) // 2]) +
                '</table></div><div><table class="t"><tr><th>מונח</th><th>מה זה אומר</th></tr>' +
                "".join(f'<tr><td><strong>{esc(g["term"])}</strong></td><td>{esc(g["meaning"])}</td></tr>' for g in glossary[(len(glossary) + 1) // 2:]) +
                "</table></div></div></section>")

# ----- method
tally_txt = ", ".join(f"{VERDICT_HE.get(k, k)} {v}" for k, v in sorted(tally.items()))
body.append(f"""<section class="card" id="method">
<h2>איך זה נוצר, ומה אי אפשר לראות</h2>
<div class="two"><div>
<h3>השיטה</h3>
<ul>
<li>סרטון ההתקפה (5:16, 27 התקפות) פורק ל-10 פריימים בשנייה. לכל התקפה נבנו גיליונות רחבים של המגרש (2 פריימים בשנייה), גיליונות מקורבים שעוקבים אחריך (5 בשנייה), ורצועות של 10 פריימים בשנייה סביב כל שחרור כדור.</li>
<li>בודק אחד (סוכן AI) לכל התקפה קרא את כל הגיליונות ומילא טופס קבוע: מה קרה, החלטה, ביצוע, טכניקה, אפשרות טובה יותר, משפט לעצמך. הערות המעקב האוטומטי אחרי הכדור ניתנו כנקודת פתיחה ונבדקו מול הפריימים.</li>
<li>שלושה מעברי סינתזה (בחירת זריקות, טכניקה, משחק בלי כדור) חיפשו דפוסים; מעבר של "מאמן ראשי" כתב את הדוח. לדרייבים נעשה מעבר נפרד: בודק לכל דרייב, סיכום דפוסים ובדיקה סקפטית.</li>
<li>בודק סקפטי צפה שוב בפריימים שמאחורי כל חוזקה, חולשה, נטייה ותיקון. סיכום ההכרעות: {esc(tally_txt)}. "אומת חלקית" ברוב המקרים אומר שהבודק הצליח לבדוק רק חלק מהקליפים, לא שהטענה שגויה.</li>
<li>הניסוח בעברית פשוטה נעשה במעבר נפרד, ובודק נוסף וידא שאף מספר, שם או טענה לא השתנו.</li>
</ul></div><div>
<h3>מגבלות של מצלמה רחבה אחת</h3>
<ul>
<li>השחקנים בגובה 100-160 פיקסלים. תנועות של כף היד והאצבעות (האגודל של יד שמאל, סיבוב פרק כף היד) לא ניתנות לקריאה; שחרור ביד אחת מול שתיים, קפיצה, איזון, סחיפה הצידה, קשת וצעדים כן.</li>
<li>העצם הכהה בפינה השמאלית העליונה מסתיר את נקודת הצ'ק בכמה התקפות; זמני ההחזקה שם הם הערכות.</li>
<li>13 זריקות הן מדגם קטן. ציוני האיכות של הזריקות חשובים יותר מהאחוזים.</li>
</ul></div></div>
<p class="foot">תיקייה: analysis_2026-10-07 (sheets/, briefs/, results/, clips/). סרטון המקור: recap_2026-10-07/output/Barak_Offense_Reel_master.mp4. גרסה באנגלית: Barak_Offense_Review_2026-10-07_en.html.</p>
</section>""")

nav = [("top", "סיכום"), ("stats", "השורה"), ("track", "ממשחק למשחק"), ("fixes", "תיקונים"), ("clips", "קליפים")] + ([("drives", "דרייבים")] if drives else []) + \
      [("strengths", "מה עובד"), ("shots", "זריקות"), ("tendencies", "נטיות"), ("moments", "רגעי לימוד"), ("drills", "תרגילים"), ("targets", "יעדים"), ("possessions", "יומן")] + \
      ([("glossary", "מילון")] if glossary else []) + [("method", "שיטה")]
nav = [n for n in nav if n[0] not in DROP("hide_sections")]
html = K.page("ברק · סקירת התקפה 07.10.2026", "משחק 07.10.2026 · סקירת סרטון ההתקפה", "סקירת התקפה: מה לשמור ומה לשנות",
              (SCOPE.get("hero_sub") or "<strong>12 נקודות מ-13 זריקות, 2 אסיסטים, 28 דקות.</strong> כל אחת מ-27 ההתקפות בסרטון נבדקה פריים אחרי פריים; כל טענה נבדקה שוב מול הפריימים על ידי בודק שני."),
              [("27 התקפות", False)] + ([] if "shots" in DROP("hide_sections") else [("13 זריקות", False)]) + [(f"{len(drives)} דרייבים" if drives else "3 משחקים", False), (f"{len(verdicts)} טענות נבדקו", True)], "\n".join(body), nav, lang="he", dir="rtl")
out = os.path.join(HERE, "Barak_Offense_Review_2026-10-07.html")
open(out, "w", encoding="utf-8").write(html)
print("wrote", out, f"{os.path.getsize(out)/1e6:.1f} MB", "| drives:", len(drives), "| glossary:", len(glossary), "| log_he:", len(log_he), "| plain fields:", sorted((load("report_plain.json") or {}).keys()))
