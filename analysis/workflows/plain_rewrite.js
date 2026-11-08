export const meta = {
  name: 'bball-review-plain-language',
  description: 'Rewrite every insight of the verified offense report in plain language (no basketball lingo, nothing assumed), then verify no number, name, clip reference or claim changed',
  phases: [
    { title: 'Rewrite', detail: 'one writer per block of the report' },
    { title: 'Verify', detail: 'one checker per block compares original vs rewrite' },
    { title: 'Glossary', detail: 'terms that still appear, explained' },
  ],
}

const A = '<project>/analysis_2026-10-07'
const REPORT = `${A}/results/report.json`
const DRILLS = `${A}/drills.json`

const RULES = `
WHO READS THIS: Barak, the player himself. He is an adult who plays pickup basketball once a week. He was NOT part of the analysis and he does not know coaching vocabulary. His instruction: "write in a way I don't need to guess what you meant; explain as you assume I wasn't part of the thinking process or have advanced basketball lingo." And: the analysis must be IN HEBREW.

LANGUAGE: Write everything in natural, plain Hebrew, addressed to him directly in the masculine second person ("אתה", "שלך"). Keep an English basketball term only where it is the word Israeli players actually use and Hebrew has no natural equivalent (floater, pull-up, layup, closeout, catch-and-shoot, screen, pick-and-roll, assist, hook, step-back, euro-step, runner, jump shot is fine as "זריקה מקפיצה"); write such a term in English letters and explain it in plain Hebrew the first time it appears in that field, e.g. "floater (זריקה ברגל אחת שמרחפת גבוה מעל היד של המגן)". Player names in Hebrew: Barak = ברק, the defender = המגן, the defender = המגן, the defender = המגן, the defender = המגן, a teammate = חבר לקבוצה, a teammate = חבר לקבוצה, a teammate = חבר לקבוצה, a teammate = חבר לקבוצה. Numbers stay as digits (0 מתוך 7, 38%, 0:42). Shot ids (c007, s011) and clip numbers stay as they are.

HOW TO WRITE:
- Plain words. Every basketball term is either replaced by plain language or explained in a few words the first time it appears in that field. Examples: "sag" -> "stands well off you (two metres away)"; "check-ball / off the check" -> "the restart at the top of the key, when the defender hands you the ball after a score"; "closeout" -> "the defender running out at you"; "pull-up" -> "a jump shot straight after dribbling"; "catch-and-shoot" -> "a shot straight off the catch, no dribble"; "runner / floater" -> "a one-foot shot that floats high over the defender"; "long two" -> "a two-point shot from far out, just inside the three-point line"; "eFG%" -> "shooting percentage with a three counted as one and a half makes"; "points per shot" -> "how many points each shot attempt earned on average"; "hockey assist" -> "the pass before the assist"; "bail-out pass" -> "a pass made only because the drive was going nowhere"; "set defender" -> "a defender already standing in position, feet planted"; "gather" -> "the moment you pick the ball up to shoot"; "hitch" -> "a pause in the middle of the shooting motion"; "guide hand" -> "the left hand, the one that only steadies the ball"; "one count" -> "within about one second"; "drift / fade" -> "jumping sideways or backwards instead of straight up"; "outlet" -> "the first pass after a rebound"; "putback" -> "catching a missed shot near the basket and shooting again at once"; "kick-out" -> "passing out to a teammate on the perimeter while you are inside"; "paint / lane" -> "the painted rectangle under the basket"; "elbow" -> "the corner of the free-throw line"; "top of the key / top of the arc" -> "the spot straight out from the basket, at the three-point line"; "ISO" -> "one on one"; "contest / contested" -> "a defender's hand in your face when you shoot".
- Keep EVERY fact exactly: every number, count, percentage, time, clip number, shot id (c007, s011 ...), player name, and the direction of every claim. Do not add facts, do not soften or strengthen a claim, do not drop a clip reference. If the original says "0 of 7", the rewrite says "0 of 7".
- Shot ids like c007 stay (they match the shot chart), but say what they are the first time: "shot c007 (the first shot of the night, 0:08 in the reel)". Reel times are minutes:seconds in his offense reel; write them as 0:42 not 42.6 when they appear in prose, keep the exact seconds in teaching_frames/reel_time fields untouched (do not change numeric fields).
- Keep the structure and field names exactly as given; return the same JSON shape with the text fields rewritten. Do not rewrite enum values (keep / cut / partly / good ...), numeric fields or clip lists.
- Sentences short. "You" for Barak, defenders and teammates by name (the defender, the defender, the defender, the defender, a teammate, a teammate, a teammate, a teammate). No praise inflation.
- Captions (teaching_moments.caption) stay at most 12 Hebrew words and still make sense on their own on a video frame.
`

const BLOCKS = [
  { key: 'summary', fields: ['headline', 'stat_context', 'one_thing'], note: 'headline <= 45 words; one_thing one sentence; stat_context keeps every number and the six numbered "calls I made" items.' },
  { key: 'fixes', fields: ['priority_fixes'], note: 'each fix: what (one or two sentences, the instruction), why_it_matters_most, cue (<= 15 words, something he can say to himself on the court), what_good_looks_like.' },
  { key: 'strengths', fields: ['strengths'], note: 'title <= 8 words, detail with every clip reference kept.' },
  { key: 'weaknesses', fields: ['weaknesses'], note: 'title <= 10 words, detail, how_often verbatim counts.' },
  { key: 'tendencies', fields: ['tendencies'], note: 'tendency text plain; numbers field verbatim except expanding abbreviations like FG/AST/TO (field goal, assist, turnover).' },
  { key: 'shots', fields: ['shot_by_shot'], note: 'zone, type, contest, result, note in plain words; quality_1to5 and verdict untouched.' },
  { key: 'moments-targets', fields: ['teaching_moments', 'next_game_targets'], note: 'captions <= 12 Hebrew words, plain; targets: metric names explained, this_game/target values verbatim.' },
]

const DRILL_FIELDS = ['name', 'how', 'reps', 'cue']

phase('Rewrite')
const rewrites = await parallel([
  ...BLOCKS.map(b => () => agent(`${RULES}

TASK: Read ${REPORT} (Read tool). Rewrite ONLY these top-level fields in plain language: ${b.fields.join(', ')}. ${b.note}
Return a JSON object (as your final text, nothing else, no code fences) with exactly those top-level fields, same shapes as in the file, text rewritten, all other sub-fields copied verbatim.`,
    { label: `rewrite:${b.key}`, phase: 'Rewrite' })),
  () => agent(`${RULES}

TASK: Read ${DRILLS} (Read tool). Rewrite the text fields of every drill (${DRILL_FIELDS.join(', ')}), every "session", "partner_session" and "game_rules" entry and "notes" in plain language. Keep mode, source, url, rank, min and the structure verbatim.
Return the full JSON object (as your final text, nothing else, no code fences) with the same shape.`,
    { label: 'rewrite:drills', phase: 'Rewrite' }),
])
const parse = s => { try { const t = String(s).trim().replace(/^```(?:json)?\s*/i, '').replace(/```\s*$/, ''); return JSON.parse(t) } catch (e) { return null } }
const drafts = rewrites.map(parse)
log(`Rewrite done: ${drafts.filter(Boolean).length}/${rewrites.length} parsed`)

phase('Verify')
const VERDICT = {
  type: 'object',
  properties: {
    faithful: { type: 'boolean' },
    problems: { type: 'array', items: { type: 'string' } },
    corrected_json: { type: 'string', description: 'the full corrected JSON for the block (same shape), or "" if faithful' },
  },
  required: ['faithful', 'problems', 'corrected_json'],
}
const checks = await parallel(drafts.map((d, i) => () => {
  if (!d) return Promise.resolve(null)
  const isDrills = i === BLOCKS.length
  const src = isDrills ? DRILLS : REPORT
  const fields = isDrills ? 'all drill text fields' : BLOCKS[i].fields.join(', ')
  return agent(`You are checking a plain-language rewrite of a verified basketball report for FAITHFULNESS. Read the original ${src} (Read tool) and compare the fields ${fields} with the rewrite below. A rewrite is faithful when every number, count, percentage, time, clip number, shot id, player name and the direction of every claim is preserved, nothing was added, nothing dropped, numeric fields and enum values are untouched, and the shape is identical. Plain wording and explanations of terms are expected and fine.
If anything drifted, fix it yourself: return the corrected JSON for the whole block in corrected_json (keep the plain wording, restore the facts). If it is faithful, return corrected_json = "".
Also check the language: the rewrite must be in plain Hebrew (English only for accepted lingo such as floater, pull-up, layup, closeout, explained once); any unexplained term, any English sentence or any transliteration mistake in a player name is a problem (list it) and fix it in corrected_json.

REWRITE:
${JSON.stringify(d, null, 1).slice(0, 60000)}`, { label: `verify:${isDrills ? 'drills' : BLOCKS[i].key}`, phase: 'Verify', schema: VERDICT })
}))
const finals = drafts.map((d, i) => {
  const c = checks[i]
  if (c && c.corrected_json) { const fixed = parse(c.corrected_json); if (fixed) return fixed }
  return d
})
const tally = checks.filter(Boolean).reduce((m, c) => ({ ...m, [c.faithful ? 'faithful' : 'corrected']: (m[c.faithful ? 'faithful' : 'corrected'] || 0) + 1 }), {})
log(`Verify done: ${JSON.stringify(tally)}`)

phase('Glossary')
const GLOSSARY = {
  type: 'object',
  properties: { terms: { type: 'array', items: { type: 'object', properties: { term: { type: 'string' }, meaning: { type: 'string' } }, required: ['term', 'meaning'] } } },
  required: ['terms'],
}
const glossary = await agent(`Below is a basketball offense review written for an adult pickup player who does not know coaching vocabulary. List the 15-30 basketball terms that still appear anywhere in it (even if explained once) with a one-sentence plain HEBREW meaning each (term field: the term as it appears, e.g. 'floater' or 'צ'ק בול (check-ball)'), so the review can show a glossary in Hebrew. Include: restart at the top (check-ball), three-point line / arc, the paint, free-throw line, elbow (of the free-throw line), wing, corner, jump shot after a dribble (pull-up), shot off the catch, runner, layup, rebound, outlet pass, assist, turnover, contest, defender standing off you, shooting percentage with threes weighted (eFG%), points per shot, possession, drive, screen, hand-off, lob, kick-out pass, and any other term you find.

REVIEW TEXT:
${JSON.stringify(finals.slice(0, BLOCKS.length), null, 1).slice(0, 70000)}`, { label: 'glossary', phase: 'Glossary', schema: GLOSSARY })

const report_plain = {}
finals.slice(0, BLOCKS.length).forEach((d, i) => { if (d) for (const f of BLOCKS[i].fields) if (d[f] !== undefined) report_plain[f] = d[f] })
return { report_plain, drills_plain: finals[BLOCKS.length], glossary: glossary?.terms || [], tally, problems: checks.filter(Boolean).flatMap(c => c.problems).slice(0, 40) }
