"""Build ../docs/offense-review-cleanup-decision-map.html: every output of the 07.10 offense review, and what to keep, merge or drop.

From the decision-map skill template, re-coloured with the OKC palette (this project is not Investing.com).
Inputs: work/qa/section_words.json (words per section of the review), ../docs/assets/cleanup/*.jpg (pictures made for the cards),
the file sizes on disk. Run after build_report_he.py.
"""
import glob, html, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(HERE, "..", "docs")
TEMPLATE = os.path.expanduser("~/.claude-personal/skills/decision-map/template.html")
if not os.path.exists(TEMPLATE):
    TEMPLATE = os.path.expanduser("~/.claude/skills/decision-map/template.html")
OUT = os.path.join(DOCS, "offense-review-cleanup-decision-map.html")
IMG = "assets/cleanup"
REVIEW = "../analysis_2026-10-07/Barak_Offense_Review_2026-10-07.html"
SAMPLE = "../analysis_2026-10-07/clips/phone/sample_drive_c15_new_format.mp4"


def esc(s):
    return html.escape("" if s is None else str(s), quote=False)


def mb(paths):
    return sum(os.path.getsize(p) for p in paths if os.path.exists(p)) / 1e6


def option(name, letter, title, what, bad, rec=False, tags=()):
    tg = "".join(f'<span class="tag {c}">{esc(t)}</span>' for t, c in tags)
    return f"""<label class="option{' recommended' if rec else ''}">
  <input type="radio" name="{name}" value="{letter} — {esc(title)}">
  <div>
    <div class="option-t">{letter} — {esc(title)}{' <span class="badge">Recommended</span>' if rec else ''}</div>
    <div class="option-d">{what}</div>
    <span class="downside"><b>What's bad:</b> {esc(bad)}</span>
    {f'<div class="option-meta">{tg}</div>' if tg else ''}
  </div>
</label>"""


def note(n, placeholder):
    return f'<div class="note"><label for="n{n}">Notes or changes for decision {n}</label><textarea id="n{n}" placeholder="{html.escape(placeholder, quote=True)}"></textarea></div>'


def card(n, title, ask, body, preview=None):
    cls = "card with-preview" if preview else "card"
    inner = f'<div class="card-body"><div>{body}</div>{preview}</div>' if preview else f'<div class="card-body">{body}</div>'
    return f"""<article class="{cls}" id="d{n}" data-decision="{n}">
  <div class="card-head"><div class="card-n">{n}</div><h2 class="card-title" data-title>{esc(title)}</h2></div>
  <div class="ask">{esc(ask)}</div>
  {inner}
</article>"""


def zoom(name, alt, style="display:block;width:100%;height:auto;border-radius:var(--r-1)"):
    """A picture that opens full-size on click. Inlined, so the map is one file that also opens on a phone."""
    import base64
    data = base64.b64encode(open(os.path.join(DOCS, IMG, name), "rb").read()).decode("ascii")
    return f'<img class="zoomable" src="data:image/jpeg;base64,{data}" alt="{esc(alt)}" style="{style}">'


def he(text, style=""):
    return f'<div class="he" style="{style}">{text}</div>'


cards, tldr = [], []

# ================================================================== D1 the line for "shot analysis"
d1_body = f"""<p class="narrative">You said no shot analysis from game footage. I removed everything that judges the shot itself. I kept the advice about what you do with the ball before a shot, even where the right move is "shoot now", because that is a decision and not shooting technique.</p>
<div class="viz"><div class="viz-title">What left the review today, and what stayed</div>
<div class="ba">
  <div class="ba-panel"><div class="ba-tag">Removed</div>
    <ul style="margin:0;padding-inline-start:18px;font-size:14.5px;line-height:1.6">
      <li>The list and the map of all 13 shots, with a grade for each</li>
      <li>Shooting numbers: makes, misses, percentages, points per shot</li>
      <li>The follow-up on your shooting technique from July</li>
      <li>The fix "one step back makes it a three"</li>
      <li>Four clips about shots (quick shot, step back, same spot twice, runner)</li>
      <li>Shot findings inside strengths, habits, targets and drills</li>
    </ul></div>
  <div class="ba-arrow">&rarr;</div>
  <div class="ba-panel after"><div class="ba-tag">Kept</div>
    <ul style="margin:0;padding-inline-start:18px;font-size:14.5px;line-height:1.6">
      <li>Holding the ball instead of deciding (10 of 14 times)</li>
      <li>"He is far and his hands are down: shoot now. He is close: go past him."</li>
      <li>Passing to the teammate left alone</li>
      <li>All 13 drives, including how each one ended</li>
    </ul></div>
</div>
<div class="viz-cap">The review went from 15 sections to 13 and lost one of its three fixes. Open it to see the result.</div></div>
<div class="label">Where This Lives</div>
<div class="where"><b>analysis_2026-10-07/scope.json</b> — the list of what the review shows; change it and rebuild<br><b><a href="{REVIEW}" target="_blank">Barak_Offense_Review_2026-10-07.html</a></b> — the review as it is now</div>
<div class="label">Pick One</div>
<div class="options">
{option('d1', 'A', 'Keep the line where it is now', 'The shots themselves are gone. "Decide within a second: shoot or go past him" stays as an instruction.', 'The word "shoot" still appears in the first instruction.', rec=True, tags=[('already applied', 'pos')])}
{option('d1', 'B', 'Cut deeper: no advice that ends in a shot', 'The first instruction becomes "do not hold the ball: go past him or pass". Nothing in the review tells you to shoot.', 'When the defender stands far with his hands down, the review will not say that the open shot is the right choice.')}
{option('d1', 'C', 'Bring back one line of numbers, with no analysis', 'Points, makes and attempts on a single line at the top. No grades, no shot list.', 'One more thing on a page that already has too many.')}
</div>
{note(1, 'e.g. A, but bring back the runner clip')}"""
cards.append(card(1, "Where the line for 'no shot analysis' sits", "Did I cut the right things when I removed the shot analysis?", d1_body))
tldr.append(("Where the line for 'no shot analysis' sits", "A", "Keep it as it is now"))

# ================================================================== D2 opening lines (creative: gallery)
OPEN = [
    ("A", "One instruction", "הדבר הכי חשוב למשחק הבא: כשאתה מקבל את הכדור, תחליט תוך שנייה מה אתה עושה איתו. אל תחזיק אותו ואל תכדרר במקום.",
     "The pass and the drive items drop below the opening."),
    ("B", "What happened, then what to do", "<b>מה קרה:</b> ב-10 מתוך 14 פעמים קיבלת את הכדור והחזקת אותו 4 שניות. בזמן הזה המגן הספיק לעמוד מולך.<br><b>מה לעשות:</b> להחליט תוך שנייה.",
     "Longer, and covers one topic only."),
    ("C", "Three numbered instructions", "1. קיבלת את הכדור? תחליט תוך שנייה מה אתה עושה איתו.<br>2. מגן נוסף בא אליך? תמסור מיד לחבר שנשאר לבד.<br>3. חודר לסל? לך לצד שיש בו פחות מגנים, ובקו ישר לסל.",
     "Three things at once, with no single priority."),
    ("D", "Three numbers", "הכדור נשאר אצלך 4 שניות: 10 מתוך 14<br>חבר פנוי שלא קיבל את הכדור: 9 התקפות<br>חדירה לצד הפנוי מהצעד הראשון: 3 מתוך 10",
     "Tells you the score, not what to do."),
    ("E", "What worked first", "<b>מה עבד:</b> כשיצאת מיד, עברת את המגן.<br><b>מה לא עבד:</b> כשחיכית עם הכדור, הוא הספיק לעמוד מולך.<br><b>במשחק הבא:</b> לצאת מיד.",
     "Says nothing about passing."),
    ("F", "A question to ask yourself", "שאלה אחת לפני שהכדור מגיע אליך: מה אני עושה איתו ברגע שהוא אצלי? זורק, עובר את המגן, או מוסר.",
     "A question is easy to forget in a game, and it carries no numbers."),
]
gopts = []
for letter, name, body, bad in OPEN:
    rec = letter == "C"
    gopts.append(f"""<div class="gopt{' recommended' if rec else ''}">
  <label class="gopt-pick"><input type="radio" name="d2" value="{letter} — {esc(name)}"><span class="gopt-letter">{letter}</span><span class="gopt-name">{esc(name)}</span>{' <span class="badge">Recommended</span>' if rec else ''}</label>
  <div class="gopt-body he" style="font-size:15.5px;line-height:1.6">{body}</div>
  <span class="downside"><b>What's bad:</b> {esc(bad)}</span>
  <label class="gopt-also"><input type="checkbox" data-shortlist="d2" value="{letter}"> Also use this</label>
</div>""")
d2_body = f"""<p class="narrative">The old opening was a clever line you had to decode. The rule from now on: say what happened in plain words, then what to do, with no codes and no coaching terms. Here are six ways to open the review, each written out in full. The page uses C today.</p>
<div class="viz"><div class="viz-title">The line you could not understand, and what replaced it</div>
<div class="ba">
  <div class="ba-panel"><div class="ba-tag">Before</div>{he("הזריקה שלך בסדר; השנייה שלפניה לא: 5 מתוך 6 כשזרקת ישר מתוך תנועה או מיד אחרי קבלת הכדור עם מרחב סביבך, 0 מתוך 7 אחרי שהחזקת את הכדור…", "font-size:15px;line-height:1.55")}
    <span class="downside"><b>What's bad:</b> a riddle, then one 60-word sentence.</span></div>
  <div class="ba-arrow">&rarr;</div>
  <div class="ba-panel after"><div class="ba-tag">Now</div>{he("קיבלת את הכדור? תחליט תוך שנייה מה אתה עושה איתו. אל תחזיק אותו ואל תכדרר במקום.", "font-size:15px;line-height:1.55")}
    <span class="downside"><b>Rule:</b> what to do first, the number behind it second.</span></div>
</div></div>
<div class="label">Pick One — 6 Openings, Written In Full</div>
<div class="gallery">
{''.join(gopts)}
</div>
<p class="gallery-hint">Pick the opening. Tick "Also use this" on another one if you want both, for example C at the top and D next to it.</p>
{note(2, 'e.g. C, but shorter sentences. Or paste a sentence from the review that is still unclear.')}"""
cards.append(card(2, "The opening lines of the review", "Which opening tells you most clearly what to do next game?", d2_body))
tldr.append(("The opening lines of the review", "C", "Three numbered instructions"))

# ================================================================== D3 what stays on the page
words = json.load(open(os.path.join(HERE, "work", "qa", "section_words.json"), encoding="utf-8"))["now"]
NAMES = {"top": ("Short version", "keep"), "track": ("Game to game", "keep"), "fixes": ("The two fixes", "keep"), "clips": ("Clips", "merge"),
         "drives": ("Drives", "shorten"), "strengths": ("What already works", "drop"), "tendencies": ("Habits and weaknesses", "drop"),
         "moments": ("Teaching moments", "drop"), "drills": ("Drills", "move"), "targets": ("Targets", "merge"),
         "possessions": ("All 27 possessions", "drop"), "glossary": ("Word list", "drop"), "method": ("How it was made", "drop")}
TAG = {"keep": ("stays", "pos", ""), "shorten": ("stays, much shorter", "pos", "c2"), "merge": ("merged into another part", "", "c3"),
       "move": ("moves to the phone card", "", "c3"), "drop": ("leaves the page", "", "c4")}
total = sum(w[2] for w in words); mx = max(w[2] for w in words)
bars = []
for sid, _, n, _, _ in words:
    nm, st = NAMES.get(sid, (sid, "keep")); lab, tcls, bcls = TAG[st]
    bars.append(f'<div class="bar-row"><div class="bar-name">{esc(nm)}</div><div class="bar-track"><div class="bar {bcls}" style="width:{max(1, int(n / mx * 100))}%"></div></div>'
                f'<div class="bar-val num">{n:,} <span class="tag {tcls}" style="margin-inline-start:6px">{lab}</span></div></div>')


def outline(rows, foot):
    r = "".join(f'<div class="ui-row"><span style="font-weight:600">{a}</span><b style="font-weight:400;color:var(--text-secondary);text-align:end">{b}</b></div>' for a, b in rows)
    return (f'<div class="frame"><div class="frame-chrome"><i></i><i></i><i></i><div class="frame-url">Barak_Offense_Review</div></div>'
            f'<div class="frame-screen"><div class="ui-tile">{r}</div><div style="font-size:12.5px;color:var(--text-tertiary);margin-top:8px">{foot}</div></div></div>')


d3_preview = f"""<aside class="live" data-live="d3">
  <div class="label">Live Preview — The Page Outline</div>
  <div class="live-stage">
    <div class="pv is-active" data-opt="A">{outline([("1 · What to do next game", "3 instructions, each with its clip"), ("2 · The drives", "13 short cards: video + two lines"), ("3 · Am I improving", "3 numbers + last game's items")], "About 1,700 words. A five-minute read.")}</div>
    <div class="pv" data-opt="B">{outline([("1 · What to do next game", "3 instructions, each with its clip"), ("2 · The drives", "13 short cards: video + two lines"), ("3 · Am I improving", "3 numbers + last game's items"), ("Closed drawer", "27 possessions + word list")], "About 1,700 words on show, 5,400 more inside the drawer.")}</div>
    <div class="pv" data-opt="C">{outline([("Short version", ""), ("Game to game", ""), ("Fixes", ""), ("Clips", ""), ("Drives", ""), ("What already works", ""), ("Habits and weaknesses", ""), ("Teaching moments", ""), ("Drills", ""), ("Targets", ""), ("All 27 possessions", ""), ("Word list", ""), ("How it was made", "")], "13 sections, each rewritten shorter. Maybe 8,000 words.")}</div>
  </div>
  <div class="live-open"><a href="{REVIEW}" target="_blank">Open the review as it is now</a></div>
  <div class="live-hint">Pick an option — this updates.</div>
</aside>"""
d3_body = f"""<p class="narrative">The page is long because every finding appears several times: once as a strength or a habit, again as a fix, again as a teaching moment, again in the possession log. You read it alone and then act on it on the court, so it should fit in one sitting.</p>
<div class="viz"><div class="viz-title">How long the review is today</div>
<div class="stats">
  <div class="stat neg"><div class="stat-label">Words today</div><div class="stat-value num">{total:,}</div><div class="stat-sub">about 90 minutes of reading</div></div>
  <div class="stat"><div class="stat-label">Sections</div><div class="stat-value num">{len(words)}</div><div class="stat-sub">after the shot sections left</div></div>
  <div class="stat pos"><div class="stat-label">Words in option A</div><div class="stat-value num">1,700</div><div class="stat-sub">about five minutes</div></div>
</div>
<div style="height:14px"></div>
<div class="bars">{''.join(bars)}</div>
<div class="viz-cap">Words per section today. The label next to each number says what happens to that section in option A. Nothing is deleted from disk; the data behind every section stays in the results folder.</div></div>
<div class="label">Pick One</div>
<div class="options">
{option('d3', 'A', 'Three parts only', 'What to do next game (the 3 instructions, each with its clip) · The drives (one short card per drive) · Am I improving (the numbers from game to game).', 'No place on the page to look up one specific possession; the 27-possession log is only on disk.', rec=True, tags=[('about 1,700 words', 'pos')])}
{option('d3', 'B', 'Three parts plus one closed drawer', 'Same three parts. At the bottom, one closed drawer holds the 27 possessions and the word list.', 'The drawer is 5,400 words that will rarely be opened, and the page still feels long when it is.')}
{option('d3', 'C', 'Keep all 13 sections, each one shorter', 'Same structure as today. Every section is rewritten in plain words at about a third of its length.', 'Still 13 things to read, and the same finding still shows up in three places.')}
</div>
{note(3, 'e.g. A, but keep "what already works" as two lines at the top')}"""
cards.append(card(3, "What stays on the review page", "How much should the review page hold?", d3_body, d3_preview))
tldr.append(("What stays on the review page", "A", "Three parts only: what to do, the drives, am I improving"))

# ================================================================== D4 the drive card
HAPPENED = "<b>מה קרה:</b> דחפת את המגן אחורה והגעת כמעט לגובה שלו, בצד ימין שלך. אז חזרת אחורה והלכת לשמאל שלך, לצד שבו עמדו שלושה שחקנים. נתקעת ומסרת."
BETTER = "<b>מה עדיף:</b> להמשיך בצד ימין שלך, בקו ישר לסל. שם היה פנוי עד המגן, שעמד ליד הסל."
new_card = f"""<div class="frame"><div class="frame-chrome"><i></i><i></i><i></i><div class="frame-url">Drive · 2:51</div></div>
<div class="frame-screen">
  {zoom("sample_drive_freeze.jpg", "A frame from the sample video: the stop with the ring. Click to enlarge.")}
  <div style="font-size:12px;color:var(--text-tertiary);margin:4px 0 8px">Video, 15 seconds: real speed, slow motion, a stop with lines, then the simulation.</div>
  {he(HAPPENED, "font-size:13.5px;line-height:1.55;margin-bottom:6px")}
  {he(BETTER, "font-size:13.5px;line-height:1.55;margin-bottom:8px")}
  {zoom("sim_c15_panel.jpg", "What happened next to the simulation of the better move. Click to enlarge.")}
  <div style="font-size:12px;color:var(--text-tertiary);margin-top:4px">Left: what happened. Right: the Weavy figure taking the better step. Click a picture to enlarge it.</div>
</div></div>"""
short_rows = "".join(f'<div class="ui-row"><span class="he" style="font-size:12.5px">{t}</span></div>' for t in (
    "0:35 · הלכת לשמאל שלך, ימין שלך היה פנוי יותר",
    "1:33 · הצד הנכון, אבל חזרת אחורה במקום לסיים",
    "3:47 · שלושה מגנים ליד הסל, עדיף היה למסור לחבר לקבוצה"))
d4_preview = f"""<aside class="live" data-live="d4">
  <div class="label">Live Preview — One Drive</div>
  <div class="live-stage">
    <div class="pv is-active" data-opt="A">{new_card}<div class="live-open"><a href="{SAMPLE}" target="_blank">Play the sample video</a></div></div>
    <div class="pv" data-opt="B">{new_card}<div style="font-size:12.5px;color:var(--text-tertiary);margin:10px 0 6px">Five cards like this. The other eight drives, one line each:</div><div class="ui-tile">{short_rows}</div><div class="live-open"><a href="{SAMPLE}" target="_blank">Play the sample video</a></div></div>
    <div class="pv" data-opt="C">{zoom("drive_card_today.jpg", "The 2:51 drive card as it is today. Click to read it full-size.")}<div style="font-size:12.5px;color:var(--text-tertiary);margin-top:6px">Today's card for the same drive: 844 words, a court drawing, a frame, seven labels and a fold-out. Click to read it full-size. The video would be added under it.</div><div class="live-open"><a href="{REVIEW}#drives" target="_blank">Open the drives section</a></div></div>
  </div>
  <div class="live-hint">Pick an option — this updates.</div>
</aside>"""
d4_body = f"""<p class="narrative">You asked for the drives to work like the fixes: a video per drive, the Weavy simulation, and lines drawn on the picture, as in the 2:51 panel. The 2:51 drive is already built that way as a sample. Six of the 13 drives still have no simulation; each of them gets its own Weavy figure.</p>
<div class="viz"><div class="viz-title">One drive, today and proposed</div>
<div class="stats">
  <div class="stat neg"><div class="stat-label">Words, 2:51 drive today</div><div class="stat-value num">844</div><div class="stat-sub">drawing, frame, 7 labels, fold-out</div></div>
  <div class="stat pos"><div class="stat-label">Words, proposed</div><div class="stat-value num">45</div><div class="stat-sub">two lines under a 15-second video</div></div>
  <div class="stat"><div class="stat-label">Drives with a simulation</div><div class="stat-value num">7 of 13</div><div class="stat-sub">six more to build</div></div>
  <div class="stat accent"><div class="stat-label">Weavy credits</div><div class="stat-value num">63</div><div class="stat-sub">6 figures and 1 line test; 64 are left</div></div>
</div>
<div class="viz-cap">The line test: one run where Weavy draws the arrows itself. If they land in the wrong place I keep drawing them on the frame, as in the panel you liked.</div></div>
<div class="label">Where This Lives</div>
<div class="where"><b>analysis_2026-10-07/clips/drive_c15_0251.mp4</b> — the sample video (phone copy in clips/phone)<br><b>analysis_2026-10-07/work/weavy/</b> — the figures, the panels and the credit ledger</div>
<div class="label">Pick One</div>
<div class="options">
{option('d4', 'A', 'A video, two lines and the simulation, for all 13 drives', 'Each drive: a 15-second video, "what happened", "what was better", and the two pictures side by side. One combined drives video goes to your phone.', 'Thirteen videos are about three and a half minutes of watching, and the card no longer explains how the read was made (his feet, who was helping).', rec=True, tags=[('63 credits', ''), ('sample ready', 'pos')])}
{option('d4', 'B', 'The same card for the five drives that teach the most', 'Five full cards. The other eight drives get one line each.', 'A drive you care about, like the one at 4:24 you asked about, can end up in the one-line list.', tags=[('about 20 credits', '')])}
{option('d4', 'C', 'Keep the long card and add the video to it', 'Everything that is there today stays, with the video and the simulation added.', 'The drives part stays at 14,700 words.')}
</div>
{note(4, 'e.g. A, sorted from the worst decision to the best')}"""
cards.append(card(4, "What one drive looks like on the page", "How should each drive be shown?", d4_body, d4_preview))
tldr.append(("What one drive looks like on the page", "A", "Video + two lines + simulation, all 13 drives"))

# ================================================================== D5 what "snatch" means
def legend(items):
    return '<div style="font-size:13px;line-height:1.5;margin-top:8px">' + "".join(f'<div><b>{n}</b> {esc(t)}</div>' for n, t in items) + "</div>"


d5_preview = f"""<aside class="live" data-live="d5">
  <div class="label">Live Preview — Your Frame, 2:51</div>
  <div class="live-stage">
    <div class="pv is-active" data-opt="A">{zoom("snatch_A.jpg", "The hand in the way. Click to enlarge.")}{legend([(1, "the defender's right hand reaches for the ball."), (2, "The ball crosses right in front of it."), (3, "Your free hand. The check: did your body or your free arm keep his hand off the ball?")])}</div>
    <div class="pv" data-opt="B">{zoom("snatch_B.jpg", "The snatch dribble. Click to enlarge.")}{legend([(1, "He reaches."), (2, "You pull the ball back, out of his reach."), (3, "He is leaning forward, so you go past him.")])}</div>
    <div class="pv" data-opt="C">{zoom("snatch_C.jpg", "Steal risk. Click to enlarge.")}{legend([(1, "His hand."), (2, "The ball. The check: how many times in a game the ball was inside his reach.")])}</div>
  </div>
  <div class="live-hint">Pick an option — this updates. Click the picture to enlarge it.</div>
</aside>"""
d5_body = f"""<p class="narrative">You wrote "I don't snatch the defender's right hand here" about the 2:51 drive. I can read that in three ways, and each one adds a different check to every drive. In your frame his right hand reaches for the ball while you cross it over in front of him.</p>
<div class="viz"><div class="viz-title">The same moment under each reading</div>
<table class="matrix">
  <tr><th></th><th class="rec-col">A — The hand in the way</th><th>B — The snatch dribble</th><th>C — Steal risk</th></tr>
  <tr><td>Checked on every drive</td><td class="rec-col">Which of his hands reaches, and what you did about it</td><td>Did he reach, and did you pull the ball back and go</td><td>Was the ball inside his reach</td></tr>
  <tr><td>What the 2:51 card would say</td><td class="rec-col">His right hand went for the ball as you crossed it in front of him. Your free arm did not clear it.</td><td>He reached at 2:51.4. A pull-back and a step to your right was open.</td><td>The ball was inside his reach for about 0.3 seconds.</td></tr>
  <tr><td>Adds to each card</td><td class="rec-col">One line and a close-up</td><td>One line, only when he reached</td><td>One number per game</td></tr>
</table>
<div class="viz-cap">The 2:51 wording is an example of the style, written from these frames; the real lines are checked drive by drive after you pick.</div></div>
<div class="label">Pick One</div>
<div class="options">
{option('d5', 'A', 'The hand in the way', 'On every drive: which of the defender\'s hands reaches toward the ball, and what you did about it. You kept your body between his hand and the ball, you knocked his hand away with your free arm, or you left the ball in front of it.', 'Hands are about 10 pixels wide in this footage. On some drives the honest answer will be "cannot see".', rec=True)}
{option('d5', 'B', 'The snatch dribble', 'The quick pull-back of the ball when the defender reaches, and then going past him while he leans. On every drive: did he reach, and did you use it.', 'Says something only on the drives where he reached.')}
{option('d5', 'C', 'Steal risk only', 'A count per game of the moments the ball was inside a defender\'s reach.', 'A number with no fix attached.')}
</div>
{note(5, 'If you meant something else, describe the move in one line.')}"""
cards.append(card(5, "What 'snatch' should mean in the drive analysis", "Which of these did you mean by 'snatch'?", d5_body, d5_preview))
tldr.append(("What 'snatch' should mean in the drive analysis", "A", "The hand in the way: his reaching hand and what you did about it"))

# ================================================================== D6 practice material
d6_body = f"""<p class="narrative">Three outputs say what to practise: a drills table inside the review, two 25-minute plans, and a phone card with three tabs. They repeat each other. Most of the solo plan was shooting drills that came from the shot analysis, so the plans have to be rebuilt in any case.</p>
<div class="viz"><div class="viz-title">Where each piece lives</div>
<table class="matrix">
  <tr><th></th><th>Today</th><th class="rec-col">A — Phone card only</th><th>B — Review only</th><th>C — None for now</th></tr>
  <tr><td>Drills alone</td><td class="bad">review + phone card</td><td class="good rec-col">phone card</td><td class="mid">review</td><td class="mid">not shown</td></tr>
  <tr><td>Drills with a partner</td><td class="bad">review + phone card</td><td class="good rec-col">phone card</td><td class="mid">review</td><td class="mid">not shown</td></tr>
  <tr><td>Rules for inside a game</td><td class="bad">review + phone card</td><td class="good rec-col">phone card</td><td class="mid">review</td><td class="mid">not shown</td></tr>
  <tr><td>25-minute plans</td><td class="bad">mostly shooting</td><td class="good rec-col">rebuilt: decisions and drives</td><td class="mid">rebuilt, in the review</td><td class="mid">not shown</td></tr>
  <tr><td>The sentence to yourself, per item</td><td class="mid">review + phone card</td><td class="good rec-col">review + phone card</td><td class="mid">review</td><td class="good">review</td></tr>
</table>
<div class="viz-cap">In every option the drills cover only what is still in the review: deciding fast, passing to the free teammate, drives.</div></div>
<div class="label">Where This Lives</div>
<div class="where"><b>analysis_2026-10-07/Barak_Session_Card_2026-10-07.html</b> — the phone card (still has the old shooting plans until you pick)<br><b>analysis_2026-10-07/session_cards/</b> — the same three tabs as pictures</div>
<div class="label">Pick One</div>
<div class="options">
{option('d6', 'A', 'One phone card, nothing in the review', 'Three tabs: alone, with a partner, inside a game. The drills table and the plans leave the review page.', 'At the desk you open a second file to see the drills.', rec=True)}
{option('d6', 'B', 'Drills stay in the review, no phone card', 'One file holds everything. The phone card and its three pictures are dropped.', 'On the court you scroll a long page on the phone to find a drill.')}
{option('d6', 'C', 'No drills for now', 'Only the sentence to yourself stays next to each item. Drills come back when you ask for them.', 'The review says what to change but not how to practise it.')}
</div>
{note(6, 'e.g. A, and send me the three tabs as pictures on WhatsApp size')}"""
cards.append(card(6, "Drills, practice plans and the phone card", "Where should the practice material live?", d6_body))
tldr.append(("Drills, practice plans and the phone card", "A", "One phone card, nothing in the review"))

# ================================================================== D7 numbers from game to game
d7_body = f"""<p class="narrative">You asked to see whether the things you work on improve. Three of the five tracked numbers were shooting numbers and are gone, so two are left. The proposal is one number per instruction, counted the same way after every game, next to a status for each item from the game before.</p>
<div class="viz"><div class="viz-title">The numbers, this game, and who shows them</div>
<table class="matrix">
  <tr><th></th><th>This game</th><th>Target</th><th class="rec-col">A</th><th>B</th><th>C</th></tr>
  <tr><td>Ball still in your hands 4 seconds after you got it</td><td class="num">10 of 14</td><td class="num">3 of 14</td><td class="good rec-col">shown</td><td class="good">shown</td><td class="mid">status only</td></tr>
  <tr><td>A teammate stood free and did not get the ball</td><td class="num">9 possessions</td><td class="num">4</td><td class="good rec-col">shown</td><td class="good">shown</td><td class="mid">status only</td></tr>
  <tr><td>Drives to the freer side from the first step</td><td class="num">3 of 10</td><td class="num">6 of 10</td><td class="good rec-col">shown</td><td class="good">shown</td><td class="mid">status only</td></tr>
  <tr><td>Assists</td><td class="num">2</td><td class="num">none</td><td class="mid rec-col">not shown</td><td class="good">shown</td><td class="mid">not shown</td></tr>
  <tr><td>Lost balls</td><td class="num">2</td><td class="num">none</td><td class="mid rec-col">not shown</td><td class="good">shown</td><td class="mid">not shown</td></tr>
</table>
<div class="viz-cap">The first target was set in this review. The targets of 4 and of 6 of 10 are my proposal; change them in the note. The status per item is one of: better, partly, still there.</div></div>
<div class="label">Where This Lives</div>
<div class="where"><b>analysis_2026-10-07/history.json</b> — the running file, one entry per game</div>
<div class="label">Pick One</div>
<div class="options">
{option('d7', 'A', 'Three numbers, one per instruction, plus a status per item', 'Each instruction in the review has its own number and a target. Next game, each one is marked better, partly or still there, with the clips that show it.', 'Nothing about results: no points, no assists.', rec=True)}
{option('d7', 'B', 'Those three, plus assists and lost balls', 'Five numbers per game.', 'Five numbers again, and assists depend on a teammate making the shot.')}
{option('d7', 'C', 'No numbers, only the status per item', 'Each item gets better, partly or still there, with clips.', 'Without a count, "better" is an opinion.')}
</div>
{note(7, 'e.g. A, with a target of 5 of 10 for the drives')}"""
cards.append(card(7, "The numbers tracked from game to game", "Which numbers should every review repeat?", d7_body))
tldr.append(("The numbers tracked from game to game", "A", "Three numbers, one per instruction, plus a status per item"))

# ================================================================== D8 the side files
A = lambda *p: os.path.join(HERE, *p)
phone = sorted(glob.glob(A("clips", "phone", "*.mp4"))); full = sorted(glob.glob(A("clips", "*.mp4")))
shot_phone = [p for p in phone if re.search(r"2_keep|3_fix2|4_compare|5_keep", os.path.basename(p))]
rows8 = [
    ("Clips for the phone", f"{len(phone)} videos", f"{mb(phone):.0f} MB", "One combined video stays; the 4 shot clips go to the archive", "mid"),
    ("Full-size originals of the clips", f"{len(full)} videos", f"{mb(full):.0f} MB", "Archive. Only needed to re-cut a clip", "mid"),
    ("English copy of the review", "1 page", f"{mb([A('Barak_Offense_Review_2026-10-07_en.html')]):.0f} MB", "Archive. It is out of date and still has the shot analysis", "mid"),
    ("Research report on film analysis", "1 page", "11,500 words", "Stays in docs as reference. Not part of a game review", "good"),
    ("The first decision map (output formats)", "1 page", "answered", "Archive", "mid"),
    ("Simulation pictures", "8 panels + 1 stacked image", "", "The panels live inside the drive cards; the stacked image goes to the archive", "good"),
    ("Court drawings of the drives", "13 pictures", "", "Dropped from the page if you pick 4A", "mid"),
    ("Phone card", "1 page + 3 pictures", "", "See decision 6", "good"),
]
t8 = "".join(f'<tr><td>{esc(a)}</td><td class="num">{esc(b)}</td><td class="num">{esc(c)}</td><td class="{cls}" style="text-align:start">{esc(d)}</td></tr>' for a, b, c, d, cls in rows8)
d8_body = f"""<p class="narrative">Besides the review itself, this round left about 40 other files: videos in two sizes, pictures, an English copy, a research report and an older map. Once the clips sit inside the review, none of them is needed to read it.</p>
<div class="viz"><div class="viz-title">Everything that is not the review</div>
<table class="matrix">
  <tr><th>Output</th><th>How many</th><th>Size</th><th class="rec-col">What happens in option A</th></tr>
  {t8}
</table>
<div class="viz-cap">Green stays in use. Grey moves out of the way. Nothing in option A is deleted.</div></div>
<div class="label">Where This Lives</div>
<div class="where"><b>analysis_2026-10-07/</b> — the review, the phone card, clips/ and work/<br><b>docs/</b> — the research report and the decision maps</div>
<div class="label">Pick One</div>
<div class="options">
{option('d8', 'A', 'Move the unused files to an archive folder', 'Nothing is deleted. The working folder shows only the review, the phone card and one clips folder.', 'Links inside the first map and the handoff notes point to the old places; I update them.', rec=True)}
{option('d8', 'B', 'Delete the unused ones', f'The 4 shot clips, the English copy, the prototype clip and the full-size originals go: about {mb(full) + mb(shot_phone) + mb([A("Barak_Offense_Review_2026-10-07_en.html")]):.0f} MB.', 'A clip you want back has to be rendered again, about a minute each.')}
{option('d8', 'C', 'Leave everything where it is', 'No files move.', 'The folder keeps 40 files and it stays unclear which one is current.')}
</div>
{note(8, 'e.g. A, but delete the prototype clip')}"""
cards.append(card(8, "The files that are not the review", "What should happen to the side files?", d8_body))
tldr.append(("The files that are not the review", "A", "Move the unused files to an archive folder"))

# ================================================================== assemble
t = open(TEMPLATE, encoding="utf-8").read()
head_end = t.index('<div class="wrap">') + len('<div class="wrap">')
tail_start = t.index('<!-- ===================== GENERAL FEEDBACK')
head, tail = t[:head_end], t[tail_start:]
TOPIC = "Offense review clean-up"
THEME = """
/* OKC Thunder palette: this project is not Investing.com */
:root{--grey-900:#10213A;--grey-800:#2D3A4E;--grey-700:#4A5568;--grey-500:#718096;--navy:#002D62;
--pumpkin-orange:#EF3B24;--pumpkin-orange-hover:#D2331F;--mandarin-orange:#007AC1;--blue-link:#005F99;--blue-interactive:#007AC1;
--surface-dark:#002D62;--viz-1:#007AC1;--viz-2:#EF3B24;--viz-3:#002D62;--viz-6:#FDBB30;--viz-1-bg:#E5F2F9;--viz-2-bg:#FDEBE8;--viz-3-bg:#E6EAF0;--viz-track:#E9EEF5}
.stat.accent{border-color:#B9DDF0;background:#F2F9FD}
.he{direction:rtl;text-align:right;font-family:"Heebo","Segoe UI",Arial,sans-serif}
.mark{font-weight:700;font-size:15px;color:var(--navy);display:flex;align-items:center;gap:8px;white-space:nowrap}
.mark i{width:10px;height:10px;border-radius:9999px;background:var(--pumpkin-orange);display:block}
.matrix td.num{font-variant-numeric:tabular-nums}
"""
head = head.replace("</style>", THEME + "</style>", 1)
head, n_svg = re.subn(r'<svg aria-label="Investing\.com".*?</svg>', '<div class="mark"><i></i>Barak · offense review</div>', head, count=1, flags=re.S)
assert n_svg == 1
head = re.sub(r"<!-- Investing\.com wordmark.*?-->", "", head, flags=re.S)
head = head.replace("{{TOPIC}} — Decision Map", f"{TOPIC} — Decision Map").replace("{{TOPIC}} — decision map", f"{TOPIC} — decision map").replace("{{PROJECT}} · {{DATE}}", "Basketball · offense review · 11.10.2026")
head, n_scope = re.subn(r"\{\{One or two sentences:.*?\}\}", "Everything that was produced for the 07.10 game, and what to keep, merge or drop so the review is short and clear. "
                        "After you paste the summary back I rebuild the review, the drives and the phone card in one pass. Outside this map: the recap and Top 10 videos.", head, count=1, flags=re.S)
assert n_scope == 1
head = head.replace('<span class="pill"><strong>{{N}}</strong> decisions</span>', f'<span class="pill"><strong>{len(cards)}</strong> decisions</span>')
head = head.replace('<span class="pill">Est. review <strong>{{X}} min</strong></span>', '<span class="pill">Est. review <strong>10 min</strong></span>')
head = head.replace('<span class="pill brand">Round <strong>{{R}}</strong></span>', '<span class="pill brand">Round <strong>1</strong></span>')
tail = tail.replace('"{{TOPIC}} — Decision Summary"', f'"{TOPIC} — Decision Summary"')
tldr_html = ['<section class="tldr"><h2>At a Glance — What I\'m Recommending</h2>']
for i, (q, letter, rec) in enumerate(tldr, 1):
    tldr_html.append(f'<div class="tldr-row"><div class="tldr-n">{i}</div><div class="tldr-q">{esc(q)}</div><div class="tldr-rec"><b>{letter}</b> {esc(rec)}</div><a href="#d{i}">Open</a></div>')
tldr_html.append("</section>")
settled = f"""<section class="settled">
  <h2>Already Done Or Settled — No Action Needed</h2>
  <table>
    <tr><td>Shot analysis</td><td>Removed from the review: the shot list and map, shooting numbers, the July technique follow-up, the "step back for a three" fix and four shot clips. Decision 1 shows the exact line.</td><td class="ok">Done</td></tr>
    <tr><td>The unclear opening</td><td>Replaced by three plain instructions. The two remaining fixes are rewritten as: what happened, what to do, how it looks when it is right. Decision 2 lets you pick another opening.</td><td class="ok">Done</td></tr>
    <tr><td>Drives use Weavy</td><td>Every drive gets a simulation with lines on it and its own video, like the fixes. The 2:51 drive is built as a sample (decision 4). 36 of the first 100 credits are used; the rest go to the drives.</td><td class="ok">Settled</td></tr>
    <tr><td>Lines drawn by Weavy</td><td>One test run where Weavy draws the arrows itself. If they land in the wrong place I keep drawing them on the frame, as in the panel you liked.</td><td class="ok">Settled</td></tr>
    <tr><td>The combined clips video</td><td>Now three clips, 48 seconds: decide fast, the free teammate, the 4:24 drive.</td><td class="ok">Done</td></tr>
  </table>
</section>"""
page = head + "\n\n" + "\n".join(tldr_html) + "\n\n" + settled + "\n\n" + "\n\n".join(cards) + "\n\n" + tail
left = re.findall(r"\{\{.*?\}\}", page.split("<script>")[0])
assert not left, left[:5]
os.makedirs(DOCS, exist_ok=True)
open(OUT, "w", encoding="utf-8", newline="\n").write(page)
print("wrote", OUT, f"{os.path.getsize(OUT) / 1e6:.2f} MB", "| decisions:", len(cards))
