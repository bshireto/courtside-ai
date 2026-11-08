export const meta = {
  name: 'bball-offense-analysis-research',
  description: 'Research best practices for analysing an amateur player offense reel, drills, feedback delivery and output formats; verify load-bearing claims; synthesize',
  phases: [
    { title: 'Sweep', detail: 'seven researchers, each a different angle' },
    { title: 'Verify', detail: 'independent skeptic per load-bearing claim' },
    { title: 'Critique', detail: 'completeness critic finds gaps, one extra sweep' },
    { title: 'Synthesize', detail: 'one validated report' },
  ],
}

const CONTEXT = `
SITUATION (read carefully, it shapes what is useful):
- The player ("Barak") is an adult recreational basketball player. He plays pickup 4-on-4 half-court games at night on a covered outdoor court, roughly weekly. Not a pro, not a youth player.
- Footage: ONE fixed phone camera on the near sideline around mid-court, wide lens, 1920x1080 at 30 fps. Players are only ~100-160 px tall in frame. The hoop is seen from the side. Fine hand mechanics are hard to read; gross mechanics (jump, balance, landing, one- vs two-hand release, arc, footwork, decisions, spacing, shot selection) are readable.
- He already has a working Python/ffmpeg pipeline (YOLO11 detections, player tracking, make/miss detection at the rim, shooter attribution, per-player stats cards, an "offense reel" of all his possessions, Top 10 videos). The offense reel for the last game is 5:16 long: 27 clips, each one of his offensive possessions, with "+2 PTS / ASSIST" pop-ups and a stats card.
- Last game line: 12 points, 5/13 FG (38%), 2/5 threes, 3/8 twos, 2 assists, ~28 minutes over 3 games. Many of his shots are pull-up jumpers after a long hold / size-up at the top of the arc against the same defender; several contested; two airballs; he also had good rebounds and loose-ball recoveries and lob/drop-off passes.
- A separate close-up shooting-form analysis in July 2026 (front, low angle, one rep) found: strong leg load and balance (good), but a two-hand push release, shooting elbow flaring out, ball carried dead-centre in front of the face, and a two-motion (dip, pause, push) rhythm. Drills were prescribed (one-hand form shooting, silent guide hand, wall snaps, one-motion rhythm).
- Tooling available for the analysis workflow: Claude (vision over extracted frames and contact sheets, NOT native video viewing), ffmpeg 8.1, Python with OpenCV, ultralytics YOLO11 (detection and pose models), torch CPU, Pillow, matplotlib; ability to render annotated videos (captions, overlays, slow-motion, zoom, side-by-side) with ffmpeg; ability to produce self-contained HTML reports.
- GOAL: design a recurring workflow where, after every game, the reel is analysed and he gets insights, drills and anything that takes his game to the next level; and decide which output formats (HTML report, captioned video, annotated clips, shot chart, pose overlays, progress tracker, etc.) are worth building.

RESEARCH RULES:
- Use WebSearch (mode "extended" when a standard search is thin) and WebFetch to read the actual pages. Do not answer from memory alone; every finding carries a URL you actually opened.
- Prefer primary and expert sources: coaching organisations, peer-reviewed sports-science papers, established player-development coaches, product documentation (Hudl, Synergy, HomeCourt, Noah, Dartfish, OnForm), NBA tracking-data analyses, well-known basketball analytics writers.
- Be concrete: names of frameworks, taxonomies, numbers, cue words, drill names with reps, product features. Vague statements ("video analysis is helpful") are worthless.
- Mark a finding load_bearing=true only if the final recommendations would change if it were false (about 3-6 per researcher).
- Return raw structured data via the StructuredOutput tool. Your final text is data, not a message to a human.
`

const FINDINGS_SCHEMA = {
  type: 'object',
  properties: {
    angle: { type: 'string' },
    findings: { type: 'array', items: { type: 'object', properties: {
      claim: { type: 'string' },
      detail: { type: 'string' },
      source_url: { type: 'string' },
      source_title: { type: 'string' },
      confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
      load_bearing: { type: 'boolean' },
    }, required: ['claim', 'detail', 'source_url', 'confidence', 'load_bearing'] } },
    output_format_ideas: { type: 'array', items: { type: 'object', properties: {
      name: { type: 'string' }, what: { type: 'string' }, why_it_helps: { type: 'string' },
      effort: { type: 'string' }, seen_at: { type: 'string' },
    }, required: ['name', 'what', 'why_it_helps'] } },
    drills: { type: 'array', items: { type: 'object', properties: {
      name: { type: 'string' }, fixes: { type: 'string' }, how: { type: 'string' }, source_url: { type: 'string' },
    }, required: ['name', 'fixes', 'how'] } },
    interesting: { type: 'array', items: { type: 'string' } },
    gaps: { type: 'array', items: { type: 'string' } },
  },
  required: ['angle', 'findings', 'interesting'],
}

const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    claim: { type: 'string' },
    verdict: { type: 'string', enum: ['confirmed', 'partly', 'refuted', 'unverifiable'] },
    evidence: { type: 'string' },
    corrected_claim: { type: 'string' },
    source_url: { type: 'string' },
  },
  required: ['claim', 'verdict', 'evidence'],
}

const ANGLES = [
  { key: 'film-frameworks', prompt: `ANGLE 1 - How coaches and skills trainers actually break down ONE player's offensive film.
Find: the frameworks and tagging taxonomies used (possession-by-possession tagging; play-type categories like Synergy's isolation / P&R ball handler / spot-up / cut / off-screen / transition / post-up / hand-off / putback; shot-type and defender-distance categories; "shot quality" models such as Second Spectrum qSQ/qSI or Shot Quality by the NBA tracking data; dribbles-before-shot and touch-time splits), what a player development coach looks for in film (shot selection, decision speed, footwork into the shot, pace change, spacing, off-ball movement, finishing package), the structure of a player "tendency report" or self-scouting report (sections, what goes first), and how college/pro staffs run an individual film session (length, clip counts, ratio of positive to corrective clips, questioning technique). Include anything about analysing an amateur or pickup player specifically.` },
  { key: 'feedback-science', prompt: `ANGLE 2 - Feedback and motor-learning science: how to deliver video feedback so it actually changes behaviour.
Find: peer-reviewed evidence on video feedback in sport (self-modelling, feedforward, delayed vs immediate, frequency, bandwidth feedback, summary feedback), external-focus cue research (Gabriele Wulf) and short cue words, the evidence on positive-to-corrective ratio, "one cue at a time" / attentional overload, how expert coaches structure a review (strengths first? question-led?), and transfer: why form-shooting gains often do not transfer to game shots and what practice design (variable / random practice, representative design, constraints-led approach, game-speed reps, pressure) fixes that. Also anything on self-coaching for adult amateurs (self-review checklists, goal setting, tracking). Give concrete numbers (effect sizes, recommended frequencies) where the papers give them.` },
  { key: 'drills-mapping', prompt: `ANGLE 3 - Drill library mapped to the weaknesses an adult pickup player typically shows.
Find well-regarded drills (with reps, sets, and the exact cue) for: (a) shooting mechanics fixes - guide-hand push, elbow flare, ball centred on the face, two-motion hitch, one-motion rhythm, arc; (b) pull-up jumper off the dribble with balance (footwork: 1-2 step vs hop, inside-foot pivot, pull-back dribble); (c) finishing at the rim with contact, off-hand layups, floater, euro-step for older players; (d) triple-threat and first step, jab/rip series, reading a closeout; (e) catch-and-shoot and relocation (why catch-and-shoot percentages beat pull-ups); (f) decision-making and passing out of the drive (drop-off, kick-out, lob reads) and reads vs a tight on-ball defender; (g) rebounding and loose-ball habits; (h) conditioning and mobility for adult rec players to keep legs under the shot late in a run; (i) solo 20-30 minute session templates with make-counts. Prefer sources like Breakthrough Basketball, Pro Skills Basketball, Basketball HQ, Coach Daniel (By Any Means), Train For Hoops, Dr Dish, PGC, USA Basketball coach education, and known skills coaches. Include measurable progress tests (e.g., 3-minute shooting test, form-shooting make counts, Noah arc targets 45-47 degrees).` },
  { key: 'output-formats', prompt: `ANGLE 4 - How video analysis is DELIVERED today: output formats and which ones change behaviour.
Find and describe concretely: Hudl (annotated playlists, telestration, comments, shared clips), Synergy player and tendency reports (what sections and charts), Dartfish / OnForm / Hudl Technique / Coach's Eye (side-by-side, slow motion, drawing tools, voice-over, "stromotion" and "simulcam"), Krossover-style breakdown reports, HomeCourt (shot tracking, release time, vertical, speed, "AI feedback"), Noah Basketball (arc, depth, left-right with 45-degree targets), ShotTracker and Dr Dish stats dashboards, NBA-style shot charts and hex maps, pose-skeleton overlays (e.g., products using pose estimation for shooting form), scouting-report PDFs, progress trackers across games, and "captioned coaching clips" formats used by skills trainers on Instagram/YouTube (what the captions say, pause frames, arrows, before/after). For each, say what it looks like, what it takes to produce, and any evidence or expert opinion on whether it changes behaviour or is just pretty. Also look for tools or writeups where someone built an AI film-review (LLM or vision model) for a single player, and what format they produced.` },
  { key: 'cv-feasibility', prompt: `ANGLE 5 - Computer-vision feasibility from ONE wide fixed camera of amateur basketball.
Find concrete evidence on: what can be measured reliably from wide fixed footage (shot location, make/miss, possession tags, player speed and distance, spacing, time of possession) vs what cannot (hand/finger mechanics), pose estimation on small subjects (YOLO11-pose, RTMPose, MediaPipe, ViTPose: minimum subject pixel height, accuracy drop with subject size, top-down vs bottom-up), jump height and release-angle estimation from monocular video (methods and error), ball tracking for shot arc and entry angle from a side view, open-source basketball analysis projects on GitHub (shot detection, player tracking, pose-based shooting form scoring), and camera placement recommendations for shooting-form analysis (height, angle, distance, frame rate; phone 60/120/240 fps slow-mo). Conclude with a realistic "measure this automatically / judge this by eye / needs a second close-up camera" split.` },
  { key: 'benchmarks-shot-quality', prompt: `ANGLE 6 - Benchmarks, shot quality and the maths of shot selection for a 38% FG pickup player.
Find: expected points per shot by zone (rim, short mid-range, long two, corner three, above-break three) at NBA, college and amateur levels; the effect of defender distance (open vs tight) and dribbles before the shot (0 vs 3-6 vs 7+) on FG% from NBA tracking data; catch-and-shoot vs pull-up efficiency; the "Moreyball" argument and where long twos sit; what FG% / eFG% / TS% ranges look like for recreational and amateur players (any data: rec leagues, 3x3 amateur, HomeCourt or Dr Dish aggregated user stats, pickup studies); points-per-possession ranges in half-court; and the evidence on usage vs efficiency (take fewer, better shots). Also simple self-tracking metrics recommended for amateurs (eFG%, shot-zone mix, assisted rate, turnover rate per touch) and how a one-game sample (13 shots) should be interpreted (variance, confidence intervals).` },
  { key: 'form-rebuild-transfer', prompt: `ANGLE 7 - Rebuilding a jump shot as an adult (two-hand push, elbow flare, centred ball, two-motion rhythm) and making it survive in games.
Find: what respected shooting coaches (e.g., Dave Hopla, Chip Engelland, Dave Love, Collin Castellaw / Shot Mechanics, Drew Hanlen, Rob Fodor, the Pro Shot System / Paul Hoover's "turn and dip" and "sweep and sway", Noah's data) say about the guide hand, elbow alignment, one-motion vs two-motion, set point, the dip, and shooting off the dribble; how long a rebuild takes and typical regression under game pressure; the "form shooting then range progression" protocols with make counts; how to shoot a pull-up jumper with balance (the hop vs 1-2); and the measurable targets (arc 45-47 degrees, entry angle, depth 11 inches past the front rim, left-right within 1 inch per Noah). Include the counter-arguments (e.g., coaches who say do NOT remove the guide hand or two-motion is fine for older shooters) so the synthesis can present both.` },
]

phase('Sweep')
const sweep = await parallel(ANGLES.map(a => () =>
  agent(`${CONTEXT}\n\n${a.prompt}\n\nReturn 8-15 findings, 3-8 output_format_ideas, 3-10 drills where relevant, 3-6 "interesting" items (things that surprised you or that nobody asks for but would help), and gaps (what you could not find).`,
    { label: `research:${a.key}`, phase: 'Sweep', schema: FINDINGS_SCHEMA })))
const sweepOk = sweep.filter(Boolean)
log(`Sweep done: ${sweepOk.length}/${ANGLES.length} researchers returned`)

phase('Verify')
const lb = sweepOk.flatMap(r => r.findings.filter(f => f.load_bearing).map(f => ({ ...f, angle: r.angle })))
log(`Verifying ${lb.length} load-bearing claims`)
const verified = await parallel(lb.map((f, i) => () =>
  agent(`You are a skeptical fact-checker. Try to REFUTE this claim using WebFetch on the cited source and at least one independent WebSearch. If the source does not actually say it, or the number is wrong, or it is outdated, say so. If uncertain, prefer "partly" or "unverifiable" over "confirmed".

CLAIM: ${f.claim}
DETAIL: ${f.detail}
CITED SOURCE: ${f.source_url} (${f.source_title || ''})
CONTEXT ANGLE: ${f.angle}

Return the verdict, the evidence (quote the relevant sentence if you can), a corrected_claim if it needs correcting, and the best source_url.`,
    { label: `verify:${i}`, phase: 'Verify', schema: VERDICT_SCHEMA })))
const verdicts = verified.filter(Boolean)
const counts = verdicts.reduce((m, v) => ({ ...m, [v.verdict]: (m[v.verdict] || 0) + 1 }), {})
log(`Verify done: ${JSON.stringify(counts)}`)

phase('Critique')
const critique = await agent(`${CONTEXT}

Below are the research findings from seven angles plus fact-check verdicts. You are the completeness critic. Answer: what is MISSING that the final recommendation needs? Think about: angles not covered, claims that are all from one type of source, product features assumed rather than checked, drills without a progression, anything about the recurring-workflow design (how often, how long, what to track across games), privacy/consent for filming other players, and the amateur-specific context (older legs, limited practice time, no coach). Then RUN THE RESEARCH YOURSELF for the 5-8 most important gaps (WebSearch + WebFetch) and return them as findings.

FINDINGS:
${JSON.stringify(sweepOk, null, 1).slice(0, 120000)}

VERDICTS:
${JSON.stringify(verdicts, null, 1).slice(0, 30000)}`,
  { label: 'critic+gapfill', phase: 'Critique', schema: FINDINGS_SCHEMA })

phase('Synthesize')
const report = await agent(`${CONTEXT}

You are writing the final validated research report for Barak. Inputs: findings from seven research angles, fact-check verdicts on the load-bearing claims, and a gap-fill round. Rules:
- Where a verdict says refuted, drop or correct the claim. Where partly, state the corrected version. Where unverifiable, keep only if useful and mark it "(unverified)".
- Every substantive statement carries its source URL in Markdown link form.
- Write in plain, direct language. Short sentences. No hype. No emoji.
- Numbers go in tables where possible.

Produce a Markdown document with EXACTLY these sections:
1. "What the research says in one page" - the 10-15 most important, verified takeaways for THIS situation (wide single camera, adult pickup player, recurring workflow). 
2. "How to break down one player's offense reel" - a concrete per-possession tagging scheme (fields and allowed values) and the per-game roll-ups (tendencies, shot mix, shot quality, decision quality), adapted to what a wide camera can see. Include the recommended order of a film session / report (what goes first, positive-to-corrective ratio, one priority at a time).
3. "Feedback that changes behaviour" - cue design (external focus, short cues), frequency, summary vs immediate, self-modelling / feedforward clips, transfer to game shots, with the evidence.
4. "Drill library mapped to weakness types" - a table: weakness -> 2-3 drills with reps/sets, cue, progress test, source. Cover: shot selection/decision, pull-up balance, guide hand / elbow / one motion, finishing with contact and off hand, triple threat and first step, catch-and-shoot and relocation, passing out of the drive, rebounding, conditioning for adult legs. Then a 25-minute solo session template.
5. "Output formats, compared" - a table of every delivery format found (HTML report, captioned coaching video, annotated clip playlist, side-by-side with a model/pro, pose-skeleton overlay, shot chart / hex map, tendency report, progress tracker across games, voice-over review, short cue card, etc.): what it is, what it takes to produce with ffmpeg/Python/HTML, what evidence or expert opinion says about its effect on behaviour, and a verdict (build first / later / skip) for this situation.
6. "What a single wide camera can and cannot measure" - the measure-automatically / judge-by-eye / needs-close-up split, with the pose-estimation subject-size evidence, and a concrete camera add-on recommendation for form (height, angle, distance, fps).
7. "Benchmarks and the maths of shot selection" - expected points per shot by zone and by defender distance / dribbles, what 13 shots can and cannot tell you, what to track per game and across games.
8. "Rebuilding the jump shot as an adult" - consensus and the counter-arguments, protocol with make counts, timeline expectations, how to keep it under game pressure.
9. "Interesting extras" - 8-12 ideas nobody asked for that would genuinely help (from the researchers' "interesting" lists), each one line with a source.
10. "Sources" - full list of URLs used, grouped by section.

Length: as long as it needs to be, but dense. Aim for 2500-4500 words.

SWEEP FINDINGS:
${JSON.stringify(sweepOk, null, 1).slice(0, 140000)}

VERDICTS:
${JSON.stringify(verdicts, null, 1).slice(0, 40000)}

GAP-FILL:
${JSON.stringify(critique, null, 1).slice(0, 30000)}`,
  { label: 'synthesize-report', phase: 'Synthesize' })

return { report, sweep: sweepOk, verdicts, critique }