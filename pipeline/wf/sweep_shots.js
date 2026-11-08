export const meta = {
  name: 'bb-sweep-shots',
  description: 'Watch the whole game in 45 s windows and log every shot attempt (independent second route to the makes)',
  phases: [{ title: 'Sweep', detail: 'one agent per 45 s window' }],
}
// args: { game, work, pipe, setups: [{name,start,end,hoops}], hoops: {name:{rim, small}} }
const { game: G, work: S, pipe: P, setups, hoops } = args
const RUN = `BB_GAME="${G}" python`
const windows = []
for (const su of setups) for (let t = Math.ceil(su.start); t < su.end; t += 42) windows.push([t, Math.min(t + 45, Math.floor(su.end)), su])

const SHOT = {
  type: 'object',
  properties: {
    t_release: { type: 'number' }, t_rim: { type: ['number', 'null'] },
    hoop: { type: 'string' }, result: { type: 'string', enum: ['make', 'miss', 'unclear'] },
    confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
    shooter_team: { type: 'string', enum: ['orange', 'lime', 'unknown'] },
    shooter_is_user: { type: 'string', enum: ['yes', 'no', 'unclear'] },
    live_game: { type: 'string', enum: ['yes', 'no', 'unclear'] },
    note: { type: 'string' },
  },
  required: ['t_release', 't_rim', 'hoop', 'result', 'confidence', 'shooter_team', 'shooter_is_user', 'live_game', 'note'],
}
const OUT = {
  type: 'object',
  properties: {
    window: { type: 'array', items: { type: 'number' } },
    shots: { type: 'array', items: SHOT },
    user_touches: { type: 'array', items: { type: 'object', properties: { t_start: { type: 'number' }, t_end: { type: 'number' }, action: { type: 'string' }, confidence: { type: 'string' } }, required: ['t_start', 't_end', 'action', 'confidence'] } },
    play_summary: { type: 'string', description: 'what happens: live play / warm-up / break / which team attacks' },
  },
  required: ['window', 'shots', 'user_touches', 'play_summary'],
}
phase('Sweep')
const results = await parallel(windows.map(([a, b, su]) => () => {
  const sheets = []
  for (let t = a; t < b; t += 6) sheets.push(`${RUN} "${P}\\sheet.py" --start ${t} --end ${Math.min(t + 6, b)} --fps 2 --cols 3 --tile-w 640 --out "${S}\\views\\sweep_${a}_${t}.jpg"`)
  const hs = su.hoops.map(h => `${h} (rim ${hoops[h].rim.join(',')}${hoops[h].small ? ', small' : ''})`).join(', ')
  return agent(`Log every SHOT ATTEMPT in the ${b - a}-second window ${a}s-${b}s of a pickup basketball video (camera setup ${su.name}, ${su.court} court; hoops: ${hs}).
First Read ${G}\\CONTEXT.md.
1. Watch the window at 2 fps - render and Read these sheets in order:
${sheets.join('\n')}
2. For anything shot-like, zoom in (--hires 10-30 fps with a --crop around shooter and rim), and decide make/miss with
   ${RUN} "${P}\\rim_check.py" --t <rim time> --rim <x,y> --span 0.7 --out "${S}\\views\\sweep_${a}_<n>.jpg"
3. Record EVERY attempt (makes, misses, blocks, tips, putbacks, free throws) - missing an attempt is worse than listing a doubtful one. Say whether it is live game play. Also note moments the user has the ball.`,
    { label: `sweep:${a}-${b}`, phase: 'Sweep', schema: OUT })
}))
const ok = results.filter(Boolean)
log(`windows ${ok.length}/${windows.length}; shots ${ok.reduce((s, r) => s + r.shots.length, 0)}`)
return { windows: ok }
