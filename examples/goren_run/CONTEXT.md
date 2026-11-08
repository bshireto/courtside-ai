# Game video context (for review agents) - Goren pickup, 6 Nov 2026

Video: `game_live.mp4` (1920x1080, 30 fps, 71:44). It is the LIVE minutes of 8 phone videos joined together. Times are seconds from its start.
Indoor school hall. The camera was a phone placed low at a corner/end of the court and it is NOT in the same place in every video;
inside one video it stays still. Players are small (60-250 px tall). Several hoops are visible in every frame (the hall has 4+ hoops).
ONLY hoop A (the one the group plays at) counts; it is listed per video below. Ignore every other hoop and any ball at another hoop.

Paths:
- GAME = `<project>\recap_2026-11-06`
- PIPE = `<project>\pipeline`
- WORK = `<project>\recap_2026-11-06\work`

## Live windows (setup = one segment of game_live.mp4 = one stretch of one source video; ALL of it is live play except dead balls)
| Setup | Source | Hoop | Seconds | Clock |
|---|---|---|---|---|
| S01 | video 1 | H1 | 0 - 423 | 0:00.0 |
| S02 | video 1 | H1 | 423 - 493 | 7:03.1 |
| S03 | video 2 | H2 | 493 - 875 | 8:13.4 |
| S04 | video 2 | H2 | 875 - 941 | 14:35.4 |
| S05 | video 3 | H3 | 941 - 1473 | 15:40.5 |
| S06 | video 4 | H4 | 1473 - 2345 | 24:32.6 |
| S07 | video 5 | H5 | 2345 - 2789 | 39:04.7 |
| S08 | video 6 | H6 | 2789 - 3294 | 46:28.8 |
| S09 | video 7 | H7 | 3294 - 3613 | 54:53.8 |
| S10 | video 7 | H7 | 3613 - 3791 | 60:12.9 |
| S11 | video 8 | H8 | 3791 - 4304 | 63:10.6 |

Dead balls still exist inside a window (ball retrieval, arguments, warm-up shots right at the start). A shot with nobody defending or
rebounding, a flip right after a basket, or a putback after a foul call is NOT a live basket. Both teams attack the same hoop; the
scoring team may keep the ball.

## Hoop A per setup (full-frame pixels)
- **H1** rim centre (798, 211) px, net hangs to y=238 (net x 785-814). the hoop with the white NETTING hanging behind it, left of the tall window (camera in the corner near the doors).
- **H2** rim centre (1092, 420) px, net hangs to y=444 (net x 1076-1101). the hoop with netting behind it, right of the tall window (camera at the other end, doors on the right).
- **H3** rim centre (898, 424) px, net hangs to y=446 (net x 891-912). the middle hoop with netting behind it, doors at the left (camera at the end near the stairs).
- **H4** rim centre (1414, 405) px, net hangs to y=430 (net x 1397-1424). the hoop right of the tall window with netting behind it (the hoop left of the window is B - ignore it).
- **H5** rim centre (914, 428) px, net hangs to y=450 (net x 905-928). the middle hoop under the netting, above the doors/mats side.
- **H6** rim centre (1498, 400) px, net hangs to y=430 (net x 1481-1510). the hoop right of the tall window with netting behind it (the hoop left of the window is B - ignore it).
- **H7** rim centre (933, 254) px, net hangs to y=302 (net x 908-953). the hoop under the white netting (closer camera, rim looks bigger; the hoop at the right edge of the frame is B - ignore it).
- **H8** rim centre (794, 364) px, net hangs to y=391 (net x 786-808). the hoop under the netting, between the doors (left) and the tall window (right); unconfirmed by Barak.
The rim is small (about 44 px wide, 69 px in video 7). The net hangs below it; behind the net is a wall or the backboard. A ball that goes
BEHIND the net can look like a make in a difference image: a make drags the net strands (net swings) and the ball exits the bottom.

## Teams and players
No pinnies. Teams are not marked and people change between games: different people play in each video, in different clothes (white / blue /
purple numbered jerseys, black tank tops, tan or white T-shirts, grey / black / white shorts). Do NOT name people. Describe the scorer
precisely in `shooter_desc` (hair or bald, beard, shirt colour and jersey number if readable, shorts, shoes, build, what he does) so the
same person can be matched later. Barak (the user) is bald, medium-heavy build, but his clothes change every week: set
`shooter_is_user` to `unclear` unless the description clearly fits. Answer `shooter_team: "unknown"`.

## Court lines (for 2 vs 3)
The 3-point arc is the big WHITE arc painted on the floor around the paint (yellow lines belong to another sport; ignore them).
Look at the shooter's feet in the release frame: both feet outside (beyond) the white arc = 3, otherwise 2. If the arc is hidden or the
feet are not visible, set `points` to null and describe where he stood. Flight time release->rim >= 1.1 s suggests a long shot.

## Tools (always prefix with the game env var)
```
BB_GAME="<project>\recap_2026-11-06" "<project>\.venv\Scripts\python" "<project>\pipeline\sheet.py" --start <s> --end <e> --fps <n> [--hires] [--crop x0,y0,x1,y1] --cols <n> --tile-w <px> --out "<project>\recap_2026-11-06\work\views\<unique>.jpg"
BB_GAME="<project>\recap_2026-11-06" "<project>\.venv\Scripts\python" "<project>\pipeline\rim_check.py" --t <rim time> --rim <x,y of the hoop> --half 35 --span 0.7 [--ref <empty-rim time>] --out "<project>\recap_2026-11-06\work\views\<unique>.jpg"
```
Read the output image with the Read tool. Use `--half 35` for these small rims (60 for video 7). Be honest: unclear / low confidence rather than guessing.
