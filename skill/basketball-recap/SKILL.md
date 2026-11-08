---
name: basketball-recap
description: Turn a pickup-basketball game video into (1) an every-basket recap with replays, (2) a Top 10 countdown (landscape + a vertical cut whose frame follows the ball, with music), (3) Barak's personal offense reel with live stat pop-ups and a stats closer, and (4) a per-player stats closer. Run step by step in-session. Trigger on "/basketball-recap", "recap this game", "new game video".
---

# Basketball recap workflow

Pipeline code: `<project>\pipeline\`
(python venv: `...\basketball_analysis\.venv`; ffmpeg on PATH). First reference game: `...\recap_2026-09-23\`
(`game.json`, `data/`, `research_style_guide.md` = the edit spec, `tools/CONTEXT.md` = reviewer briefing example).

Argument: path to the video (and optional reference screenshots of Barak). Create a game folder
`basketball_analysis\recap_<YYYY-MM-DD>\` and run everything with `BB_GAME=<game folder>`.

## Non-negotiable rules (learned from the first game)

1. **Rim truth is by frame, never by vote.** For EVERY candidate make, and for every shot Barak takes, run
   `pipeline/rim_check.py` (every 30 fps frame around the rim, tight upscaled crop + difference-vs-empty-rim row)
   and look at it yourself. Make = the ball blob goes *inside* the net outline, the net lights up/swings and the ball
   leaves through the bottom opening. Miss = blob leaves sideways/up or drops beside an unchanged net. Agent
   reviewers (even 2–3 agreeing) got 3 of the first game's featured shots wrong. Do not ask Barak to judge shots —
   extract more frames (wider span, tighter `--half`, different `--ref`) until it is certain. If the rim is truly
   blocked (player in front), say so and use the rebound/restart flow as secondary evidence.
1b. **2 vs 3 is decided at the release frame, not from the reviewer's description.** Find the exact release
   (ball leaving the hands — step back frame by frame from the rim moment; agents placed both of Barak's first-game
   threes ~1 s late, at a cut into the lane, and called them 2s). Then (a) look at the shooter's feet vs. the
   3-point arc in that frame (map the arc once per setup: mark arc points in a still and store them in game.json),
   and (b) sanity-check with flight time: release→rim ≥ ~1.1 s is a long shot; ≤ 0.6 s is at the rim.
   If feet and flight time disagree, zoom in more before deciding.
2. **Only live game baskets.** Exclude warm-ups, shootaround in breaks, dead-ball putbacks after a make,
   between-games shooting. Check the play context around every make.
3. **No team score/tally overlay** (no "ORANGE 4 LIME 2"). Label baskets by number/shooter only.
4. **Top 10** (not 5). Rank by: team play first (assist quality, ball movement, fast break, extra pass, offensive
   rebound + putback), then individual skill (difficulty, contest, range, finish). Show the Top 10 list with
   timestamps to Barak before the final render.
5. **Personal reel plays each possession to its end**: clip runs from 2 s before his first touch to 1.5 s after the
   result of the next shot (his or a teammate's, within 10 s of his last touch), max 20 s.
6. **Personal reel pop-ups**: every basket/assist he makes pops top-right for 3 s ("+2 PTS" / "+3 PTS" / "ASSIST")
   with his running line ("BARAK  4 PTS  3 AST"), then disappears (`pipeline/reel_events.py`).
7. **Stats closers**: 10 s card at the end of Barak's reel; one card per player at the end of the every-basket
   recap, with the player's photo (`pipeline/stats_card.py`). Averages/percentages only over the time a player was
   actually on court; games he sat out don't count.
8. Deliver phone copies under 30 MB via SendUserFile, WhatsApp copies under 180 MB, full-quality in `output/`.
9. **Every vertical video follows the ball.** The vertical frame shows less than half of the wide shot, so its window
   must pan with the ball and the action: passer, catch, shooter at the release, ball into the rim. A fixed crop is
   never delivered (Barak rejected it on 09.10.2026: "doesn't catch the whole action. I expect the trim to move with
   the ball/action of the game and not be static"). Use step 7b; `render_vertical.py` (the fixed crop) refuses to run.

## How to run (all scripts read `game.json` via `BB_GAME`)

Every command: `BB_GAME="<game folder>" <python> "<pipeline>\<script>.py" ...`, run from the game folder
(`<python>` = `..\.venv\Scripts\python` for torch/YOLO/sklearn steps, plain `python` for the rest).
Workflow scripts (Workflow tool, `scriptPath`): `pipeline\wf\verify_shots.js`, `sweep_shots.js`, `label_touches.js`,
`attribute_shots.js`, `follow_paths.js` — args `{game, work, pipe, ...}` (see each file's header). Keep these files LF-only (CRLF makes the Workflow
tool refuse them: "control characters hidden in the approval dialog"). Half-court dry run folder: `recap_2026-09-23_half`.

## Steps

1. **Setup** — ffprobe the video; 1 fps keyframe contact sheets; find camera moves (frame-difference spikes) and
   define `setups` + hoop pixel positions (rim, net, ROI) in `game.json` (schema in `pipeline/bbconfig.py`).
   Write the game's `CONTEXT.md` briefing (copy `recap_2026-09-23_half\CONTEXT.md`, update setups/hoops/looks).
2. **Frames + signals** (background) — 5 fps frame dump to `work/f5`; `hoop_features.py` → `shot_candidates.py`
   → `build_shot_strips.py`; `track_players.py` (YOLO11s OpenVINO + ByteTrack, model in `pipeline/models`).
3. **Makes** — `wf/verify_shots.js` on all candidates AND `wf/sweep_shots.js` (every 45 s window);
   `merge_makes.py verify_raw.json sweep_raw.json`. Then the **net-swing test** (`net_swing.py`) on every called
   make AND every sweep attempt: score = net movement 0.25–0.75 s after the rim moment ÷ pre-shot noise.
   First game calibration: all real makes ≥ 2.8, all known misses ≤ 2.1 (incl. Barak's 7:38 and the 11:01 putback,
   which 2 agent reviewers had called makes). ≥ 2.5 make · ≤ 2.1 miss · in between → look at `rim_check.py` yourself.
   A "swish" that barely moves the net passed in front of / behind it. Then rule 2: mark live-play windows from the
   sweep's play summaries and drop anything outside them.
4. **Players** — `players.py embed` then `players.py ask`: builds numbered naming sheets (`WORK/naming_sheet_*.jpg`),
   one tile per tracker segment (a stretch where one person was tracked continuously, so each tile is normally one
   person), 3 crops per tile. Then `naming_page.py` → `<game>\player-naming-decision-map.html` (decision-map
   format: one card per tile, name field with suggestions, Mixed / Don't know, Generate Summary). Auto-open it and
   SendUserFile it — never ask for names in chat or as loose JPGs. Parse his pasted summary ("Decision n … Choice:
   name"; drop mixed/skip) into `players.py learn '{"1":"Name",...}'`, which trains the player classifier, labels every detection and stores each
   player's crops in `pipeline/players/<name>_train.npz`, so the next game starts already recognising them
   (on later games only ask about tiles the classifier can't place). Appearance clustering alone MIXES players
   (same pinnies) — never name players from `cluster`. Then build per-player stat cards.
5. **Barak** — `orange_crops.py embed` → `user_clf.py apply` (stored model, no labelling) → `timeline` →
   `user_sheets.py` → `wf/label_touches.js`; his shots/assists get rule 1 + 1b individually.
   Minutes = time on court in live-play windows only.
   ⚠ Touch labelling misses shots when the tracker drifts to another player (dry run: 3 of 5 Barak shots lost,
   exactly inside the labellers' `wrong_person` ranges). His shot list = UNION of (touches with a shot) + every
   verify/sweep attempt with `shooter_is_user` yes/unclear + any attempt inside a `wrong_person`/`not_visible`
   range — look at each one, then add the missing reel clips (shot −3 s … result +1.5 s).
6. **Stats** — per player (basic set, expand over time): minutes, points, FG made/att & %, 3PT made/att & %,
   2PT made/att & %, assists. Assist = his pass directly leads to a made basket within ~4 s with ≤1 dribble by the
   scorer. (Candidates for later: offensive rebounds, steals, turnovers, blocks.)
7. **Render** — `render_v2.py recap` (every basket, replays per style guide, no tally) + per-player stat cards;
   `render_v2.py top5` with 10 entries (list shown to Barak first) + music (royalty-free, credit on end card);
   `render_v2.py reel` + `reel_events.py` + Barak's stats card.
7b. **Vertical Top 10 that follows the ball** (rule 9; needs the landscape `top5` render first, about 25 min in all):
   1. `vfollow.py init data/top10.json` → one spec per play in `data/vpaths/<id>.json` (live + replay time windows).
   2. Workflow `wf/follow_paths.js`, args `{game, work, pipe, clips: [{id, rank, caption}, ...]}` (one agent per play,
      ~10 min): each marks where the ball is through the play (`live_focus` / `replay_focus` keyframes) and repeats
      `vfollow.py check <id> live|replay` until the framing is clean.
   3. Look at every `WORK/vpath/<id>_live_check.jpg` and `<id>_replay_check.jpg` yourself (they show exactly what the
      vertical video will show): the ring sits on the ball, the passer and the receiver are in the picture, the whole
      shooter is in the picture at the release, the rim is in the picture before the ball gets there. An edge warning
      is acceptable only when the ball is at the edge of the SOURCE frame (passer in the corner, top of a three's arc).
   4. `render_vertical_follow.py data/top10.json output/Top10_Baskets_Vertical.mp4` → builds the portrait cards,
      cuts every play with the moving window, adds music, writes the `_WhatsApp.mp4` copy (~27 MB). It stops with a
      message if any play has no ball path. `--only <id>` re-renders one play after a path fix.
   The YOLO ball boxes in `tracks.jsonl` cannot replace step 2 (a lamp is detected as the ball in most frames).
   Any other vertical video (a vertical reel, a single clip) uses the same three tools: spec + ball path + moving window.
8. **QA** — decode check, sample frames of every output, phone copies, SendUserFile, auto-open. For the vertical cut:
   sample a frame every ~2 s and confirm the picture moves with each play (not the same crop from start to end).

## Added after the 07.10.2026 game (`recap_2026-10-07`, one fixed side-on half-court camera, 4 on 4, 9 players)

- **Live windows from Barak.** When he gives time ranges, make each range one `setup` in `game.json` (same hoop in all of them);
  `shot_candidates.py`, tracking and the sweep then ignore everything else. `game.json` `"plain_players": true` keeps players
  without a pinnie (a game with no pinnies, or a pinnie rolled round the neck).
- **Strand test = rule 1 in numbers** (`pipeline/net_strands.py`). A ball dropping BEHIND the net shows through the mesh and
  lights up a difference image, so reviewers call it a make (5 of 42 reviewer "makes" in this game, two and three reviewers
  agreeing). The test measures whether net strands themselves went dark: real makes peak >= 0.19 and hold >= 4 frames (most
  >= 9); behind-the-net misses peak <= 0.16 for <= 1 frame; a ball in FRONT of the net peaks ~0.3 but is back to exactly 0
  within 4 frames. Run it on every called make AND on every reviewer miss (a miss with a moving net = net hit from outside
  or a head in front; look at it). Still look at every make yourself (`rim_check.py`, then a 5x zoom with `sheet.py --hires`).
- **Dead-ball makes**: a flip right after a basket, a putback after a foul call, or a defender scoring a rebound without
  clearing are not baskets. The restart tells you: in make-it-take-it the scoring team keeps the ball.
- **Dead-ball shots by Barak too**: after a stoppage and an argument, a lone shot from the top with nobody defending or
  rebounding is a shot to settle possession, not a field-goal attempt (29:39 here; the touch labeller marked it dead_ball).
  Check the context of every shot on his list, not only the makes.
- **Roster by eye when the tiles are mixed** (`pipeline/roster_page.py`). In a crowded half court the tracker ids jump between
  people and `players.py ask` tiles mix 2-3 players. Instead: find clean frames (many tall, non-overlapping boxes), write
  `data/roster.json` (one entry per REAL person, picks = [second, index left-to-right]) and build the naming page from it.
  Put the named roster table in `CONTEXT.md` right away so every later reviewer uses names.
- **Barak in different clothes** (`pipeline/body_colors.py` + `pipeline/user_clf2.py`). The stored classifier knows last game's
  outfit. Label ~1,900 crops with a two-labeller workflow (40 sheets of 48, keep only where both agree), train DINOv2 +
  clothing-colour histograms: precision 0.96 / recall 0.93 (embedding alone: 0.85 / 0.88). `game.json` `user.setups` lists
  the windows he plays in; `label_touches.js` takes `args.look`.
- **Name every shot + assists** (`pipeline/wf/attribute_shots.js`): two independent reviewers per make (scorer, assist, one-line
  play, skill and team-play scores), tie-break on disagreement, misses in batches of 5. Descriptions go in `data/attr/<id>.txt`
  so the args stay small.
- **Union of attempts**: match the two routes on RELEASE time (<= 0.75 s), not rim time: a blocked shot 1.3 s before a putback
  was swallowed by a 1.6 s rim match. A lob that the scorer catches is an assist, never also a missed shot (check that the
  same ball is not in both lists).
- **2 vs 3** (`pipeline/feet_check.py --t <release> --xy <feet>`): raw frames plus the arc from `game.json` drawn over them.
- **Top 10 approval page** (`pipeline/top10_page.py`): cut a clip per candidate into `output/top10_preview/`, 10 picks + ~6
  alternates, recommended choices pre-selected. Barak moved a spectacular solo finish to #1 and his own pull-up three to #3
  above assisted plays, so do not rank team play mechanically first.
- **Stats cards**: `stats_card.py <json> <out> [seconds]` now encodes like `render_v2.ENC`, so cards join without re-encoding
  (6 s per player after the recap, 10 s for Barak's reel). `render_v2.py` labels baskets `BUCKET n  NAME`.
- **Shareable box score** (`pipeline/stats_poster.py`, after `data/stats.json` exists): one vertical 1080x1920 image, leader chips
  (top scorer, best FG%, most threes, most assists) over a table of every player, `output/Box_Score_Vertical.png`. Pick front-facing,
  pinnie-on avatars in `data/poster_photos.json` (`t`, `idx` from `roster_frame.py`, `cx` = where the head is). Barak asked for it
  after the videos: make it by default and send it with the phone copies.
- **Vertical cut follows the ball** (rule 9, step 7b): `vfollow.py` (virtual camera: lead room toward the basket, smoothing that
  anticipates a pass, focus kept within the middle half of the window), `wf/follow_paths.js`, `render_vertical_follow.py`.
  The first version for this game used a fixed 4:5 crop centred between rim and shooter and lost passers and three-point shooters.
- **Long runs**: workflows stop at a usage limit; in the same session `resumeFromRunId` replays finished agents, otherwise
  relaunch with only the missing items (journals: `.../subagents/workflows/<run>/journal.jsonl`). Keep a `RESUME.md` in the game folder.

## Added after the 06.11.2026 goren games (`recap_2026-11-06`, 8 phone videos, 94 min, different players each video, camera moved between videos)

- **Several videos = one joined file.** Cut each live stretch with `-c copy`, concat into `game_live.mp4`, one `setup` per stretch,
  `data/live_segments.json` maps back to source video + time. Barak's live rule: live starts when 6+ people are playing, ends when the game ends
  (count people per second with YOLO via an ffmpeg pipe, `count_people.py`, no files on disk; he checks the list).
- **Never assume one camera position.** Check one frame per video before anything else (this game: 8 different views; I wrongly said "same view in
  all 8" and had to redo hoops and tracking). Show Barak numbered/circled hoops per video and let him say which one is hoop A; rims per video are
  measured on zoomed crops with a pixel ruler. Check the camera is steady inside each video (ORB homography of a reference frame, `hoop_track.py`).
- **Rotation tags.** Phone videos can carry a `-180` rotate tag (videos 1-7) while the last one has none. A stream-copy concat applies the FIRST
  file's tag to everything, so an untagged video comes out upside down. Check `ffprobe ... stream_side_data=rotation` on every file; re-encode the odd
  one with `-noautorotate -vf hflip,vflip -video_track_timescale 90000 -pix_fmt yuvj420p -r 30` (a different time base breaks seeking). Verify a
  frame WITH players from every video after the join.
- **Frame names are 5 digits** (`work/f5/00001.jpg`); several scripts assume it. Disk can be nearly full: do not copy the originals.
- **Naming players across many videos.** Automatic tiles (players.py ask, DINOv2 clustering, clothing-colour clustering, even per video) come out
  MIXED when players are small and look alike. Do not ship them. What Barak accepts: I attribute from the shots only (see below) and send a decision
  map for the doubtful ones with my suggested option; every card/person carries written attributes that do NOT depend on the shirt (shoes, shorts,
  head/hair/beard/bald, build, jersey number when readable, shirts seen). NEVER pre-fill names from earlier games (different players;
  `game.json` `"naming_suggest": false` turns the suggestions off in `naming_page.py`).
- **Attribute only what the stats need: shooters and assisters of makes and attempts, not the whole game.** Minutes on court are left out unless he asks.
- **Credits**: he works in Sonnet; the 06.11 map chose the full pipeline anyway. Triage candidates locally first (drop setup-start artefacts = windows
  > 8 s, and weak `above_ball`-only signals) before agents see them. The strand test does not work when the net hangs against a light wall.

## Camera placement (tell Barak before each game)

Visual guide: `basketball_analysis\camera_position.html` (top view, side view, checklist). Ultra-wide lens is
required for the full-court spot (1x would need ~18 m distance).

Same spot every game, phone horizontal, 1080p/30 (60 fps if available), lens at ~2.5–3 m high (tripod on a
bench/fence/extension pole), locked exposure/focus, no zoom.
- **Half court**: behind the sideline extension at the free-throw-line level, ~3 m back from the sideline,
  angled ~30° toward the basket, so the rim sits in the upper third, ~⅓ in from the side, and the whole arc is in
  frame. Rim against a dark/plain background (not lights).
- **Full court**: centre line, ~4–5 m back from the sideline, as high as possible, both baskets and both baselines
  in frame, level horizon. Never under a basket shooting lengthwise (far rim becomes ~15 px and unreadable —
  that is what broke the first game's second half).
