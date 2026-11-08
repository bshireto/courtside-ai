"""The short offense review (Hebrew, OKC colours): three parts and one closed drawer. Replaces build_report_he.py as the review
builder after Barak's clean-up decisions of 2026-10-12 (three parts only; every drive = a video, a few lines and the simulation;
all available numbers with trend graphs; drills also here, but closed).

  python build_review.py
Inputs: scope.json (the three instructions and their texts), work/drivevid/card_c*.json (one per drive, written with the videos),
        history.json (numbers per game), practice.json (drills), work/weavy/sims.json (panel for the pass instruction),
        clips/*.mp4 (phone-size videos; a video that is missing is simply not shown),
        clip_map.json (reel time range of every possession) and the phone-size reel (copied to clips/reel.mp4): every mention of
        a clip in the text ("קליפ 14 (2:43 בסרטון)") becomes a link that plays that moment in the video slot next to the text.
Output: ../review_2026-10-07/Barak_Offense_Review_2026-10-07.html (the videos it plays are in ../review_2026-10-07/clips)
"""
import glob, json, math, os, re, shutil
import htmlkit as K

HERE = os.path.dirname(os.path.abspath(__file__))
REVIEW_DIR = os.path.join(HERE, "..", "review_2026-10-07")      # the clean folder Barak opens: the review, the phone card, clips/
esc = K.esc
J = lambda *p: json.load(open(os.path.join(HERE, *p), encoding="utf-8"))
scope, history, practice = J("scope.json"), J("history.json"), J("practice.json")
sims = J("work", "weavy", "sims.json")
cards = sorted((json.load(open(p, encoding="utf-8")) for p in glob.glob(os.path.join(HERE, "work", "drivevid", "card_c*.json"))), key=lambda c: c["clip"])

# ------------------------------------------------------------------ clip mentions -> links that play in the slot next to the text
CLIPS = {c["i"]: (c["reel_start"], c["reel_end"]) for c in J("clip_map.json")}
REEL_SRC = os.path.join(HERE, "..", "recap_2026-10-07", "output", "Barak_Offense_Reel_phone.mp4")
REEL_DST = os.path.join(REVIEW_DIR, "clips", "reel.mp4")
if os.path.exists(REEL_SRC) and (not os.path.exists(REEL_DST) or os.path.getsize(REEL_DST) != os.path.getsize(REEL_SRC)):
    os.makedirs(os.path.dirname(REEL_DST), exist_ok=True); shutil.copyfile(REEL_SRC, REEL_DST)
HAS_REEL = os.path.exists(REEL_DST)
NOT_A_CARD_VIDEO = ("all_drives.mp4", "reel.mp4")
LINKS = {"made": 0, "unknown": [], "bad_time": []}
ONE = re.compile(r"קליפ (\d{1,2})(?: \((\d{1,2}):(\d{2})(?: בסרטון)?\))?")
MANY = re.compile(r"קליפים ((?:\d{1,2}(?:, | ו-| ו)?)+)")
SKIP_TAGS = {"a", "script", "style", "svg", "video", "button", "title"}


def clip_link(n, text, t=None):
    if not HAS_REEL:
        return text
    if n not in CLIPS:
        LINKS["unknown"].append(n); return text
    if t is not None and not (CLIPS[n][0] - 1 <= t <= CLIPS[n][1] + 1):
        LINKS["bad_time"].append((n, t)); t = None
    LINKS["made"] += 1
    return f'<a class="cl" href="#" data-clip="{n}"{"" if t is None else f" data-t={t}"} title="לנגן את הקליפ">{text}</a>'


def link_text(txt):
    txt = MANY.sub(lambda m: "קליפים " + re.sub(r"\d{1,2}", lambda d: clip_link(int(d.group(0)), d.group(0)), m.group(1)), txt)
    return ONE.sub(lambda m: clip_link(int(m.group(1)), m.group(0), None if m.group(2) is None else int(m.group(2)) * 60 + int(m.group(3))), txt)


def linkify(html):
    """Link every clip mention in the text of the page. Text inside links, scripts, charts and the caption under a video is left alone."""
    out, skip, in_cap = [], 0, False
    for tok in re.split(r"(<[^>]+>)", html):
        if tok.startswith("<"):
            m = re.match(r"<(/?)([a-zA-Z0-9]+)", tok)
            if m and m.group(2).lower() in SKIP_TAGS and not tok.endswith("/>"):
                skip += -1 if m.group(1) else 1
            elif "vcap" in tok and not tok.startswith("</"):
                in_cap = True
            elif tok.startswith("</div") and in_cap:
                in_cap = False
            out.append(tok)
        else:
            out.append(tok if (skip > 0 or in_cap or "קליפ" not in tok) else link_text(tok))
    return "".join(out)


SLOTBAR = ('<div class="slotbar" hidden><span class="now"></span><span class="sbtns">'
           '<button type="button" class="sb" data-act="again">מההתחלה</button>'
           '<button type="button" class="sb" data-act="slow">חצי מהירות</button>'
           '<button type="button" class="sb" data-act="back">חזרה לסרטון הניתוח</button></span></div>')

CSS = """
<style>
.dcard{border:1px solid var(--border-default);border-radius:var(--r-2);padding:18px 20px;margin-bottom:16px;background:var(--surface-page)}
.dcard h3{font-size:18px;margin:0 0 12px;line-height:1.4}
.dcard .tm{display:inline-block;background:var(--navy);color:#fff;border-radius:var(--r-1);padding:1px 9px;font-size:14px;margin-left:8px;direction:ltr;font-variant-numeric:tabular-nums}
.dgrid{display:grid;grid-template-columns:minmax(0,1.2fr) minmax(0,1fr);gap:20px;align-items:start}
@media (max-width:820px){.dgrid{grid-template-columns:1fr}}
video.v{width:100%;height:auto;border-radius:var(--r-2);background:#000;display:block}
.vcap{font-size:13px;color:var(--text-tertiary);margin-top:5px}
.ln{margin:0 0 11px;font-size:16px;line-height:1.6}
.ln b{display:block;font-size:12.5px;font-weight:700;color:var(--thunder);margin-bottom:1px}
.cuebox{display:inline-block;background:#FFF4D6;border:1px solid #FDDC8A;color:#5A3E00;border-radius:var(--r-1);padding:7px 13px;font-weight:600;margin:4px 0 2px;font-size:16px}
.slotcol{position:sticky;top:calc(var(--tb,48px) + 10px);align-self:start;z-index:4}
@media (max-width:820px){.slotcol{background:var(--surface-page);padding:6px 0 8px;box-shadow:0 8px 10px -9px rgba(0,0,0,.4)}}
a.cl{color:var(--thunder);font-weight:600;text-decoration:underline dotted;text-underline-offset:3px;cursor:pointer;white-space:nowrap;border-radius:var(--r-1);padding:0 3px}
a.cl::before{content:"";display:inline-block;width:0;height:0;border-style:solid;border-width:5px 0 5px 8px;border-color:transparent transparent transparent currentColor;margin-inline-end:5px;vertical-align:middle;position:relative;top:-1px}
a.cl:hover{background:#E6F3FA}
a.cl.on{background:var(--thunder);color:#fff;text-decoration:none}
.slotbar{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:6px 10px;background:var(--navy);color:#fff;border-radius:var(--r-2) var(--r-2) 0 0;padding:7px 10px;font-size:13.5px;font-weight:600}
.slotbar[hidden]{display:none}
.slotbar:not([hidden]) + video.v{border-radius:0 0 var(--r-2) var(--r-2)}
.sbtns{display:flex;flex-wrap:wrap;gap:6px}
.sb{font:inherit;font-size:12.5px;font-weight:600;border:1px solid rgba(255,255,255,.45);background:transparent;color:#fff;border-radius:var(--r-1);padding:3px 9px;cursor:pointer}
.sb:hover{background:rgba(255,255,255,.16)}
.sb.on{background:var(--sun);border-color:var(--sun);color:#3A2A00}
#floatslot{position:fixed;inset-inline-start:16px;bottom:16px;width:min(440px,calc(100vw - 32px));z-index:60;background:#000;border-radius:var(--r-2);box-shadow:0 10px 30px rgba(0,0,0,.4)}
#floatslot[hidden]{display:none}
#floatslot video.v{border-radius:0}
#floatslot .vcap{color:#D5DEEA;padding:5px 10px 8px;margin:0}
.simp{margin-top:14px}
.simp img{width:100%;height:auto;border-radius:var(--r-1);display:block}
.simp .cap{font-size:13px;color:var(--text-tertiary);margin-top:5px}
.tks{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));margin:12px 0 18px}
.tk{border:1px solid var(--border-default);border-radius:var(--r-2);padding:14px 16px;background:var(--surface-page)}
.tk.big{border-color:#B9DDF0;background:#F7FBFE}
.tk-n{display:inline-flex;width:22px;height:22px;border-radius:var(--r-pill);background:var(--sunset);color:#fff;font-size:12px;font-weight:700;align-items:center;justify-content:center;margin-inline-end:6px}
.tk-name{font-size:15px;font-weight:600;line-height:1.4}
.tk-val{font-size:30px;font-weight:700;line-height:1.2;margin-top:8px}
.tk-val{display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 12px}
.tk-cnt{font-size:17px;font-weight:600;color:var(--text-secondary)}
.hv small,td.num small{font-weight:400;font-size:12.5px;color:var(--text-secondary)}
.tk-what{font-size:14px;line-height:1.5;color:var(--text-secondary);margin-top:2px}
.units{display:flex;flex-wrap:wrap;gap:4px;margin:10px 0 8px}
.u{width:13px;height:13px;border-radius:var(--r-pill);border:1.5px solid #B5C0CE;background:#fff;box-sizing:border-box}
.u.on{background:var(--thunder);border-color:var(--thunder)}
.u.on.over{background:var(--sunset);border-color:var(--sunset)}
.u.need{border:1.5px dashed #007C32;background:#EAF6EE}
.dir{display:inline-block;border-radius:var(--r-pill);font-size:12.5px;font-weight:700;padding:2px 10px;margin:2px 0 6px;background:var(--surface-well);color:var(--text-secondary)}
.tk-goal{font-size:14.5px;line-height:1.5;border-inline-start:3px solid var(--sunset);padding-inline-start:9px;margin:2px 0 4px}
.tk-goal.ok{border-color:#007C32}
.tk-hist{margin-top:12px;border-top:1px solid var(--border-default);padding-top:8px}
.tk-hh{font-size:12.5px;font-weight:700;color:var(--thunder);margin-bottom:4px}
.hr{display:grid;grid-template-columns:46px minmax(40px,1fr) auto;gap:8px;align-items:center;font-size:13.5px;min-height:24px}
.hd{color:var(--text-secondary)}
.hna{grid-column:2 / 4;color:var(--text-tertiary)}
.hbar{position:relative;height:12px;background:var(--surface-well);border-radius:var(--r-1)}
.hbar i{position:absolute;inset-block:0;inset-inline-start:0;background:var(--thunder);border-radius:var(--r-1)}
.hbar i.bad{background:var(--sunset)}
.hbar i.good{background:#007C32}
.hbar u{position:absolute;top:-4px;bottom:-4px;width:0;border-inline-start:2px dashed #007C32}
.hv{font-weight:700;white-space:nowrap}
.tk-note{font-size:12.5px;color:var(--text-tertiary);margin-top:6px}
.tk-note.up{color:#007C32;font-weight:600}
.tk-note.dn{color:var(--sunset);font-weight:600}
.key{display:flex;flex-wrap:wrap;gap:6px 18px;align-items:center;font-size:13.5px;color:var(--text-secondary);background:var(--surface-well);border-radius:var(--r-2);padding:9px 12px;margin:6px 0 14px}
.key span{display:inline-flex;align-items:center;gap:6px}
.key .hbar{display:inline-block;width:46px}
.grp td{background:var(--surface-well);font-weight:700;font-size:13px;color:var(--text-secondary)}
.mode{border:1px solid var(--border-default);border-radius:var(--r-2);padding:14px 16px;margin:12px 0;background:var(--surface-page)}
.mode h3{margin:0 0 4px}
.dr{border-top:1px solid var(--border-default);padding:11px 0}
.dr h4{margin:0 0 4px;font-size:16px}
.dr .for{display:inline-block;background:var(--surface-well);border-radius:var(--r-pill);font-size:11.5px;font-weight:700;color:var(--text-secondary);padding:1px 8px;margin-inline-start:6px}
.dr p{margin:0 0 4px;font-size:15.5px;line-height:1.55}
.dr .cnt{color:var(--text-secondary);font-size:14px}
</style>
"""


def video(name, cap=""):
    p = os.path.join(REVIEW_DIR, "clips", name)
    if not os.path.exists(p):
        return ""
    return (f'<div class="slot" data-src="clips/{name}" data-cap="{esc(cap)}">{SLOTBAR}'
            f'<video class="v" controls preload="metadata" playsinline src="clips/{name}#t=0.6"></video><div class="vcap">{esc(cap)}</div></div>')


def panel(path, cap=""):
    full = os.path.join(HERE, path) if path else ""
    if not path or not os.path.exists(full):
        return ""
    return f'<div class="simp"><img src="{K.img_b64(full, max_w=1500, quality=84)}" alt=""><div class="cap">{esc(cap)}</div></div>'


body = [CSS]
nvid = len([p for p in glob.glob(os.path.join(REVIEW_DIR, "clips", "*.mp4")) if os.path.basename(p) not in NOT_A_CARD_VIDEO])

# ------------------------------------------------------------------ part 1: what to do next game
T = scope["top"]
body.append(f'<section class="tldr" id="top"><h2>{esc(T["title"])}</h2>' +
            "".join(f'<div class="tldr-row"><div class="tldr-n">{i}</div><div class="tldr-q" style="font-size:18px">{esc(it["do"])}'
                    f'<small style="font-size:15px;margin-top:4px">{esc(it["why"])}</small></div></div>' for i, it in enumerate(T["items"], 1)) + "</section>")
FT = scope["fix_text"]
c14 = next((c for c in cards if c["clip"] == 14), None)
INSTR = [
    (1, FT["1"], video("fix1_decide.mp4", "הסרטון של ההוראה הזו: כמה זמן הכדור נשאר אצלך, ואיך זה נראה כשיוצאים מיד."), ""),
    (2, FT["3"], video("drive_c14.mp4", "קליפ 14 (2:43): שלושה מגנים סביבך, וחבר לקבוצה לבד למעלה."),
     panel((c14 or {}).get("sim_panel") or sims.get("fix3", {}).get("img", ""), "משמאל מה שקרה, מימין סימולציה של המסירה לחבר לקבוצה. זו המחשה, לא מדידה.")),
    (3, FT["drive"], video("drive_c23.mp4", "קליפ 23 (4:24): יצאת מיד ועברת את המגן. כל 13 החדירות נמצאות בחלק הבא."), ""),
]
td = ['<section class="card" id="todo"><h2>מה לעשות במשחק הבא</h2><p class="lead">שלושה דברים. לכל אחד: מה קרה במשחק, מה לעשות במקום, משפט קצר לומר לעצמך על המגרש, וסרטון. '
      'כשהטקסט משחקןר קליפ, לחיצה על השם שלו מנגנת את הרגע הזה בסרטון שליד הטקסט.</p>']
for n, ft, vid, pan in INSTR:
    td.append(f"""<div class="dcard"><h3><span class="tk-n">{n}</span>{esc(ft["title"])}</h3>
<div class="dgrid"><div class="slotcol">{vid}</div><div>
<p class="ln"><b>מה קרה</b>{esc(ft["happened"])}</p>
<p class="ln"><b>מה לעשות</b>{esc(ft["do"])}</p>
<p class="ln"><b>איך זה נראה כשזה נעשה נכון</b>{esc(ft["good"])}</p>
<div class="cuebox">משפט לעצמך: {esc(ft["cue"])}</div>
</div></div>{pan}</div>""")
td.append("</section>")
body.append("".join(td))

# ------------------------------------------------------------------ part 2: the drives
game = [g for g in history["games"] if g.get("kind") == "game"]
now = game[-1]["nums"]
exposed = sum(1 for c in cards if c.get("hand", {}).get("what_barak_did") == "exposed")
if len(cards) >= now["drives"]:
    now["hand"] = [exposed, len(cards)]
    json.dump(history, open(os.path.join(HERE, "history.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def stat(label, val, sub="", cls=""):
    return f'<div class="stat {cls}"><div class="stat-label">{label}</div><div class="stat-value num">{val}</div><div class="stat-sub">{sub}</div></div>'


dv = ['<section class="card" id="drives"><h2>החדירות לסל</h2>',
      f'<p class="lead">{now["drives"]} חדירות, לכל אחת סרטון של כדקה וחצי. קודם רואים את המהלך במהירות רגילה. אחר כך הוא חוזר בהילוך איטי, '
      'שנעצר בכל רגע חשוב עם סימונים על התמונה. הטקסט מופיע רק כשהתמונה עומדת, כך שקודם קוראים ואז צופים. בסוף: המהלך שוב במהירות רגילה, '
      'סימולציה של המהלך שהיה עדיף, ומשפט לעצמך.</p>',
      '<div class="stats">' + stat("חדירות לסל", now["drives"]) +
      stat("לצד הפנוי מהצעד הראשון", f'{now["free_side"][0]} מתוך {now["free_side"][1]}', "מתוך החדירות שבהן צד אחד היה פנוי יותר", "neg") +
      stat("עברת את המגן בבירור", f'{now["beat"][0]} מתוך {now["beat"][1]}', "תמיד כשיצאת מיד") +
      (stat("הכדור היה חשוף מול יד של מגן", f'{now["hand"][0]} מתוך {now["hand"][1]}', "המגן שלח יד, והגוף שלך לא היה ביניהם", "accent") if now.get("hand") else "") + "</div>",
      '<p class="callout">ימין ושמאל הם תמיד <strong>שלך</strong>, כשהפנים שלך לסל. המצלמה עומדת בצד המגרש: ימין שלך הוא הצד הקרוב למצלמה, שמאל שלך הוא הצד הרחוק. '
      'בגלל הזווית הזו המרחקים לצדדים הם הערכה. בסרטונים: ירוק הוא הדרך העדיפה או המקום הפנוי, אדום הוא מה שהשתבש, צהוב הוא הכדור.</p>',
      video("all_drives.mp4", "כל החדירות ברצף, אחת אחרי השנייה.")]
for c in cards:
    hand = f'<p class="ln"><b>היד של המגן</b>{esc(c["hand_he"])}</p>' if c.get("hand_he") else ""
    dv.append(f"""<div class="dcard" id="d{c["clip"]}"><h3><span class="tm">{esc(c["time"])}</span>{esc(c["title_he"])}</h3>
<div class="dgrid"><div class="slotcol">{video(f'drive_c{c["clip"]}.mp4')}</div><div>
<p class="ln"><b>מה קרה</b>{esc(c["happened_he"])}</p>
<p class="ln"><b>מה עדיף</b>{esc(c["better_he"])}</p>
{hand}
<div class="cuebox">משפט לעצמך: {esc(c["cue_he"])}</div>
</div></div>{panel(c.get("sim_panel"), "משמאל מה שקרה באמת, מימין סימולציה של המהלך העדיף. הדמות בסימולציה נוצרה במחשב: זו המחשה, לא מדידה.")}</div>""")
dv.append("</section>")
body.append("".join(dv))

# ------------------------------------------------------------------ part 3: am I improving
MET = [m for m in history["metrics"] if m.get("group") in ("todo", "drive", "more", "box")]


def shown(m, g):
    v = g.get("nums", {}).get(m["key"])
    if v is None:
        return "לא נבדק", None
    if m["kind"] == "ratio":
        return f"{v[0]} מתוך {v[1]}", (v[0] / v[1] * 100 if v[1] else 0)
    return str(v), float(v)


DIR = {"down": "כמה שפחות, יותר טוב", "up": "כמה שיותר, יותר טוב"}


def of_what(m):
    """The metric's explanation without its "less is better" sentence (the card shows the direction as a chip)."""
    e = m.get("explain") or ""
    for d in ("פחות זה יותר טוב.", "יותר זה יותר טוב."):
        e = e.replace(d, "")
    return e.strip()


def level(m, v):
    """One comparable number per game: the share for an "X of Y" metric, the count otherwise. Never shown, only compared."""
    if v is None:
        return None
    return (v[0] / v[1] * 100 if v[1] else 0.0) if m["kind"] == "ratio" else float(v)


def pct(m, v):
    """The percent of an "X of Y" number as text ("71%"). None for a plain count."""
    if v is None or m["kind"] != "ratio" or not v[1]:
        return None
    return f"{round(v[0] / v[1] * 100)}%"


def target_level(m):
    """The target on the same scale as level(): a percent for an "X of Y" metric (history.json "target_pct"), a count otherwise."""
    if m.get("target_pct") is not None:
        return float(m["target_pct"])
    t = m.get("target")
    return level(m, t) if t else None


def met(m, v):
    tl = target_level(m)
    if tl is None or v is None or m.get("better") not in DIR:
        return None
    return level(m, v) <= tl if m["better"] == "down" else level(m, v) >= tl


def units(m, v):
    """One circle per time it could have happened. Full = it happened; red = more than the target allows; dashed green = missing."""
    if m["kind"] != "ratio" or not v or not 0 < v[1] <= 40:
        return ""
    done, total = v
    tl = target_level(m); tgt = None        # how many of THIS game's times the target share allows (down) or asks for (up)
    if tl is not None and m.get("better") in DIR:
        tgt = math.floor(tl / 100 * total + 1e-9) if m["better"] == "down" else math.ceil(tl / 100 * total - 1e-9)
    out = []
    for i in range(total):
        cls = "u"
        if i < done:
            cls += " on over" if (m.get("better") == "down" and tgt is not None and i >= tgt) else " on"
        elif m.get("better") == "up" and tgt is not None and i < tgt:
            cls += " need"
        out.append(f'<i class="{cls}"></i>')
    return f'<div class="units" role="img" aria-label="{done} מתוך {total}">{"".join(out)}</div>'


def goal(m, v):
    """The target for the next game. For an "X of Y" metric it is a percent, because every game has a different number of chances."""
    tl = target_level(m)
    if tl is None or v is None or m.get("better") not in DIR:
        return ""
    ok = met(m, v)
    plain = f' ({esc(m["target_plain"])})' if m.get("target_plain") else ""
    now = pct(m, v) or shown(m, game[-1])[0]
    more = "עמדת ביעד. לשמור על זה." if ok else f"במשחק הזה: {now}."
    return f'<div class="tk-goal{" ok" if ok else ""}"><strong>היעד למשחק הבא: {esc(m["target_text"])}</strong>{plain}. {more}</div>'


def bars(m):
    """Game after game, oldest first: one bar per game, with the same words as the big number next to it."""
    vals = [(g, g.get("nums", {}).get(m["key"])) for g in game]
    top = 100.0 if m["kind"] == "ratio" else max([level(m, v) for _, v in vals if v is not None] + [1.0])
    tl = target_level(m); tick = ""
    if tl is not None and m.get("better") in DIR:
        tick = f'<u style="inset-inline-start:{min(100.0, tl / top * 100):.1f}%"></u>'
    out = []; n_measured = sum(1 for _, v in vals if v is not None)
    for g, v in vals:
        if v is None:
            out.append(f'<div class="hr"><span class="hd num">{esc(g["short"])}</span><span class="hna">לא נבדק</span></div>')
            continue
        ok = met(m, v); cls = "" if ok is None else ("good" if ok else "bad")
        if m["kind"] != "ratio" and n_measured < 2:        # a single count has nothing to be compared with: the number alone
            out.append(f'<div class="hr"><span class="hd num">{esc(g["short"])}</span><span class="hna" style="color:inherit;font-weight:700">{shown(m, g)[0]}</span></div>')
            continue
        out.append(f'<div class="hr"><span class="hd num">{esc(g["short"])}</span><span class="hbar"><i class="{cls}" style="width:{max(2.0, level(m, v) / top * 100):.1f}%"></i>{tick}</span>'
                   f'<span class="hv num">{both(m, g)}</span></div>')
    measured = [v for _, v in vals if v is not None]
    if len(measured) < 2 or m.get("better") not in DIR:      # first time counted: the section's opening lines already say so
        note = ""
    else:
        prev, cur = level(m, measured[-2]), level(m, measured[-1])
        if abs(cur - prev) < 1e-9:
            note = '<div class="tk-note">כמו במשחק הקודם.</div>'
        elif (cur > prev) == (m["better"] == "up"):
            note = '<div class="tk-note up">טוב יותר מהמשחק הקודם.</div>'
        else:
            note = '<div class="tk-note dn">פחות טוב מהמשחק הקודם.</div>'
    return f'<div class="tk-hist"><div class="tk-hh">משחק אחרי משחק</div>{"".join(out)}{note}</div>'


def both(m, g):
    """A game's number for a bar row or a table cell: the percent with the count in brackets, or the plain count."""
    v = g.get("nums", {}).get(m["key"]); pc = pct(m, v)
    return f'{pc} <small>({shown(m, g)[0]})</small>' if pc else shown(m, g)[0]


def tile(m, big=False):
    g = game[-1]; v = g.get("nums", {}).get(m["key"])
    badge = f'<span class="tk-n">{m["instruction"]}</span>' if m.get("instruction") else ""
    what = of_what(m)
    chip = f'<div><span class="dir">{DIR[m["better"]]}</span></div>' if m.get("better") in DIR else ""
    return (f'<div class="tk{" big" if big else ""}"><div class="tk-name">{badge}{esc(m["name"])}</div><div class="tk-val">{f"<span class=num dir=ltr>{pct(m, v)}</span><span class=tk-cnt dir=rtl>{shown(m, g)[0]}</span>" if pct(m, v) else f"<span class=num>{shown(m, g)[0]}</span>"}</div>'
            f'{f"<div class=tk-what>{esc(what)}</div>" if what else ""}{units(m, v)}{chip}{goal(m, v)}{bars(m)}</div>')


KEY = ('<div class="key"><span><i class="u on"></i>פעם שזה קרה</span><span><i class="u"></i>פעם שזה לא קרה</span>'
       '<span><i class="u on over"></i>יותר ממה שהיעד מרשה</span><span><i class="u need"></i>חסר כדי להגיע ליעד</span>'
       '<span><span class="hbar"><i style="width:60%"></i><u style="inset-inline-start:35%"></u></span>פס: באיזה אחוז מהפעמים זה קרה באותו משחק. הקו הירוק המקווקו: היעד</span></div>')


rows = []
for grp in history["groups"]:
    rows.append(f'<tr class="grp"><td colspan="{len(game) + 2}">{esc(grp["name"])}</td></tr>')
    for m in MET:
        if m["group"] != grp["key"]:
            continue
        cells = "".join(f'<td class="num">{both(m, g)}</td>' for g in game)
        rows.append(f'<tr><td>{esc(m["name"])}<div style="font-size:12.5px;color:var(--text-tertiary)">{esc(m.get("explain", ""))}</div></td>{cells}<td class="num"><strong>{esc(m.get("target_text") or "—")}</strong></td></tr>')
body.append(f"""<section class="card" id="track"><h2>האם השתפרתי</h2>
<p class="lead">אותם דברים נספרים אחרי כל משחק, כדי לראות אם שלוש ההוראות עובדות. בכל כרטיס יש, מלמעלה למטה: כמה פעמים זה קרה במשחק הזה ומתוך מה, לאיזה כיוון רוצים שהמספר יזוז, היעד למשחק הבא, ואותו מספר בכל משחק שנבדק.</p>
<p>האחוז והספירה הם אותו מספר בשתי צורות: 10 מתוך 14 הם 71%. היעדים למשחק הבא כתובים באחוזים, כי בכל משחק יש מספר אחר של התקפות וחדירות, ורק אחוז אפשר להשוות ממשחק למשחק.</p>
<p>כרגע יש שני משחקים, ורוב הדברים נספרו לראשונה במשחק הזה. ההשוואה בין משחקים תתחיל מהמשחק הבא.</p>
{KEY}
<h3>שלושת המספרים של ההוראות</h3>
<div class="tks">{"".join(tile(m, True) for m in MET if m["group"] == "todo")}</div>
<h3>כל המספרים, משחק אחרי משחק</h3>
<table class="t"><tr><th>מה נספר</th>{"".join(f"<th>{esc(g['label'])}</th>" for g in game)}<th>יעד למשחק הבא</th></tr>{"".join(rows)}</table>
<p class="viz-cap">"לא נבדק" = המשחק ההוא לא נותח לעומק הזה. בלוח התוצאות מופיעים מספרים בלבד; ניתוח הזריקות עצמו לא חלק מהסקירה.</p>
<h3>שאר המספרים, באותה צורה</h3>
<div class="tks">{"".join(tile(m) for m in MET if m["group"] != "todo" and m["key"] not in ("drives", "minutes"))}</div>
<h3>מה ייבדק בסקירה הבאה</h3>
<ul>{"".join(f"<li>{esc(x)}</li>" for x in game[-1].get("fixes_for_next_review", []))}</ul>
<p class="callout">בסקירה הבאה כל אחד מהדברים האלה מקבל סטטוס: השתפר, השתפר חלקית, או עדיין שם, עם הסרטונים שמראים את זה.</p>
</section>""")

# ------------------------------------------------------------------ closed drawer: drills
MODE = [("solo", "לבד"), ("partner", "עם פרטנר"), ("game", "בתוך משחק")]
dr = ['<section class="card" id="drills"><h2>תרגילים</h2><p class="lead">מה לתרגל עד המשחק הבא, לפי מה שיש לך באותו יום. אותו תוכן נמצא גם בכרטיס האימון לטלפון.</p>',
      '<p><a href="Barak_Session_Card_2026-10-07.html" target="_blank">לפתוח את כרטיס האימון לטלפון</a></p>',
      '<details class="more"><summary>לפתוח את התרגילים</summary><div class="more-body">']
for key, name in MODE:
    md = practice[key]
    dr.append(f'<div class="mode"><h3>{name}</h3><p class="why" style="color:var(--text-secondary)">{esc(md["sub"])}</p>')
    if md.get("plan"):
        dr.append('<table class="t"><tr><th>דקות</th><th>מה עושים</th></tr>' + "".join(f'<tr><td class="num" style="direction:ltr;text-align:end">{esc(s["min"])}</td><td>{esc(s["what"])}</td></tr>' for s in md["plan"]) + "</table>")
    if md.get("rules"):
        dr.append("<ol>" + "".join(f"<li>{esc(x)}</li>" for x in md["rules"]) + "</ol>")
    for d in md["drills"]:
        tag = f'<span class="for">{esc(practice["items"][d["for"]])}</span>' if d.get("for") else ""
        src = f' · <a href="{esc(d["url"])}" target="_blank">{esc(d["source"])}</a>' if d.get("url") else (f' · {esc(d["source"])}' if d.get("source") else "")
        dr.append(f'<div class="dr"><h4>{esc(d["name"])}{tag}</h4><p>{esc(d["how"])}</p><p class="cnt">{esc(d["count"])}{src}</p><div class="cuebox">{esc(d["cue"])}</div></div>')
    dr.append("</div>")
dr.append("</div></details></section>")
body.append("".join(dr))

body.append('<p class="foot" style="margin:8px 4px 40px">איך זה נעשה: סרטון ההתקפה שלך (5:16, 27 התקפות) נבדק תמונה אחרי תמונה, 10 תמונות בשנייה. כל חדירה נבדקה פעמיים, ובודק שני תיקן את הראשון. '
            'המצלמה אחת ורחבה, ולכן ידיים ומרחקים לצדדים נראים רק בערך; איפה שלא רואים, כתוב שלא רואים.</p>')

JS = """
<script>
(function(){
  var CLIPS = __CLIPS__, REEL = "clips/reel.mp4", BAR = __BAR__;
  function fmt(t){ t = Math.floor(t); return Math.floor(t / 60) + ":" + ("0" + (t % 60)).slice(-2); }
  function topbar(){ var tb = document.querySelector(".topbar"); if (tb) document.documentElement.style.setProperty("--tb", tb.offsetHeight + "px"); }
  topbar(); window.addEventListener("resize", topbar);
  function floatSlot(){
    var f = document.getElementById("floatslot");
    if (!f) {
      f = document.createElement("div"); f.id = "floatslot"; f.className = "slot";
      f.innerHTML = BAR + '<video class="v" controls playsinline></video><div class="vcap"></div>';
      document.body.appendChild(f); f.querySelector('[data-act="back"]').textContent = "סגירה";
    }
    f.hidden = false; return f;
  }
  function clearOn(){ document.querySelectorAll("a.cl.on").forEach(function(a){ a.classList.remove("on"); }); }
  function playClip(slot, n, t, link){
    var c = CLIPS[n]; if (!c) return;
    var v = slot.querySelector("video"), bar = slot.querySelector(".slotbar");
    var start = t == null ? c[0] : Math.max(c[0], t - 4);
    slot._clip = {start: start, end: c[1]};
    clearOn(); if (link) link.classList.add("on");
    bar.hidden = false;
    bar.querySelector(".now").textContent = "קליפ " + n + " · " + fmt(t == null ? c[0] : t) + " · מתוך הסרטון המלא";
    slot.querySelector(".vcap").textContent = t == null ? "ההתקפה כולה, במהירות רגילה." : "מתחיל כמה שניות לפני " + fmt(t) + " ונעצר בסוף ההתקפה.";
    function go(){ v.currentTime = start; v._end = c[1]; v.playbackRate = slot._slow ? 0.5 : 1; var p = v.play(); if (p && p.catch) p.catch(function(){}); }
    if (!v._hooked) { v._hooked = true; v.addEventListener("timeupdate", function(){ if (v._end != null && v.currentTime >= v._end) { v.pause(); v._end = null; } }); }
    if (v.getAttribute("data-reel") === "1" && v.readyState >= 1) go();
    else {
      v.setAttribute("data-reel", "1");
      v.addEventListener("loadedmetadata", function h(){ v.removeEventListener("loadedmetadata", h); go(); });
      v.src = REEL + "#t=" + start.toFixed(1); v.load();
    }
    var r = slot.getBoundingClientRect();
    if (r.top < 0 || r.bottom > window.innerHeight) slot.scrollIntoView({block: "nearest", behavior: "smooth"});
  }
  function restore(slot){
    var v = slot.querySelector("video"); v.pause(); v._end = null; v.playbackRate = 1; slot._slow = false; slot._clip = null;
    slot.querySelector(".slotbar").hidden = true; clearOn();
    slot.querySelectorAll(".sb.on").forEach(function(b){ b.classList.remove("on"); });
    if (slot.id === "floatslot") { slot.hidden = true; return; }
    v.removeAttribute("data-reel"); v.src = slot.getAttribute("data-src") + "#t=0.6"; v.load();
    slot.querySelector(".vcap").textContent = slot.getAttribute("data-cap") || "";
  }
  document.addEventListener("click", function(e){
    var a = e.target.closest ? e.target.closest("a.cl") : null;
    if (a) {
      e.preventDefault();
      var card = a.closest(".dcard"), slot = (card && card.querySelector(".slot")) || floatSlot();
      playClip(slot, a.getAttribute("data-clip"), a.hasAttribute("data-t") ? parseFloat(a.getAttribute("data-t")) : null, a);
      return;
    }
    var b = e.target.closest ? e.target.closest(".sb") : null; if (!b) return;
    var s = b.closest(".slot"), v = s.querySelector("video"), act = b.getAttribute("data-act");
    if (act === "back") restore(s);
    else if (act === "again" && s._clip) { v.currentTime = s._clip.start; v._end = s._clip.end; v.play(); }
    else if (act === "slow") { s._slow = !s._slow; v.playbackRate = s._slow ? 0.5 : 1; b.classList.toggle("on", s._slow); }
  });
  document.addEventListener("play", function(e){
    document.querySelectorAll("video").forEach(function(o){ if (o !== e.target && !o.paused) o.pause(); });
  }, true);
})();
</script>
"""
page_body = linkify("\n".join(body)) + JS.replace("__CLIPS__", json.dumps({str(k): list(v) for k, v in CLIPS.items()})).replace("__BAR__", json.dumps(SLOTBAR, ensure_ascii=False))

nav = [("top", "בקצרה"), ("todo", "מה לעשות"), ("drives", "החדירות"), ("track", "האם השתפרתי"), ("drills", "תרגילים")]
html = K.page("ברק · סקירת התקפה 07.10.2026", "משחק 07.10.2026 · סקירת התקפה", "שלושה דברים למשחק הבא",
              "27 ההתקפות ו-13 החדירות לסל שלך נבדקו תמונה אחרי תמונה. כאן נשאר רק מה שצריך כדי לשחק טוב יותר בשבוע הבא: מה לעשות, החדירות בסרטונים, והמספרים.",
              [("27 התקפות", False), (f"{now['drives']} חדירות לסל", False), (f"{nvid} סרטונים", True)], page_body, nav, lang="he", dir="rtl")
import sys
out = os.path.join(HERE, sys.argv[1]) if len(sys.argv) > 1 else os.path.join(REVIEW_DIR, "Barak_Offense_Review_2026-10-07.html")
open(out, "w", encoding="utf-8").write(html)
import re
text = re.sub(r"<[^>]+>", " ", re.sub(r'src="data:[^"]*"', "", re.sub(r"<style.*?</style>", " ", html, flags=re.S)))
print("wrote", out, f"{os.path.getsize(out) / 1e6:.1f} MB | drive cards {len(cards)} | videos found {nvid} | words {len(text.split())}")
print(f"clip links: {LINKS['made']}" + ("" if HAS_REEL else " | NO REEL: clips/reel.mp4 is missing, so clip mentions are plain text"))
if LINKS["unknown"]:
    print("WARNING, the text mentions clips that are not in clip_map.json:", sorted(set(LINKS["unknown"])))
if LINKS["bad_time"]:
    print("WARNING, a mentioned time is not inside that clip (clip, seconds):", LINKS["bad_time"])
