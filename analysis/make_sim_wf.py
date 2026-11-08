"""Generate workflows/sim_composites.js: one builder per Weavy simulation composite, one reviewer over all panels, repairs.

The tasks (verified Hebrew context + tracker boxes) are embedded in the script; they are also saved to work/weavy/sim_tasks.json.
"""
import json, os, re

A = "<project>/analysis_2026-10-07"
R = lambda n: json.load(open(os.path.join("results", n), encoding="utf-8"))
report = R("report_plain.json"); drives = {d["clip"]: d for d in R("drives.json")}
final = R("drive_patterns_final.json"); notes = {n["clip"]: n["note"] for n in final.get("drive_notes", [])}
clips = {c["i"]: c for c in json.load(open("clip_map.json", encoding="utf-8"))}
tl = json.load(open("../recap_2026-10-07/data/user_timeline_v2.json", encoding="utf-8"))["frames"]
fixes = {f["rank"]: f for f in report["priority_fixes"]}
moments = report["teaching_moments"]


def boxes(clip, reel_t, span=1.6):
    c = clips[clip]; out = []
    for f in tl:
        rt = c["reel_start"] + (f["t"] - c["src_start"])
        if c["src_start"] <= f["t"] <= c["src_end"] and abs(rt - reel_t) <= span:
            out.append({"reel": round(rt, 1), "box": f["box"]})
    return out


def moment(clip, t):
    return next((m["caption"] for m in moments if m["clip"] == clip and abs(m["reel_time"] - t) < 0.3), "")


def drive_ctx(c):
    d = drives[c]
    keep = ("decision_reel", "passby_reel", "start_spot", "defender", "side_attacked", "open_by_defender", "help_side", "help_note",
            "side_open", "side_reason", "angle", "angle_note", "outcome", "outcome_note", "better_choice", "cue", "visibility")
    return {"record": {k: d[k] for k in keep}, "defender_at_decision": d["defender_at_decision"], "barak_feet_px": d["barak_feet_px"],
            "second_coach_note": notes.get(c, "")}


tasks = [
    {"id": "fix2_c00", "clip": 0, "game": 1, "figure": "work/weavy/gen_03_set_shot.png", "anchor": "feet_center", "outfit": "maroon_tee",
     "suggested_reel": 8.4,
     "goal": "Fix 2: one step back turns his most frequent shot into a three. At the release of shot c007 (reel about 8.4; his feet were at about (648, 638), roughly one metre INSIDE the arc at the top, with the defender about two metres off) show him one step back, with both feet behind the three-point line, at the set point of the same shot. The real side shows where he actually shot from. Mark the three-point line next to his feet on both sides so the difference is visible.",
     "verified": {"fix": fixes[2], "teaching_caption": moment(0, 8.0)}, "tracker": boxes(0, 8.4)},
    {"id": "fix3_c14", "clip": 14, "game": 2, "figure": "work/weavy/gen_04_kick_out_pass.png", "anchor": "feet_center", "outfit": None,
     "suggested_reel": 163.0,
     "goal": "Fix 3: when a second defender steps up, the ball goes to the open teammate while the dribble is still alive. At the moment he gathered into three defenders (reel about 162.7-163.2) show him stopped on two feet and passing back out to a teammate, who stands alone at the top of the arc. Ring a teammate and draw the pass (green arrow) from the ball to him. The real side shows the shot he took into three bodies. The pass figure faces left; that suits a pass back out toward the top of the arc. If a teammate is not visibly alone at the top in the frame you choose, pick the frame where he is, or skip.",
     "verified": {"fix": fixes[3], "teaching_caption": moment(14, 163.2), "drive": drive_ctx(14)}, "tracker": boxes(14, 163.0)},
    {"id": "drive_c11", "clip": 11, "game": 1, "figure": "work/weavy/gen_02_drive_far_hand.png", "anchor": "right_foot", "outfit": "maroon_tee",
     "suggested_reel": drives[11]["decision_reel"],
     "goal": "Drive, clip 11: he attacked the correct side (his left) but late and on a wide diagonal, after an extra dribble in place, so the defender stayed in front. Show the alternative at the moment the defender reacted to the fake: leaving at once with a first dribble toward the basket on his left, ball in the LEFT hand (the far hand), away from the defender. Draw the tight line (green) and, on the real side, the wide diagonal he actually took (red).",
     "verified": {"drive": drive_ctx(11)}, "tracker": boxes(11, drives[11]["decision_reel"])},
]
for c in (13, 15, 24, 25):
    tasks.append({"id": f"drive_c{c}", "clip": c, "game": 2 if c < 18 else 3, "figure": "work/weavy/gen_01_drive_near_hand.png", "anchor": "right_foot", "outfit": None,
                  "suggested_reel": drives[c]["decision_reel"],
                  "goal": f"Drive, clip {c}: his right was the less crowded side and his final move did not go there. Show the alternative at the decision moment: a first step to his right (the near side), ball in the right hand. Draw the path into the less crowded space (green) and, on the real side, what he actually did (red). Use the wording of the verified text about how far that side was free.",
                  "verified": {"drive": drive_ctx(c)}, "tracker": boxes(c, drives[c]["decision_reel"])})
os.makedirs("work/weavy", exist_ok=True)
json.dump(tasks, open("work/weavy/sim_tasks.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

script = r"""export const meta = {
  name: 'bball-sim-composites',
  description: 'Place the Weavy-generated figures on the real frames: one builder per simulation, one reviewer over all panels, repairs',
  phases: [
    { title: 'Build', detail: 'one builder per simulation composite' },
    { title: 'Review', detail: 'one reviewer checks every panel against the verified text' },
    { title: 'Repair', detail: 'builders fix what the reviewer flagged' },
  ],
}

const A = '__A__'
const BRIEF = `${A}/work/weavy/SIM_BRIEF.md`
const TASKS = __TASKS__

const RESULT = {
  type: 'object',
  properties: {
    id: { type: 'string' },
    status: { type: 'string', enum: ['done', 'skip'] },
    reason: { type: 'string', description: 'why it was skipped, or empty' },
    panel_jpg: { type: 'string', description: 'path of the final panel, relative to the analysis folder' },
    annotated_jpg: { type: 'string' },
    spec_json: { type: 'string' },
    title_he: { type: 'string', description: 'Hebrew title for the review, at most 10 words, starting with "סימולציה:"' },
    caption_he: { type: 'string', description: 'Hebrew caption for the review, 2-3 short sentences: what the left side shows, what the right side shows, and that it is an illustration and not a measurement' },
    tries: { type: 'integer' },
    self_check: { type: 'string', description: 'one line per quality-bar item: pass or what is still imperfect' },
  },
  required: ['id', 'status', 'reason', 'panel_jpg', 'annotated_jpg', 'spec_json', 'title_he', 'caption_he', 'tries', 'self_check'],
}

const buildPrompt = (t, extra) => `You are building ONE simulation composite for a basketball offense review. First Read the brief ${BRIEF} in full and look at the finished example it names. Then do the task below.

TASK id: ${t.id} (clip ${t.clip}, game ${t.game})
FIGURE: ${t.figure} | anchor: ${t.anchor} | outfit: ${t.outfit || 'none (orange bib, as generated)'}
SUGGESTED MOMENT: reel ${t.suggested_reel} s (frame ${String(Math.round(t.suggested_reel * 10) + 1).padStart(5, '0')}.jpg). You may move a few tenths of a second.
GOAL: ${t.goal}

VERIFIED TEXT (Hebrew, already checked against the frames by two reviewers; your labels and caption must agree with it):
${JSON.stringify(t.verified, null, 1)}

TRACKER BOXES of the real Barak around that moment ([x0, y0, x1, y1] in full-frame pixels; may be missing or wrong when he is hidden):
${JSON.stringify(t.tracker)}

Write the spec to work/weavy/sim_${t.id}.json with "out": "work/weavy/sim_${t.id}.png" and the panel at "work/weavy/sim_${t.id}_panel.jpg".
${extra || ''}`

phase('Build')
const built = await parallel(TASKS.map(t => () => agent(buildPrompt(t), { label: `build:${t.id}`, phase: 'Build', schema: RESULT })))
const done = built.map((b, i) => b ? { ...b, id: TASKS[i].id } : null).filter(Boolean)
log(`Built: ${done.filter(d => d.status === 'done').length} done, ${done.filter(d => d.status === 'skip').length} skipped, ${TASKS.length - done.length} failed`)

phase('Review')
const REVIEW = {
  type: 'object',
  properties: { reviews: { type: 'array', items: { type: 'object', properties: {
    id: { type: 'string' }, verdict: { type: 'string', enum: ['ok', 'fix', 'drop'] },
    problems: { type: 'array', items: { type: 'string' } },
  }, required: ['id', 'verdict', 'problems'] } } },
  required: ['reviews'],
}
const toReview = done.filter(d => d.status === 'done')
const review = toReview.length ? await agent(`You are the picky reviewer of simulation composites made for a basketball player's offense review. Read the brief ${BRIEF} (it has the quality bar). Then, for every item below, Read its panel image (path relative to ${A}) and judge it against the quality bar and against the verified text of its task.

Be strict about four things: (1) leftovers of the real player on the simulated side, (2) a figure that floats, is sunk, or is clearly the wrong size, (3) wrong layering with a nearer player, (4) a caption or label that claims more than the frame shows (for example "ריק" where a defender stands there, or an "open" teammate who has a defender next to him). Small imperfections of the generated face do not matter.
verdict: "ok" = good enough to show him; "fix" = worth one repair round, say exactly what to change; "drop" = the frame does not support the claim, or it cannot be made to look right.

ITEMS:
${JSON.stringify(toReview.map(d => ({ id: d.id, panel_jpg: d.panel_jpg, title_he: d.title_he, caption_he: d.caption_he, self_check: d.self_check, goal: TASKS.find(t => t.id === d.id).goal, verified: TASKS.find(t => t.id === d.id).verified })), null, 1)}`,
  { label: 'review-all', phase: 'Review', schema: REVIEW }) : { reviews: [] }
const verdictOf = id => (review?.reviews || []).find(r => r.id === id)

phase('Repair')
const toFix = toReview.filter(d => verdictOf(d.id)?.verdict === 'fix').slice(0, 3)
const dropped = toReview.filter(d => verdictOf(d.id)?.verdict === 'fix').slice(3).map(d => d.id)
if (dropped.length) log(`Not repaired (cap of 3 repairs): ${dropped.join(', ')}`)
const repaired = await parallel(toFix.map(d => () => {
  const t = TASKS.find(x => x.id === d.id)
  return agent(buildPrompt(t, `THIS IS A REPAIR ROUND. Your spec already exists at ${d.spec_json} and the panel at ${d.panel_jpg}. A reviewer flagged these problems; fix exactly these, re-run, and check the panel again:
${(verdictOf(d.id).problems || []).map(p => '- ' + p).join('\n')}`), { label: `repair:${d.id}`, phase: 'Repair', schema: RESULT })
}))
const final = done.map(d => {
  const v = verdictOf(d.id)
  const rep = repaired.filter(Boolean).find(r => r.id === d.id)
  return { ...(rep || d), id: d.id, review: v ? v.verdict : (d.status === 'skip' ? 'skipped' : 'not_reviewed'), problems: v ? v.problems : [], repaired: !!rep }
})
return { final }
"""
script = script.replace("__A__", A).replace("__TASKS__", json.dumps(tasks, ensure_ascii=False, indent=1))
script = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", script).replace("\r\n", "\n")
open("workflows/sim_composites.js", "w", encoding="utf-8", newline="\n").write(script)
print("wrote workflows/sim_composites.js", len(script), "tasks", [t["id"] for t in tasks])
