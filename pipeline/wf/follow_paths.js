export const meta = {
  name: 'bb-follow-paths',
  description: 'Mark where the ball is through every Top 10 clip so the vertical crop can follow the action (one agent per clip)',
  phases: [{ title: 'Focus paths', detail: 'one agent per clip: annotate the ball, check the framing, fix, repeat' }],
}
// args: { game, work, pipe, clips: [{id, rank, caption}] }   - each clip has a spec file <game>/data/vpaths/<id>.json (vfollow.py init)
const { game: G, work: S, pipe: P, clips } = args
const RUN = `BB_GAME="${G}" python`

const OUT = {
  type: 'object',
  properties: {
    id: { type: 'string' },
    live_keys: { type: 'integer' },
    replay_keys: { type: 'integer' },
    worst_margin_live: { type: 'number', description: 'percent, from the last "check live" run' },
    worst_margin_replay: { type: 'number', description: 'percent, from the last "check replay" run' },
    rounds: { type: 'integer', description: 'check-look-fix rounds done (live + replay)' },
    ball_hidden: { type: 'string', description: 'time ranges where the ball could not be seen and the position was estimated' },
    notes: { type: 'string', description: 'anything the editor should know: a player cut by the frame edge that could not be avoided, etc.' },
  },
  required: ['id', 'live_keys', 'replay_keys', 'worst_margin_live', 'worst_margin_replay', 'rounds', 'ball_hidden', 'notes'],
}

phase('Focus paths')
const res = await parallel(clips.map(c => () => agent(
  `You are the camera operator for ONE basketball highlight that will be shown as a VERTICAL video. The source is a wide, fixed 1920x1080 shot of a half court; the vertical video shows only a window of it (864 px wide in the live clip, 640x800 in the slow-motion replay). A program moves that window so it follows the action. Your job: tell it, moment by moment, where the BALL is. If your marks are right, the viewer sees the passer, the catch, the shot and the ball going in; if they are wrong, the play happens outside the picture.

First Read ${G}\\CONTEXT.md (court, hoop positions and the camera of each video) and the clip's spec file:
  ${G}\\data\\vpaths\\${c.id}.json     (this is highlight #${c.rank} "${c.caption}")
It gives: "play" (what happens), "T" (second the ball goes through the net), "t_release", "t_pass" (assist pass, may be null), "shooter_xy", and two time windows in seconds of the source video: "live" {start,end} and "replay" {start,end} (the replay window lies inside the live one).

WHAT TO WRITE - edit ONLY the two lists in that file (they may hold a rough draft: replace it; keep every other field as it is):
  "live_focus":   [[t, x, y], ...]   covering live.start .. live.end
  "replay_focus": [[t, x, y], ...]   covering replay.start .. replay.end
t = seconds of the source video, x,y = pixel position of the FOCUS in the full 1920x1080 frame.
The focus is the ball. Rules:
- Ball in a player's hands or being dribbled: the ball itself (or the player's chest when the ball is hidden behind a body - say so in ball_hidden).
- Pass: one key where it leaves the passer's hands, one where it is caught. The program interpolates the flight.
- Shot: a key at the release, keys along the flight every 0.2 s, a key at the rim at T. A high shot may leave the top of the picture: still give its estimated position (y may be negative).
- After the ball drops through the net: follow it down for about 0.3 s, then HOLD the focus just under the rim (the rim position is the "rim" field of the spec file; hold about 60 px below it) until the end. Do not chase the ball when someone carries it away.
- Density: live at least one key every 0.4 s; inside the replay window one key every 0.2 s (use the same keys in both lists there). First key at or before the window start, last key at or after the window end. Positions within about 25 px are good enough; a mark 150 px off is a failure.

HOW TO SEE THE BALL
1. Frame sheets with a pixel grid (the grid numbers are source pixels):
   ${RUN} "${P}\\vfollow.py" frames ${c.id} live       (every 0.2 s; prints the sheet paths - Read all of them, in order)
   ${RUN} "${P}\\vfollow.py" frames ${c.id} replay     (every 0.1 s)
2. The ball is small (about 12 px). When you cannot find it, zoom in on the area at 10-15 fps:
   ${RUN} "${P}\\sheet.py" --start <s> --end <e> --fps 10 --hires --crop <x0,y0,x1,y1> --cols 5 --tile-w 480 --out "${S}\\views\\vp_${c.id}_<n>.jpg"
   (tiles are stamped with the time; positions inside a crop are crop offset + position in the tile divided by the tile scale). Follow the play description: know who has the ball before you look for it.

CHECK YOUR WORK (mandatory, repeat until clean)
   ${RUN} "${P}\\vfollow.py" check ${c.id} live
   ${RUN} "${P}\\vfollow.py" check ${c.id} replay
Each prints a table and writes a sheet (path at the end of the output) showing EXACTLY what the vertical video will show, one tile per moment, with a cyan ring at your focus. Read the sheet and go through every tile:
- the cyan ring sits on the ball (or on the ball handler when it is hidden). If the ring is on empty floor or on the wrong player, your key is wrong - zoom in and fix it;
- the player with the ball is fully inside the picture, not cut by the left or right edge;
- before a pass arrives the receiver is already in the picture; at the shot the shooter's whole body is in the picture;
- the rim is in the picture from about 0.3 s before the ball reaches it until the end;
- no line of the table is flagged "focus near the edge".
The camera is smoothed, so it cannot jump: if a fast pass makes it lag, add a key or move a key a little earlier. Do at least two check-look-fix rounds for live and two for replay. Do not run any render command and do not edit other files.
Return the counts, the worst margins printed by the last two checks, and honest notes.`,
  { label: `path:#${c.rank}:${c.id}`, phase: 'Focus paths', schema: OUT, effort: 'high' })))
const ok = res.filter(Boolean)
log(`paths done ${ok.length}/${clips.length}; worst live margin ${Math.min(...ok.map(r => r.worst_margin_live))}%, worst replay margin ${Math.min(...ok.map(r => r.worst_margin_replay))}%`)
return { clips: ok }
