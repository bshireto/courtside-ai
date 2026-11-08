export const meta = {
  name: 'bball-reel-clip-analysis',
  description: 'Analyse all 27 possessions of Barak offense reel from contact sheets, synthesize through three coaching lenses, aggregate a scouting report, adversarially verify every claim',
  phases: [
    { title: 'Clips', detail: 'one vision agent per possession (27)' },
    { title: 'Lenses', detail: 'shot selection / mechanics / off-ball synthesizers' },
    { title: 'Report', detail: 'aggregate into one scouting report' },
    { title: 'Verify', detail: 'skeptic re-views the frames behind every claim' },
  ],
}

const BRIEFS = '<project>/analysis_2026-10-07/briefs'
const N = 27

const COURT = `
HOW TO READ THE FOOTAGE
- One fixed phone camera on the near sideline around mid-court, looking right toward the hoop. The hoop (rim ~ (1254,320) in full-frame px) is at the top right, seen from the side; the white backboard is right of the rim. Night, covered outdoor court.
- A big dark out-of-focus object covers the TOP-LEFT of the frame; players behind it are hidden (only legs/arms may show).
- Court lines: the big WHITE arc is the 3-point line; its apex (farthest from the hoop) is at the left ~ (527,645) px full-frame. The red-brown rectangle is the paint; the free-throw line is its LEFT edge. YELLOW lines belong to another sport: ignore them. Half-court game: both teams attack this one hoop; after a make or defensive rebound the ball is taken back out past the arc and "checked" (bounced to the defender and back) at the top.
- Times: every tile is stamped "reel m:ss.s" (time inside the offense reel) and "src m:ss.s" (time in the original game video). Use REEL time when you cite a moment.
- Sheet kinds: "flow" = wide court crop, 2 frames per second, 2 columns x 4 rows, read left-to-right then down. "zoom" = a 640x560 window that follows Barak's tracked box at 5 fps ([box] = tracker had him, [xy] = window placed on the shot position, [fallback] = tracker lost him, the window may NOT contain him). "shot strip" = the same window at 10 fps from 1.4 s before the release to 1.0 s after it, the tile marked RELEASE is the release frame. "release frame" = the full 1920x1080 frame at the release (judge the feet against the arc here).

WHO IS WHO
- BARAK (the player we analyse): bald / shaved light-skinned head, medium-heavy build, dark-red / maroon short-sleeve T-shirt, black knee-length shorts with a white side stripe, black socks, maroon / red sneakers. Game 1 (G1): no pinnie. Games 2-3 (G2, G3): an ORANGE pinnie over the maroon shirt (red sleeves show).
- Look-alikes who are NOT him: the defender (bald, black T-shirt, dark shoes; lime pinnie rolled around the neck from G2), the defender (bald, heavier, all black with LONG trousers), a teammate (short grey hair, grey T-shirt, beige shorts).
- His usual defender: the defender - wavy grey-brown hair, black sleeveless top, black shorts, bright ORANGE shoes (lime pinnie from G2).
- Other opponents: the defender (dark hair + beard, white sleeveless top; lime from G2), the defender, the defender.
- Teammates: a teammate (tall, dark hair + beard, black tank top, dark green shorts), a teammate (white T-shirt, white shorts; G1 and G3), a teammate (grey T-shirt, beige shorts; G1 and G2), a teammate (dark hair + beard, BLUE shorts, white shoes; G2 and G3).
`

const CLIP_SCHEMA = {
  type: 'object',
  properties: {
    clip: { type: 'integer' },
    narrative: { type: 'string', description: '2-5 sentences: what actually happened, in coaching language, verified against the frames' },
    pipeline_notes_agreement: { type: 'string', enum: ['agree', 'minor_discrepancy', 'major_discrepancy'] },
    discrepancies: { type: 'string' },
    play_start: { type: 'string', description: 'check_ball | defensive_rebound | offensive_rebound | loose_ball | outlet_catch | handoff | cut_catch | spot_up_catch | inbound | other' },
    on_ball_sequence: { type: 'array', items: { type: 'string' }, description: 'ordered actions e.g. catch, hold, jab, dribble_right, pull_back, drive_left, gather, shot' },
    hold_seconds_before_action: { type: 'number', description: 'seconds he held the ball before the first dribble/pass/shot; -1 if not visible' },
    dribbles_before_release_or_pass: { type: 'integer', description: 'count; -1 if not visible' },
    drive_direction: { type: 'string', enum: ['right', 'left', 'both', 'none', 'unclear'] },
    dribble_hand: { type: 'string', enum: ['right', 'left', 'both', 'none', 'unclear'] },
    defender: { type: 'string' },
    shot: { type: 'object', properties: {
      present: { type: 'boolean' },
      shot_id: { type: 'string' },
      type: { type: 'string', description: 'pull-up 2 | pull-up 3 | catch-and-shoot 2 | catch-and-shoot 3 | runner/floater | layup | hook | post move | other' },
      zone: { type: 'string', description: 'e.g. top of arc (3), top of key long 2, far elbow, near elbow, lane, left wing, right wing, corner' },
      contest: { type: 'string', enum: ['open', 'light', 'tight', 'heavily_contested', 'unclear'] },
      made: { type: 'boolean' },
      points: { type: 'integer' },
      feet_set_and_square: { type: 'string' },
      fade_or_drift: { type: 'string' },
      jump: { type: 'string', description: 'low / medium / high and straight up or drifting' },
      release_hands: { type: 'string', enum: ['one_hand', 'two_hand_push', 'unclear'] },
      guide_hand_note: { type: 'string' },
      arc: { type: 'string', enum: ['flat', 'medium', 'high', 'unclear'] },
      landing_balance: { type: 'string' },
      rushed: { type: 'boolean' },
      shot_quality_1to5: { type: 'integer', description: '1 = bad shot (contested, off balance, long two early in the clock) ... 5 = great shot (open, in rhythm, good zone)' },
      keep_or_cut: { type: 'string', enum: ['keep', 'keep_but_improve', 'cut'] },
      mechanics_notes: { type: 'string' },
    }, required: ['present'] },
    pass: { type: 'object', properties: {
      present: { type: 'boolean' },
      type: { type: 'string', description: 'drop-off | lob | kick-out | handoff | outlet | swing | entry | other' },
      to: { type: 'string' },
      quality: { type: 'string', description: 'good | risky | late | turnover | unclear' },
      led_to: { type: 'string' },
      notes: { type: 'string' },
    }, required: ['present'] },
    rebound_or_loose_ball: { type: 'object', properties: {
      present: { type: 'boolean' }, type: { type: 'string' }, notes: { type: 'string' },
    }, required: ['present'] },
    off_ball_before_touch: { type: 'string', description: 'cut / relocate / stand / screen / sprint to spot / not visible' },
    spacing_and_open_teammates: { type: 'string' },
    better_option_available: { type: 'string', description: 'name the better option if there was one, with the reel time; else "none seen"' },
    decision_quality: { type: 'string', enum: ['good', 'acceptable', 'questionable', 'poor', 'n/a'] },
    decision_reason: { type: 'string' },
    execution_quality: { type: 'string', enum: ['good', 'acceptable', 'poor', 'n/a'] },
    execution_reason: { type: 'string' },
    positives: { type: 'array', items: { type: 'string' } },
    improvement_cue: { type: 'string', description: 'ONE short external-focus cue (<= 12 words) a coach would say about this possession' },
    teaching_frames: { type: 'array', items: { type: 'object', properties: {
      reel_time: { type: 'number' }, caption: { type: 'string' }, kind: { type: 'string', enum: ['positive', 'corrective'] },
    }, required: ['reel_time', 'caption', 'kind'] } },
    visibility_limits: { type: 'string' },
    confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
  },
  required: ['clip', 'narrative', 'pipeline_notes_agreement', 'play_start', 'on_ball_sequence', 'hold_seconds_before_action',
    'dribbles_before_release_or_pass', 'drive_direction', 'dribble_hand', 'defender', 'shot', 'pass', 'rebound_or_loose_ball',
    'off_ball_before_touch', 'spacing_and_open_teammates', 'better_option_available', 'decision_quality', 'decision_reason',
    'execution_quality', 'execution_reason', 'positives', 'improvement_cue', 'teaching_frames', 'visibility_limits', 'confidence'],
}

const LENS_SCHEMA = {
  type: 'object',
  properties: {
    lens: { type: 'string' },
    findings: { type: 'array', items: { type: 'object', properties: {
      finding: { type: 'string' },
      kind: { type: 'string', enum: ['strength', 'weakness', 'tendency'] },
      numbers: { type: 'string', description: 'the count behind it, e.g. "7 of 13 shots", or "" ' },
      evidence_clips: { type: 'array', items: { type: 'integer' } },
      confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
    }, required: ['finding', 'kind', 'evidence_clips', 'confidence'] } },
    suggested_priorities: { type: 'array', items: { type: 'object', properties: {
      what: { type: 'string' }, why: { type: 'string' }, cue: { type: 'string' }, evidence_clips: { type: 'array', items: { type: 'integer' } },
    }, required: ['what', 'why', 'cue', 'evidence_clips'] } },
    teaching_moments: { type: 'array', items: { type: 'object', properties: {
      clip: { type: 'integer' }, reel_time: { type: 'number' }, caption: { type: 'string' }, kind: { type: 'string', enum: ['positive', 'corrective'] },
    }, required: ['clip', 'reel_time', 'caption', 'kind'] } },
  },
  required: ['lens', 'findings', 'suggested_priorities', 'teaching_moments'],
}

const REPORT_SCHEMA = {
  type: 'object',
  properties: {
    headline: { type: 'string' },
    stat_context: { type: 'string' },
    strengths: { type: 'array', items: { type: 'object', properties: {
      title: { type: 'string' }, detail: { type: 'string' }, evidence_clips: { type: 'array', items: { type: 'integer' } },
    }, required: ['title', 'detail', 'evidence_clips'] } },
    weaknesses: { type: 'array', items: { type: 'object', properties: {
      title: { type: 'string' }, detail: { type: 'string' }, how_often: { type: 'string' }, evidence_clips: { type: 'array', items: { type: 'integer' } },
    }, required: ['title', 'detail', 'how_often', 'evidence_clips'] } },
    tendencies: { type: 'array', items: { type: 'object', properties: {
      tendency: { type: 'string' }, numbers: { type: 'string' }, evidence_clips: { type: 'array', items: { type: 'integer' } },
    }, required: ['tendency', 'numbers', 'evidence_clips'] } },
    shot_by_shot: { type: 'array', items: { type: 'object', properties: {
      shot_id: { type: 'string' }, clip: { type: 'integer' }, reel_time: { type: 'number' }, zone: { type: 'string' }, type: { type: 'string' },
      contest: { type: 'string' }, dribbles: { type: 'integer' }, result: { type: 'string' }, quality_1to5: { type: 'integer' },
      verdict: { type: 'string', enum: ['keep', 'keep_but_improve', 'cut'] }, note: { type: 'string' },
    }, required: ['shot_id', 'clip', 'reel_time', 'zone', 'type', 'contest', 'result', 'quality_1to5', 'verdict', 'note'] } },
    priority_fixes: { type: 'array', items: { type: 'object', properties: {
      rank: { type: 'integer' }, what: { type: 'string' }, why_it_matters_most: { type: 'string' }, cue: { type: 'string' },
      what_good_looks_like: { type: 'string' }, evidence_clips: { type: 'array', items: { type: 'integer' } },
    }, required: ['rank', 'what', 'why_it_matters_most', 'cue', 'what_good_looks_like', 'evidence_clips'] } },
    teaching_moments: { type: 'array', items: { type: 'object', properties: {
      clip: { type: 'integer' }, reel_time: { type: 'number' }, caption: { type: 'string' }, kind: { type: 'string', enum: ['positive', 'corrective'] },
    }, required: ['clip', 'reel_time', 'caption', 'kind'] } },
    one_thing: { type: 'string' },
    next_game_targets: { type: 'array', items: { type: 'object', properties: {
      metric: { type: 'string' }, this_game: { type: 'string' }, target: { type: 'string' },
    }, required: ['metric', 'this_game', 'target'] } },
  },
  required: ['headline', 'stat_context', 'strengths', 'weaknesses', 'tendencies', 'shot_by_shot', 'priority_fixes', 'teaching_moments', 'one_thing', 'next_game_targets'],
}

const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    claim: { type: 'string' },
    verdict: { type: 'string', enum: ['confirmed', 'partly', 'refuted', 'not_visible'] },
    evidence: { type: 'string' },
    corrected_claim: { type: 'string' },
    clips_checked: { type: 'array', items: { type: 'integer' } },
  },
  required: ['claim', 'verdict', 'evidence', 'clips_checked'],
}

const pad = i => String(i).padStart(3, '0')

phase('Clips')
const records = await parallel(Array.from({ length: N }, (_, i) => () =>
  agent(`You are an experienced basketball player-development coach reviewing ONE offensive possession of an adult recreational player from game film, frame by frame.

STEP 1: Read the brief file ${BRIEFS}/r${pad(i)}.json with the Read tool. It contains: the clip's reel/source time range, the game (G1-G3) and teams, the pipeline's touch notes (written earlier by review agents who tracked the ball; they are reliable on WHAT happened and WHEN, but say nothing about quality or coaching), his shot(s) in this clip with the release time, and the list of contact sheets with their absolute paths.
STEP 2: View EVERY sheet listed under sheets.flow, sheets.zoom, sheets.shot_strips and sheets.release_frames with the Read tool (it renders images). Do not skip any. Look at the flow sheets first to understand the possession, then the zoom / shot strips for his body and the ball.
STEP 3: Fill the structured record. Rules:
- Verify the pipeline notes against the frames; report agreement or discrepancies.
- Coaching judgement, not description for its own sake: was it a good decision, was it executed well, what was the better option (name the open teammate and where, with the reel time), what would a coach say in one short cue.
- Mechanics calls (two-hand push vs one-hand release, flat arc, drifting, off-balance landing) need at least two consecutive frames that show it; otherwise answer "unclear". Never invent detail the frames do not show. Note what was hidden (dark object, other players, small size).
- Hold time = from his catch (or rebound) until the first dribble, pass or shot; estimate from the tile timestamps.
- Shot quality 1-5 and keep / keep_but_improve / cut: judge like a coach who wants him to be efficient in a half-court pickup game: open catch-and-shoot threes, drives to the rim, shots in rhythm = good; long contested twos after a long hold, airballs from deep, forced shots in traffic = cut.
- teaching_frames: 1-3 moments (reel time with one decimal) with a caption of max 14 words, written like an on-screen coaching caption; mark positive or corrective.
- improvement_cue: external-focus, short, about the environment or the outcome ("hit the far side of the rim", "attack the hip", "catch and go on one count"), not body-part instructions.
${COURT}`, { label: `clip:r${pad(i)}`, phase: 'Clips', schema: CLIP_SCHEMA })))
const recs = records.filter(Boolean)
log(`Clips done: ${recs.length}/${N} records`)

const GAME_CONTEXT = `
GAME CONTEXT
- This game (07.10.2026, 3 of 4 pickup games, ~28 min on court): 12 points, 5/13 FG (38%), 2/5 threes, 3/8 twos, 2 assists. Every make checked at the rim.
- Previous game (23.09.2026, ~25 min): 6 points, 2/12 FG (17%), 2/5 threes, 0/7 twos, 3 assists.
- Two-game totals: 7/25 FG (28%), 4/10 threes (40%), 3/15 twos (20%), 5 assists.
- July 2026 close-up shooting-form analysis (front, low angle, one rep in practice): strong deep leg load and balance, holds the follow-through; but a two-hand push release with the guide hand propelling, shooting elbow flaring out, ball carried dead-centre in front of the face, and a two-motion rhythm (dip, pause at the face, push). Prescribed: one-hand form shooting, "silent" guide hand, wall snaps, one-motion "dip and go", off-centre set point.
- Pipeline-tagged shot types this game: c007 pull-up long two top of key (make), c008 pull-up long two top (miss), c013 pull-up three top straight off the check (miss), c017 contested deep three top (airball), c035 one-foot running pull-up far elbow contested (make), c036 catch-and-shoot long two far wing off handoff contested (miss), s011 two-hand shot at the free-throw line after a handoff, altered (airball/miss), c049 driving contested layup left wing through contact (miss), s018 pull-up long two far side after defensive rebound (miss), c077 pull-up three top open (make), c078 pull-up three top light contest (make), c089 driving running right-hand hook in the lane (make), c107 pull-up far elbow contested (miss).
`

phase('Lenses')
const LENSES = [
  { key: 'shot-selection-decisions', prompt: `LENS: SHOT SELECTION AND DECISION-MAKING. Count and characterise: shot mix (zone, type, contest, dribbles before the shot, hold time before the action), which shots were good shots and which should be cut, how often he attacks early vs holds and sizes up, passing decisions (drop-offs, lobs, kick-outs, handoffs: good / risky / late), turnovers and near-turnovers, how often a better option was available and he did not take it, how his two makes from three and his misses from two relate to shot quality (not luck). Produce findings with numbers and clip evidence.` },
  { key: 'mechanics-footwork-finishing', prompt: `LENS: MECHANICS, FOOTWORK AND FINISHING. Across all shots and drives: release hands (one-hand vs two-hand push) and whether the July diagnosis shows up in games, arc, jump and balance, drift/fade, footwork into the pull-up (hop vs 1-2, feet set?), gather and rhythm (one motion vs hitch), drive direction and dribble hand (right vs left), finishing package (runner, hook, layup through contact, what he has and what is missing), consistency between made and missed shots. Produce findings with clip evidence; separate what is clearly visible from what is inferred.` },
  { key: 'offball-effort-tempo', prompt: `LENS: OFF-BALL PLAY, REBOUNDING, SPACING, PACE AND TEMPO. What he does before he gets the ball (cuts, relocation, standing, screens), rebounds and loose balls (how he gets them, what he does next, outlet quality), spacing (where he stands relative to teammates, does he crowd drives, does he relocate after passing), pace (how long he holds, does the offense stall when he has it, does he play fast after rebounds), physical signs across G1 -> G3 (legs, jump height, late-game shots), and how his possessions start (check-ball vs flow). Produce findings with clip evidence.` },
]
const lenses = await parallel(LENSES.map(l => () =>
  agent(`You are a basketball player-development coach synthesising the per-possession records of ONE player's offense reel (27 possessions, one record each, produced by frame-by-frame reviewers). ${l.prompt}

Rules: every finding carries clip numbers as evidence and a count where a count exists. Do not repeat the records back; find the patterns. If the records disagree with each other or seem unreliable on a point, say so and lower confidence. Also propose 2-3 priorities for this lens (what, why, one external-focus cue) and 4-6 teaching moments (clip, reel_time, caption <= 14 words, positive or corrective) drawn from the records' teaching_frames.
${GAME_CONTEXT}

PER-POSSESSION RECORDS (JSON):
${JSON.stringify(recs)}`, { label: `lens:${l.key}`, phase: 'Lenses', schema: LENS_SCHEMA })))
const lensOk = lenses.filter(Boolean)
log(`Lenses done: ${lensOk.length}/3`)

phase('Report')
const report = await agent(`You are the head coach writing the scouting report on ONE adult recreational player's offense, for the player himself, from (a) 27 per-possession records produced by frame-by-frame reviewers and (b) three lens syntheses (shot selection / mechanics / off-ball). Produce the structured report.

Rules:
- Honest and specific. Strengths first (3-5), then weaknesses (3-6, each with how often it happened and clip evidence), then tendencies with numbers (5-10), then a shot-by-shot table for all 13 shots (use the records; quality 1-5; keep / keep_but_improve / cut; one-line note), then exactly 3 priority fixes ranked by expected impact on his scoring efficiency in THIS kind of game (half-court pickup, same defender most of the night), each with a short external-focus cue and a description of what good looks like, then 10-16 teaching moments for an annotated video (clip, reel_time, caption <= 14 words, positive/corrective, roughly 1 positive for every 2 corrective), then "one_thing" (the single change to carry into the next game, one sentence), then 4-6 next-game targets (metric, this game's value, target).
- Where the lens syntheses disagree, go back to the records and decide; say what you decided.
- Numbers in the tendencies must be countable from the records (e.g. "held 2+ s before acting on 6 of 9 check-ball possessions").
- No praise inflation, no hedging mush. Coaching language a player understands.
${GAME_CONTEXT}

LENS SYNTHESES:
${JSON.stringify(lensOk)}

PER-POSSESSION RECORDS:
${JSON.stringify(recs)}`, { label: 'aggregate-report', phase: 'Report', schema: REPORT_SCHEMA })

phase('Verify')
const claims = []
for (const w of (report?.weaknesses || [])) claims.push({ text: `WEAKNESS: ${w.title} - ${w.detail} (${w.how_often})`, clips: w.evidence_clips })
for (const t of (report?.tendencies || [])) claims.push({ text: `TENDENCY: ${t.tendency} (${t.numbers})`, clips: t.evidence_clips })
for (const p of (report?.priority_fixes || [])) claims.push({ text: `PRIORITY FIX #${p.rank}: ${p.what} - ${p.why_it_matters_most}`, clips: p.evidence_clips })
for (const s of (report?.strengths || [])) claims.push({ text: `STRENGTH: ${s.title} - ${s.detail}`, clips: s.evidence_clips })
log(`Verifying ${claims.length} claims against the frames`)
const verdicts = await parallel(claims.map((c, i) => () => {
  const clipsToCheck = (c.clips || []).slice(0, 4)
  const briefList = clipsToCheck.map(k => `${BRIEFS}/r${pad(k)}.json`).join('\n')
  return agent(`You are a skeptical second coach. Your job is to try to REFUTE the claim below by looking at the actual frames. Read each brief file listed (Read tool), then view the flow sheets and shot strips it lists (Read tool renders images). Judge only what you can see. If the frames support the claim, say confirmed; if only partly (e.g. the count is off, or it holds in some clips but not others), say partly and write the corrected claim; if the frames contradict it, say refuted; if the frames cannot show it, say not_visible.

CLAIM: ${c.text}
EVIDENCE CLIPS CITED: ${JSON.stringify(c.clips)}
BRIEF FILES TO READ (one per clip, each lists its sheet image paths):
${briefList || '(no clips cited - judge from the records and say not_visible if you cannot)'}
${COURT}`, { label: `verify:${i}`, phase: 'Verify', schema: VERDICT_SCHEMA })
}))
const vOk = verdicts.filter(Boolean)
const tally = vOk.reduce((m, v) => ({ ...m, [v.verdict]: (m[v.verdict] || 0) + 1 }), {})
log(`Verify done: ${JSON.stringify(tally)}`)

return { records: recs, lenses: lensOk, report, verdicts: vOk }