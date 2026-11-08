export const meta = {
  name: 'bb-label-touches',
  description: 'Mark every moment the user has the ball, from user-centred 5 fps sheets (6 sheets per agent)',
  phases: [
    { title: 'Label touches', detail: 'batches of 6 user-centred sheets (36 s each)' },
  ],
}
const R = args.game  // game folder (has CONTEXT.md)
const P = args.pipe
const REF = args.ref
// args.look: one line describing the user in THIS game (his clothes change every week)
const LOOK = args.look || 'bald head, orange pinnie over NAVY/purple T-shirt, dark shorts, maroon shoes; ORANGE team'
const S = args.work
const sheets = args.sheets
if (!Array.isArray(sheets) || !sheets.length) throw new Error('args.sheets missing')
const name = s => `${S}\\usheets\\u_${String(Math.round(s * 10)).padStart(5, '0')}.jpg`

const TOUCH = {
  type: 'object',
  properties: {
    t_start: { type: 'number', description: 'seconds: first frame he has / touches the ball' },
    t_end: { type: 'number', description: 'seconds: last frame he has it (release of pass/shot, or loses it)' },
    actions: { type: 'array', items: { type: 'string', enum: ['catch', 'hold', 'dribble', 'pass', 'shot', 'offensive_rebound', 'defensive_rebound', 'steal', 'loose_ball', 'inbound', 'check_ball', 'tip', 'turnover', 'screen', 'other'] } },
    context: { type: 'string', enum: ['live_offense', 'starts_offense', 'dead_ball', 'defense', 'unclear'], description: 'live_offense = his team attacking with the ball live; starts_offense = defensive rebound/steal/inbound that starts his team\'s possession; dead_ball = retrieving the ball after a make/out of bounds, handing it to the other team, warm-up; defense = e.g. deflection while defending' },
    shot_result: { type: 'string', enum: ['make', 'miss', 'unknown', 'n/a'] },
    confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
    note: { type: 'string' },
  },
  required: ['t_start', 't_end', 'actions', 'context', 'shot_result', 'confidence', 'note'],
}
const OUT = {
  type: 'object',
  properties: {
    touches: { type: 'array', items: TOUCH },
    wrong_person: { type: 'array', description: 'time ranges where the tiles are centred on someone who is NOT the user', items: { type: 'array', items: { type: 'number' } } },
    not_visible: { type: 'array', description: 'time ranges where you could not find the user even after checking wider views', items: { type: 'array', items: { type: 'number' } } },
    summary: { type: 'string' },
  },
  required: ['touches', 'wrong_person', 'not_visible', 'summary'],
}

const batches = []
for (let i = 0; i < sheets.length; i += 6) batches.push(sheets.slice(i, i + 6))
log(`${sheets.length} sheets, ${batches.length} agents`)

phase('Label touches')
const res = await parallel(batches.map((b, bi) => () => agent(
  `You are finding every moment ONE player ("the user", Barak) touches the basketball in a pickup game video.
First Read ${R}\\CONTEXT.md and look at ${REF} (${LOOK}).

Each sheet below is 6 seconds at 5 fps (30 tiles, left-to-right, top-to-bottom, each stamped m:ss.s). Each tile is a crop centred on where a tracker thinks the user is ("~" after the time = interpolated position). Red "NOT LOCATED" tiles show the whole frame instead - look for him there.
Sheets (Read each):
${b.map(([s, loc]) => `- ${s}s to ${s + 6}s: ${name(s)}  (${loc}/30 tiles located)`).join('\n')}

For every period where the USER has the ball in his hands or touches it (catch, hold, dribble, pass release, shot, rebound, steal, tip, loose ball, inbound, check ball, turnover), return a touch with start/end times in SECONDS from video start (convert m:ss.s: 5:03.4 = 303.4). Be precise to 0.2 s. Merge continuous possession into one touch (catch -> dribble -> pass is one touch with actions [catch, dribble, pass]).
Tell apart: live offense vs dead-ball handling (picking the ball up after a basket, walking it back, handing/checking it to the other team, passing it back to the opponent) - label context accordingly.
When you are not sure whether he has the ball (ball small, hidden by his body, or the crop cuts it off), CHECK: render a wider/hi-res view with the sheet tool from CONTEXT.md, e.g.
BB_GAME="${R}" python "${P}\\sheet.py" --start <s> --end <e> --fps 10 --hires --crop <x0,y0,x1,y1 around him> --cols 5 --tile-w 400 --out "${S}\\views\\ut_${bi}_<n>.jpg"
(full-frame 5 fps views without --hires are instant). Use wider views also to decide offense vs defense and whether a shot went in.
If tiles are centred on someone else (wrong person), report the time range in wrong_person and still try to find the user in wider views for that time. Missing a real touch is worse than listing a doubtful one (mark it low confidence).`,
  { label: `touches:${b[0][0]}-${b[b.length - 1][0] + 6}`, phase: 'Label touches', schema: OUT }
).then(r => r && { range: [b[0][0], b[b.length - 1][0] + 6], ...r })))
const ok = res.filter(Boolean)
log(`done ${ok.length}/${batches.length}; touches ${ok.reduce((s, r) => s + r.touches.length, 0)}`)
return { batches: ok }
