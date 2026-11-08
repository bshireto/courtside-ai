export const meta = {
  name: 'bb-attribute-shots',
  description: 'Name the shooter of every attempt, find the assist on every make (two independent reviewers + tie-break)',
  phases: [
    { title: 'Makes', detail: 'two independent reviewers per make: scorer, assist, play description' },
    { title: 'Tie-break', detail: 'third reviewer where the two disagree on scorer or assist' },
    { title: 'Misses', detail: 'batches of 5: shooter, real attempt or not, 2 or 3' },
  ],
}
// args: { game, work, pipe, names: [...], makes: [{id,t_through,t_release,points,xy}], misses: [{id,t_rim,t_release,points}] }
// each attempt's earlier description lives in <game>/data/attr/<id>.txt (keeps the args small)
const { game: G, work: S, pipe: P, names, makes, misses } = args
const RUN = `BB_GAME="${G}" python`
const WHO = [...names, 'unknown']

const MAKE = {
  type: 'object',
  properties: {
    id: { type: 'string' },
    scorer: { type: 'string', enum: WHO },
    scorer_confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
    assist: { type: 'string', enum: [...WHO, 'none'], description: 'the teammate whose pass led directly to the basket; none if the scorer created it himself' },
    assist_confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
    t_pass: { type: ['number', 'null'], description: 'second the assisting pass left the passer' },
    dribbles_after_catch: { type: ['integer', 'null'] },
    off_rebound: { type: 'boolean', description: 'true if the scorer (or a teammate just before) got an offensive rebound in this possession' },
    passes_before: { type: 'integer', description: 'passes by the scoring team in the 8 s before the shot (ball movement)' },
    contest: { type: 'string', enum: ['open', 'light', 'tight'] },
    kind: { type: 'string', enum: ['three', 'jumper', 'pull-up', 'layup', 'putback', 'floater', 'hook', 'bank shot', 'other'] },
    play: { type: 'string', description: 'one plain sentence, max 25 words: what happened, using the players names' },
    highlight: { type: 'integer', minimum: 1, maximum: 5, description: 'individual skill: difficulty, contest, range, finish' },
    team_play: { type: 'integer', minimum: 0, maximum: 5, description: 'assist quality, ball movement, extra pass, cut, offensive rebound + putback' },
    evidence: { type: 'string' },
  },
  required: ['id', 'scorer', 'scorer_confidence', 'assist', 'assist_confidence', 't_pass', 'dribbles_after_catch', 'off_rebound', 'passes_before', 'contest', 'kind', 'play', 'highlight', 'team_play', 'evidence'],
}
const MISS = {
  type: 'object',
  properties: {
    id: { type: 'string' },
    shooter: { type: 'string', enum: WHO },
    confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
    is_attempt: { type: 'string', enum: ['yes', 'no', 'unclear'], description: 'no = a pass / lob, a ball knocked loose before the shooting motion, a tap-out, or a dead-ball shot' },
    live: { type: 'string', enum: ['yes', 'no', 'unclear'] },
    points: { type: ['integer', 'null'], description: '2 or 3 by the feet at the release frame' },
    blocked: { type: 'boolean' },
    note: { type: 'string' },
  },
  required: ['id', 'shooter', 'confidence', 'is_attempt', 'live', 'points', 'blocked', 'note'],
}
const MISSES = { type: 'object', properties: { results: { type: 'array', items: MISS } }, required: ['results'] }

const TOOLS = `First Read ${G}\\CONTEXT.md - it has the ROSTER table (names, teams, what each player wears), the live-game windows, the court lines and the tools.
Tools (full paths, quoted):
  ${RUN} "${P}\\sheet.py" --start <s> --end <e> --fps <n> [--hires] [--crop x0,y0,x1,y1] --cols <n> --tile-w <px> --out "${S}\\views\\<unique>.jpg"
  ${RUN} "${P}\\feet_check.py" --t <release s> --xy <feet x,y> --half 90 --span 0.2 --post 0 --scale 4 --out "${S}\\views\\<unique>.jpg"   (feet vs the 3-point arc)
Without --hires sheet.py reads a 5 fps dump (instant, fps <= 5). With --hires any fps up to 30.
Name players ONLY from the roster table, by clothes and build. Two pairs are easy to mix up: the defender (bald, black T-shirt, black SHORTS, bare legs) vs the defender (bald, heavier, LONG black trousers); the defender (beard, WHITE top, black shorts, dark shoes) vs the defender (wavy grey-brown hair, black top, ORANGE shoes). In game 1 nobody wears a pinnie. If you cannot pin a player down, answer unknown rather than guessing.`

function makePrompt(m, who) {
  return `You are documenting ONE made basket in a pickup basketball video (4 on 4, half court). The ball going in is already verified - do not re-judge it.
${TOOLS}

Basket ${m.id}: ball through the net at ${m.t_through}s, released at about ${m.t_release}s${m.xy ? ` from about pixel (${m.xy.join(',')})` : ''}, ${m.points} points.
An earlier reviewer's description of the shooter and the shot is in ${G}\\data\\attr\\${m.id}.txt (Read it). Treat it as a hint, not as truth.

Do this:
1. Watch the 9 seconds before the release and 1 second after${who === 'b' ? ', starting from the release and working BACKWARDS in time' : ''}: e.g. sheet.py --start ${Math.max(0, m.t_release - 9).toFixed(1)} --end ${(m.t_release + 1).toFixed(1)} --fps 5 --cols 6 --tile-w 640, then --hires close-ups (10-15 fps, cropped around the ball) wherever a pass or a catch happens.
2. SCORER: name him from the roster.
3. ASSIST: the teammate whose pass led DIRECTLY to this basket - the scorer shot within about 4 seconds of catching it and took at most 1 dribble. A hand-off counts. No assist if he dribbled more, pump-faked and drove a long way, or scored off his own / someone's rebound without a pass (a putback has no assist). Give the time the pass left the passer's hands and the number of dribbles after the catch.
4. Describe the play in ONE plain sentence with names (max 25 words), e.g. "a teammate cuts baseline, takes a teammate's bounce pass and lays it in off the glass."
5. Score highlight (individual skill 1-5) and team_play (0-5).
Views go in ${S}\\views\\ named attr_${m.id}_${who}_*.`
}

phase('Makes')
const makeRes = await pipeline(
  makes,
  m => parallel(['a', 'b'].map(who => () => agent(makePrompt(m, who), { label: `make:${m.id}:${who}`, phase: 'Makes', schema: MAKE }))),
  async (two, m) => {
    const [a, b] = two || []
    let c = null
    const differ = !a || !b || a.scorer !== b.scorer || a.assist !== b.assist
    if (differ) {
      c = await agent(`Two reviewers documented the same made basket and disagree (or one failed). Decide from the pixels.
${TOOLS}

Basket ${m.id}: ball through the net at ${m.t_through}s, released at about ${m.t_release}s${m.xy ? ` from about pixel (${m.xy.join(',')})` : ''}, ${m.points} points.
Reviewer A: ${JSON.stringify(a)}
Reviewer B: ${JSON.stringify(b)}

Settle the SCORER and the ASSIST (assist = teammate's pass leading directly to the basket: shot within ~4 s of the catch, at most 1 dribble; hand-off counts; putbacks have no assist). Look at the catch and the pass at 10-15 fps with --hires. Fill every field. Views named attr_${m.id}_c_*.`,
        { label: `tiebreak:${m.id}`, phase: 'Tie-break', schema: MAKE, effort: 'high' })
    }
    return { id: m.id, a, b, c }
  }
)

phase('Misses')
const batches = []
for (let i = 0; i < misses.length; i += 5) batches.push(misses.slice(i, i + 5))
const missRes = await parallel(batches.map((b, bi) => () => agent(
  `You are putting a NAME on missed shot attempts in a pickup basketball video (4 on 4, half court), for a box score.
${TOOLS}

Attempts (all already judged as not going in):
${b.map(x => `- ${x.id}: ball at the rim about ${x.t_rim}s${x.t_release ? `, released about ${x.t_release}s` : ''}${x.points ? `, earlier reviewer said ${x.points}-point attempt` : ''}. Earlier description: Read ${G}\\data\\attr\\${x.id}.txt`).join('\n')}

For EACH attempt:
1. SHOOTER: name him from the roster. If the earlier description already pins down exactly one roster player (clothes match one row and no other), you may use it without rendering; otherwise look at the release (sheet.py --hires, 10 fps, cropped around the shooter).
2. is_attempt: yes for a real field-goal attempt (also a blocked shot or an airball). no for a pass / lob, a ball knocked loose before the shooting motion started, a tap-out of a rebound, or a casual dead-ball shot (after a made basket, after a foul call, players standing around).
3. points: 2 or 3 by the feet at the release frame (use feet_check.py when it is close; a foot on the line = 2).
4. live: was it live play.
Views named attr_miss_${bi}_*.`,
  { label: `misses:${b[0].id}-${b[b.length - 1].id}`, phase: 'Misses', schema: MISSES })))

const m2 = makeRes.filter(Boolean)
log(`makes ${m2.length}/${makes.length} (tie-breaks ${m2.filter(x => x.c).length}); miss batches ${missRes.filter(Boolean).length}/${batches.length}`)
return { makes: m2, misses: missRes.filter(Boolean).flatMap(r => r.results) }
