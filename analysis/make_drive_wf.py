"""Generate workflows/drive_analysis.js: one reviewer per drive possession (frames + sheets), a patterns pass, a skeptic pass.
Hebrew output. Embeds each drive's possession narrative from results/records.json so the agent starts with context.
"""
import json, re
A = "<project>/analysis_2026-10-07"
DRIVES = [2, 8, 9, 10, 11, 13, 14, 15, 20, 23, 24, 25, 26]
QUESTIONS = {23: "Barak's own question about this drive (reel 4:24): 'after the shot fake (hesitation) the defender raised his right arm to try to block; it seems my angle was too wide. Or was I supposed to eventually drive right to avoid the three defenders in the lane?' Answer it explicitly in better_choice: was the angle too wide, which side was open given the defender's raised RIGHT arm, and whether going right (away from the three defenders) was the better line."}
recs = {r["clip"]: r for r in json.load(open("results/records.json", encoding="utf-8"))}
clips = {c["i"]: c for c in json.load(open("clip_map.json", encoding="utf-8"))}
items = []
for c in DRIVES:
    r = recs[c]; cm = clips[c]
    items.append({"clip": c, "reel_start": cm["reel_start"], "reel_end": cm["reel_end"], "narrative": r["narrative"],
                  "sequence": r["on_ball_sequence"], "drive_direction": r["drive_direction"], "dribble_hand": r["dribble_hand"],
                  "defender": r["defender"], "better_option": r["better_option_available"],
                  "question": QUESTIONS.get(c, "")})
court = re.search(r"const COURT = `.*?`\n", open("workflows/clip_analysis_resume2.js", encoding="utf-8").read(), re.S).group(0)

script = """export const meta = {
  name: 'bball-drive-analysis',
  description: 'For every drive in the offense reel: which side was open from the defender stance, which side and angle he took, hesitation before the drive; patterns; skeptic check. Hebrew output.',
  phases: [
    { title: 'Drives', detail: 'one reviewer per drive possession (13)' },
    { title: 'Patterns', detail: 'counts across the drives, priorities, cues' },
    { title: 'Verify', detail: 'skeptic re-watches the frames behind each pattern' },
    { title: 'Finalize', detail: 'head coach rewrites the summary from the corrected claims' },
  ],
}

const A = '__A__'
const BRIEFS = `${A}/briefs`
const FRAMES = `${A}/work/frames`
__COURT__
const HEBREW = `
LANGUAGE: all free-text fields in natural, plain Hebrew addressed to Barak in the masculine second person ("אתה", "ימין שלך"). English only for accepted lingo (floater, pull-up, layup, closeout, crossover, hesitation / "hezi", jab step), explained in plain Hebrew the first time. Names: ברק, המגן, המגן, המגן, המגן, חבר לקבוצה, חבר לקבוצה, חבר לקבוצה, חבר לקבוצה. Numbers as digits. "Right" and "left" ALWAYS from Barak's own point of view, written explicitly ("ימין שלך", "שמאל שלך"); when you describe the defender's hand or foot say whose it is ("יד שמאל של המגן").
`
const ITEMS = __ITEMS__

const DRIVE = {
  type: 'object',
  properties: {
    clip: { type: 'integer' },
    drive_start_reel: { type: 'number', description: 'reel time (s, one decimal) of the first drive dribble' },
    decision_reel: { type: 'number', description: 'reel time of the moment the decision is made: the last frame before the first drive dribble (or before the hesitation move that replaced the drive)' },
    passby_reel: { type: 'number', description: 'reel time when he is level with the first defender, or when the drive dies' },
    start_spot: { type: 'string' },
    defender: { type: 'string' },
    defender_at_decision: { type: 'object', properties: {
      distance_m: { type: 'number' },
      feet: { type: 'string', enum: ['square', 'left_foot_forward', 'right_foot_forward', 'unclear'], description: 'the DEFENDER\\'s feet' },
      hand_up: { type: 'string', enum: ['none', 'left', 'right', 'both', 'unclear'], description: 'the DEFENDER\\'s raised hand(s)' },
      weight: { type: 'string', enum: ['flat', 'back_on_heels', 'forward', 'moving_toward', 'moving_away', 'unclear'] },
      feet_px: { type: 'array', items: { type: 'number' }, description: '[x, y] full-frame pixels of the defender feet at the decision moment' },
      note: { type: 'string' },
    }, required: ['distance_m', 'feet', 'hand_up', 'weight', 'feet_px', 'note'] },
    barak_feet_px: { type: 'array', items: { type: 'number' }, description: '[x, y] full-frame pixels of Barak feet at the decision moment' },
    side_attacked: { type: 'string', enum: ['right', 'left', 'middle', 'none'], description: 'from Barak\\'s point of view' },
    open_by_defender: { type: 'string', enum: ['right', 'left', 'either', 'none', 'unclear'], description: 'the side the FIRST defender\\'s body gave (lead foot / raised hand / momentum), from Barak\\'s point of view' },
    help_side: { type: 'string', enum: ['right', 'left', 'both', 'none', 'unclear'], description: 'the side(s) where a help defender stood in the driving path, from Barak\\'s point of view' },
    help_note: { type: 'string', description: 'who the help defenders were and where they stood' },
    side_open: { type: 'string', enum: ['right', 'left', 'either', 'none', 'unclear'], description: 'the best side with both reads together, from Barak\\'s point of view' },
    side_reason: { type: 'string', description: 'why that side was open: his hand, his front foot, his weight, the help defender; or why neither' },
    angle: { type: 'string', enum: ['tight_past_hip', 'wide_loop', 'lateral', 'into_chest', 'none', 'unclear'] },
    angle_note: { type: 'string', description: 'estimate of the sideways gap in metres between the two of them at the pass-by, and where the path went' },
    hesitation_moves: { type: 'integer', description: 'number of moves in place before the drive: jab, crossover in place, pound dribble, pull-back, shot fake' },
    hesitation_note: { type: 'string', description: 'what the moves were and whether any of them moved the defender' },
    first_step: { type: 'string', enum: ['explosive', 'normal', 'slow', 'none', 'unclear'] },
    pace_change: { type: 'boolean' },
    outcome: { type: 'string', enum: ['beat_defender', 'contained', 'help_stopped', 'pass', 'shot', 'turnover', 'other'] },
    outcome_note: { type: 'string' },
    right_decision: { type: 'string', enum: ['yes', 'partly', 'no', 'unclear'] },
    better_choice: { type: 'string', description: '1-2 sentences, concrete: which side, which angle, at what moment' },
    cue: { type: 'string', description: 'at most 12 Hebrew words, something to say to himself' },
    teaching_frame: { type: 'object', properties: { reel_time: { type: 'number' }, caption: { type: 'string' }, kind: { type: 'string', enum: ['positive', 'corrective'] } }, required: ['reel_time', 'caption', 'kind'] },
    visibility: { type: 'string' },
    confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
  },
  required: ['clip', 'drive_start_reel', 'decision_reel', 'passby_reel', 'start_spot', 'defender', 'defender_at_decision', 'barak_feet_px', 'side_attacked', 'open_by_defender', 'help_side', 'help_note', 'side_open', 'side_reason', 'angle', 'angle_note', 'hesitation_moves', 'hesitation_note', 'first_step', 'pace_change', 'outcome', 'outcome_note', 'right_decision', 'better_choice', 'cue', 'teaching_frame', 'visibility', 'confidence'],
}

const pad = i => String(i).padStart(3, '0')
phase('Drives')
const drives = await parallel(ITEMS.map(it => () =>
  agent(`You are a basketball player-development coach reviewing ONE drive (a dribble attack toward the basket) by an adult recreational player, frame by frame, to answer three questions he asked: did he attack the open side (reading the defender's raised hand, front foot and weight), was the angle past the defender tight or too wide, and did a hesitation move replace the drive.

CONTEXT FOR THIS POSSESSION (written by an earlier reviewer; reliable on what happened and when, not on the drive reads):
clip ${it.clip}, reel ${it.reel_start.toFixed(1)}-${it.reel_end.toFixed(1)} s. Sequence: ${JSON.stringify(it.sequence)}. Earlier read: drive ${it.drive_direction}, dribble hand ${it.dribble_hand}. Defender: ${it.defender}
Narrative: ${it.narrative}
Better option noted earlier: ${it.better_option}
${it.question ? 'PLAYER QUESTION: ' + it.question : ''}

STEP 1: Read ${BRIEFS}/r${pad(it.clip)}.json (Read tool) and view its flow and zoom sheets (Read renders images) to find the drive.
STEP 2: View FULL-RESOLUTION FRAMES around the decision: the frame for reel time t is ${FRAMES}/<k>.jpg with k = round(t*10)+1 padded to 5 digits (e.g. t = 42.6 -> 00427.jpg). View these frames and no more than 8 images in total: 0.5 s before the first drive dribble, the decision moment, the first step, the pass-by moment (when he is level with the defender or the drive dies), and the outcome. Zoom mentally on the DEFENDER: which foot is forward, which hand is up, where his weight is, how far he stands.
STEP 3: Fill the record. SIDES IN THIS CAMERA VIEW: Barak attacks toward the right of the image. When he faces the rim from the top of the arc, his RIGHT side is the NEAR side (toward the camera, lower in the image) and his LEFT side is the FAR side (away from the camera, higher in the image). A defender facing him is mirrored: the DEFENDER's right hand and right foot are on the FAR side (Barak's left), the defender's left hand and left foot are on the NEAR side (Barak's right). Work out each hand and foot from the body, then translate to Barak's point of view. HOW TO JUDGE THE OPEN SIDE, two separate reads. Read 1, the first defender's body (field open_by_defender): (a) LEAD FOOT: the side of the foot he has forward is the side to attack, because he has to turn his hips (drop-step) before he can follow; (b) RAISED HAND: a hand raised to contest a shot or a shot fake lifts his weight and normally goes with the same-side foot forward, so the side of the RAISED hand is the open side, and his LOW hand is the one that can poke the dribble, so the low-hand side is the risky side; (c) MOMENTUM: a defender running at him or leaning one way cannot change direction, so the side against his momentum is open. Say which of a/b/c you actually saw. Read 2, the help (field help_side): where the second and third defenders stand. A side with a defender waiting in the driving path is closed even if the first defender gives it. Then side_open is the best side with BOTH reads taken together; when they conflict (his body gives one side, the help closes it) say so in side_reason and say which one mattered more on this play. Angle: tight_past_hip = shoulder goes past the defender's hip within about half a metre; wide_loop = he swings a metre or more sideways before going forward; lateral = east-west dribbling that never turns toward the basket; into_chest = straight into a set defender. Count the hesitation moves in place before the drive (jab, crossover in place, pound dribble, pull-back, shot fake) and say whether any of them moved the defender. If the drive is hidden by the dark object or by bodies, say so in visibility and lower confidence; never invent what you cannot see. Pixel positions: full-frame 1920x1080 coordinates of the feet (bottom of the body).
${HEBREW}
${COURT}`, { label: `drive:r${pad(it.clip)}`, phase: 'Drives', schema: DRIVE })))
const ok = drives.filter(Boolean)
log(`Drives done: ${ok.length}/${ITEMS.length}`)

phase('Patterns')
const PATTERNS = {
  type: 'object',
  properties: {
    summary: { type: 'string', description: '2-4 sentences, Hebrew' },
    counts: { type: 'object', properties: {
      drives: { type: 'integer' }, open_side_taken: { type: 'integer' }, open_side_missed: { type: 'integer' }, side_unclear: { type: 'integer' },
      tight: { type: 'integer' }, wide: { type: 'integer' }, lateral: { type: 'integer' }, into_chest: { type: 'integer' },
      with_hesitation: { type: 'integer' }, hesitation_that_moved_defender: { type: 'integer' }, beat_defender: { type: 'integer' }, right_hand: { type: 'integer' }, left_hand: { type: 'integer' },
    }, required: ['drives', 'open_side_taken', 'open_side_missed', 'side_unclear', 'tight', 'wide', 'lateral', 'into_chest', 'with_hesitation', 'hesitation_that_moved_defender', 'beat_defender', 'right_hand', 'left_hand'] },
    findings: { type: 'array', items: { type: 'object', properties: {
      finding: { type: 'string' }, numbers: { type: 'string' }, evidence_clips: { type: 'array', items: { type: 'integer' } }, confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
    }, required: ['finding', 'numbers', 'evidence_clips', 'confidence'] } },
    rule_check: { type: 'string', description: 'Hebrew: the raised-hand rule stated clearly with the mirror explained, then where it applied in his drives, where the help overrode it, with clip evidence' },
    priorities: { type: 'array', items: { type: 'object', properties: {
      what: { type: 'string' }, why: { type: 'string' }, cue: { type: 'string' }, evidence_clips: { type: 'array', items: { type: 'integer' } },
    }, required: ['what', 'why', 'cue', 'evidence_clips'] } },
  },
  required: ['summary', 'counts', 'findings', 'rule_check', 'priorities'],
}
const patterns = await agent(`You are the head coach summarising the drive records below (one per drive possession, written in Hebrew by frame-by-frame reviewers) for the player himself. Count: open side taken vs missed (use side_open, the read with the help included), angle types, hesitation moves and whether they moved the defender, drives that beat the first defender, dribble hand. Write 4-7 findings with counts and clip evidence, check the rule he was told. In his words: "if a defender raises his left hand to contest the shot I can drive left". The standard coaching version is: attack the side of the hand the defender raises (and of his front foot), and remember the mirror, the defender's left hand is on Barak's RIGHT. State the rule clearly in rule_check with the mirror explained, then say on which drives it applied, on which the help defenders overrode it, and how often he followed it, and give 2-3 priorities with a cue each. Where records disagree or are low confidence, say so and lower confidence.
${HEBREW}
DRIVE RECORDS:
${JSON.stringify(ok)}`, { label: 'drive-patterns', phase: 'Patterns', schema: PATTERNS })

phase('Verify')
const VERDICT = {
  type: 'object',
  properties: { claim: { type: 'string' }, verdict: { type: 'string', enum: ['confirmed', 'partly', 'refuted', 'not_visible'] }, evidence: { type: 'string' }, corrected_claim: { type: 'string' }, clips_checked: { type: 'array', items: { type: 'integer' } } },
  required: ['claim', 'verdict', 'evidence', 'clips_checked'],
}
const claims = [...(patterns?.findings || []).slice(0, 5).map(f => ({ text: `${f.finding} (${f.numbers})`, clips: f.evidence_clips })), ...(patterns?.priorities || []).slice(0, 2).map(p => ({ text: `PRIORITY: ${p.what} - ${p.why}`, clips: p.evidence_clips }))]
const verdicts = await parallel(claims.map((c, i) => () => {
  const list = (c.clips || []).slice(0, 4).map(k => `${BRIEFS}/r${pad(k)}.json`).join('\\n')
  return agent(`You are a skeptical second coach. Try to REFUTE the claim below by looking at the frames: read each brief listed (Read tool), view its flow and zoom sheets, and open full-resolution frames (${FRAMES}/<k>.jpg, k = round(reel_t*10)+1, 5 digits) around the drives. Judge only what you can see: confirmed / partly (write the corrected claim) / refuted / not_visible. Right and left are from Barak's point of view. Write evidence and corrected_claim in Hebrew.
CLAIM: ${c.text}
CLIPS: ${JSON.stringify(c.clips)}
BRIEFS:
${list}
${COURT}`, { label: `verify:${i}`, phase: 'Verify', schema: VERDICT })
}))
const vOk = verdicts.filter(Boolean)
const tally = vOk.reduce((m, v) => ({ ...m, [v.verdict]: (m[v.verdict] || 0) + 1 }), {})
log(`Verify done: ${JSON.stringify(tally)}`)
phase('Finalize')
const INT = { type: 'integer' }
const CLIPS = { type: 'array', items: { type: 'integer' } }
const CHECK = { type: 'string', enum: ['confirmed', 'corrected', 'not_checked'] }
const FINAL = {
  type: 'object',
  properties: {
    summary: { type: 'string', description: '3-5 sentences, Hebrew, every number matching the corrected findings' },
    counts: { type: 'object', properties: {
      drives: INT, open_side_taken: INT, open_side_missed: INT, side_unclear: INT, tight: INT, wide: INT, lateral: INT, into_chest: INT,
      with_hesitation: INT, hesitation_that_moved_defender: INT, beat_defender: INT, beat_defender_half_step: INT, right_hand: INT, left_hand: INT,
    }, required: ['drives', 'open_side_taken', 'open_side_missed', 'side_unclear', 'tight', 'wide', 'lateral', 'into_chest', 'with_hesitation', 'hesitation_that_moved_defender', 'beat_defender', 'beat_defender_half_step', 'right_hand', 'left_hand'] },
    findings: { type: 'array', items: { type: 'object', properties: {
      finding: { type: 'string' }, numbers: { type: 'string' }, evidence_clips: CLIPS, confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
      second_check: CHECK, what_changed: { type: 'string' },
    }, required: ['finding', 'numbers', 'evidence_clips', 'confidence', 'second_check', 'what_changed'] } },
    rule_check: { type: 'string' },
    priorities: { type: 'array', items: { type: 'object', properties: {
      what: { type: 'string' }, why: { type: 'string' }, cue: { type: 'string' }, evidence_clips: CLIPS, second_check: CHECK, what_changed: { type: 'string' },
    }, required: ['what', 'why', 'cue', 'evidence_clips', 'second_check', 'what_changed'] } },
    drive_notes: { type: 'array', items: { type: 'object', properties: { clip: INT, note: { type: 'string' } }, required: ['clip', 'note'] } },
  },
  required: ['summary', 'counts', 'findings', 'rule_check', 'priorities', 'drive_notes'],
}
const checked = verdicts.map((v, i) => v ? { index: i, verdict: v.verdict, corrected_claim: v.corrected_claim || '', evidence: v.evidence } : null).filter(Boolean)
const finalP = await agent(`You are the head coach. You wrote the drive summary below (SUMMARY) for the player from 13 per-drive records. A skeptical second coach then re-watched the frames behind your first five findings and your first two priorities and returned a verdict and a corrected claim for each (VERDICTS: index 0-4 = findings 1-5 in order, index 5-6 = priorities 1-2). Produce the FINAL version that the player will read, in the structured format.

Rules:
- Where the second coach corrected a number, a count, a clip list or an interpretation, the corrected version wins. Use his corrected claim as the basis of that finding or priority, in plain Hebrew, and put the counts in "numbers". Set second_check = "corrected" and say in what_changed, in one short sentence, what changed against the first version. If he confirmed it unchanged: second_check = "confirmed", what_changed = "".
- Findings and priorities he did not check keep their content with second_check = "not_checked", but any number in them that contradicts a corrected finding must be brought in line with the corrected one (say so in what_changed).
- counts: the corrected counts. beat_defender = clear passes of the first defender only; beat_defender_half_step = drives where he gained only about half a step; tight / wide / lateral / into_chest as the second coach regrouped them (lateral = dribbling without turning toward the basket, into_chest = going straight at a defender).
- summary: 3-5 sentences, rewritten so every number matches the corrected findings. Include the second coach's caveat wherever it changes the meaning of a finding (for example, that going to the side the defender gave may be a habit of leaving to one side and not a read).
- rule_check: keep the explanation of the raised-hand rule with the mirror, then bring the part about where it applied in line with the corrected findings and add the caveat.
- priorities: for a corrected priority, "what" is a short title (at most 12 words), "why" the corrected reasoning, "cue" at most 12 Hebrew words.
- drive_notes: one entry per drive about which the second coach's evidence corrects or adds something specific (side attacked, both sides attacked in one possession, a clear pass versus half a step, a hidden moment, no contact, and so on): one or two short Hebrew sentences. Only drives he actually said something specific about.
- Do not invent anything that is in neither input. Keep every clip number.
${HEBREW}
SUMMARY:
${JSON.stringify(patterns)}

VERDICTS:
${JSON.stringify(checked)}`, { label: 'drive-final', phase: 'Finalize', schema: FINAL })
return { drives: ok.length, findings: (patterns?.findings || []).length, tally, final: !!finalP }
"""
script = script.replace("__A__", A).replace("__COURT__", court).replace("__ITEMS__", json.dumps(items, ensure_ascii=False, indent=1))
script = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", script).replace("\r\n", "\n")
open("workflows/drive_analysis.js", "w", encoding="utf-8", newline="\n").write(script)
print("wrote workflows/drive_analysis.js", len(script), "drives", len(items))
