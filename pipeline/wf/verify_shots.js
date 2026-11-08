export const meta = {
  name: 'bb-verify-shots',
  description: 'Classify every hoop-motion candidate as make/miss (first pass, blind recheck, tie-break)',
  phases: [
    { title: 'First pass', detail: 'batches of 4 candidates' },
    { title: 'Blind recheck', detail: 'independent frame-by-frame look at every make / unclear / low-confidence call' },
    { title: 'Tie-break', detail: 'third reviewer when the two disagree' },
  ],
}
// args: { game: <game folder>, work: <work folder>, pipe: <pipeline folder>, hoops: {name: {rim:[x,y], small:bool, strip_crop, ctx_crop}}, cands: [...] }
const { game: G, work: S, pipe: P, hoops: HOOPS, cands } = args
if (!Array.isArray(cands) || !cands.length) throw new Error('args.cands must be a non-empty array')
const RUN = `BB_GAME="${G}" python`

const VERDICT = {
  type: 'object',
  properties: {
    id: { type: 'string' },
    verdict: { type: 'string', enum: ['make', 'miss', 'no_shot', 'unclear'] },
    confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
    t_through: { type: ['number', 'null'] },
    t_release: { type: ['number', 'null'], description: 'exact frame the ball leaves the hands (step back frame by frame from the rim)' },
    shooter_team: { type: 'string', enum: ['orange', 'lime', 'unknown'] },
    shooter_is_user: { type: 'string', enum: ['yes', 'no', 'unclear'] },
    shooter_desc: { type: 'string' },
    shot_type: { type: 'string' },
    points: { type: ['integer', 'null'], description: '2 or 3 from the shooter feet vs the arc at the release frame' },
    shooter_xy: { type: ['array', 'null'], items: { type: 'number' } },
    live_game: { type: 'string', enum: ['yes', 'no', 'unclear'], description: 'no = warm-up / shootaround / dead-ball putback after a make / between games' },
    highlight: { type: 'integer', minimum: 1, maximum: 5 },
    team_play: { type: 'integer', minimum: 0, maximum: 5, description: 'assist quality / ball movement / fast break / extra pass / offensive-rebound putback' },
    evidence: { type: 'string' },
  },
  required: ['id', 'verdict', 'confidence', 't_through', 't_release', 'shooter_team', 'shooter_is_user', 'shooter_desc', 'shot_type', 'points', 'shooter_xy', 'live_game', 'highlight', 'team_play', 'evidence'],
}
const BATCH = { type: 'object', properties: { results: { type: 'array', items: VERDICT } }, required: ['results'] }

const COMMON = `First Read the briefing ${G}\\CONTEXT.md (camera, hoop positions, how to recognise the user, tools).
MAKE vs MISS is decided frame by frame, not by impression. For every rim moment run the rim tool:
  ${RUN} "${P}\\rim_check.py" --t <rim time> --rim <x,y of the hoop> --half <60 normal / 35 small hoop> --span 0.7 --out "${S}\\views\\<name>.jpg"
It shows every 30 fps frame plus a difference row (ball = bright blob). MAKE = blob goes INSIDE the net outline, the net lights up/swings, ball exits the bottom opening. MISS = blob leaves sideways/upward or falls beside an unchanged net. Widen --span or change --ref if needed.
Release: step back from the rim moment until the ball leaves the hands; 2 vs 3 = feet vs 3-point arc at that frame (flight time >= ~1.1 s suggests a long shot).
Also judge whether it is a LIVE game basket (not warm-up, shootaround, dead-ball putback right after a make, or between games).
Wider views: ${RUN} "${P}\\sheet.py" --start <s> --end <e> --fps <n> [--hires] [--crop x0,y0,x1,y1] --cols <n> --tile-w <px> --out "${S}\\views\\<name>.jpg"
Be honest: unclear/low confidence rather than guessing.`

function info(c) {
  const h = HOOPS[c.hoop]
  return `- ${c.id}: hoop=${c.hoop} (rim ${h.rim.join(',')}${h.small ? ', SMALL' : ''}), motion ${c.start}s-${c.end}s (peak ${c.peak_t}s, ${c.src.join('+')}).
  rim strip: ${S}\\shots\\${c.id}_hoop.jpg   context: ${S}\\shots\\${c.id}_ctx.jpg`
}
function needsRecheck(v) {
  if (!v) return true
  if (v.verdict === 'make' || v.verdict === 'unclear') return true
  if (v.verdict === 'miss' && v.confidence !== 'high') return true
  return v.verdict === 'no_shot' && v.confidence === 'low'
}

const batches = []
for (let i = 0; i < cands.length; i += 4) batches.push(cands.slice(i, i + 4))
log(`${cands.length} candidates in ${batches.length} batches`)

const out = await pipeline(
  batches,
  batch => agent(`You are verifying possible basketball shots in a game video.\n${COMMON}\n\nCandidates:\n${batch.map(info).join('\n')}\n\nReturn one verdict per candidate (same id). If a window holds several shots judge the one nearest the peak and mention the others (with times) in evidence. Views go in ${S}\\views\\ named ${batch[0].id}_*.`,
    { label: `pass1:${batch[0].id}-${batch[batch.length - 1].id}`, phase: 'First pass', schema: BATCH }),
  async (res, batch) => {
    const byId = {}
    for (const r of (res && res.results) || []) byId[r.id] = r
    return parallel(batch.map(c => async () => {
      const first = byId[c.id] || null
      if (!needsRecheck(first)) return { cand: c, first, second: null, third: null }
      const second = await agent(`Independently re-check ONE possible basketball shot. Ignore earlier opinions; decide from the pixels.\n${COMMON}\n\nCandidate:\n${info(c)}\n\nMandatory: run rim_check.py across the rim moment and look at the ~5 s after it. Views named ${c.id}_r2_*.`,
        { label: `recheck:${c.id}`, phase: 'Blind recheck', schema: VERDICT })
      let third = null
      const a = first ? first.verdict : 'unclear', b = second ? second.verdict : 'unclear'
      if ((a === 'make') !== (b === 'make') || (a === 'unclear' && b === 'unclear')) {
        third = await agent(`Two reviewers disagree whether a basketball shot went in. Break the tie from the pixels.\n${COMMON}\n\nCandidate:\n${info(c)}\n\nReviewer 1: ${JSON.stringify(first)}\nReviewer 2: ${JSON.stringify(second)}\n\nRun rim_check.py yourself (try --span 1.0 and a tighter --half). Views named ${c.id}_r3_*.`,
          { label: `tiebreak:${c.id}`, phase: 'Tie-break', schema: VERDICT, effort: 'high' })
      }
      return { cand: c, first, second, third }
    }))
  }
)
const flat = out.filter(Boolean).flat().filter(Boolean)
function finalVerdict(x) {
  if (x.third) return x.third.verdict
  if (!x.second) return x.first ? x.first.verdict : 'unclear'
  if (x.first && x.first.verdict === x.second.verdict) return x.first.verdict
  return (x.second.verdict === 'make' || (x.first && x.first.verdict === 'make')) ? 'disputed' : x.second.verdict
}
const summary = flat.map(x => ({ id: x.cand.id, hoop: x.cand.hoop, peak_t: x.cand.peak_t, final: finalVerdict(x), first: x.first, second: x.second, third: x.third }))
log(`done: ${summary.length} candidates, ${summary.filter(s => s.final === 'make').length} makes`)
return { summary }
