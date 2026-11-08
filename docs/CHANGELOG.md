# Changelog

## 2026-11-08 - The project goes public (`courtside-ai`), explainers, blurred copies, laptop handover

Barak's decisions: `docs/share-plan-decision-map.html` (11 calls) and `docs/laptop-handover-decision-map.html` (3 calls).

- **Public repo** https://github.com/bshireto/courtside-ai (personal GitHub, MIT): a scrubbed export of this folder made by
  `tools/export_public.py` (pipeline, coaching-review tools, the skill with generalised paths, docs, one example config, the
  explainer source; friends' first names, Latin and Hebrew, replaced by roles; no footage, no face data). Release v0.1 carries
  both explainers, the blurred recap, one English coaching clip and the box score.
- **Explainer video** (`explainer/`, Remotion 4.0.541, 1080x1920, 67 s): navy / blue / yellow, Inter; a Hebrew composition
  (`ExplainerHE`, Heebo, plain words) next to the English one. Footage only from the 07.10 game, faces blurred except Barak's.
  Music "Funky Chunk" by Kevin MacLeod (CC BY 4.0), credited on the end card. Remotion 4.0.0 decoded 1080-wide clips as streaks.
- **Face blur for public copies**: `pipeline/blur_faces.py` (YuNet faces + YOLO head zones every frame, the stored "is this the
  user" model keeps Barak sharp, `--keep-box`, image mode, a hook for per-frame patches). `stats_poster.py` gained
  `BB_BLUR_OTHERS=1` and a frame fallback to the video when the 5 fps dump is gone.
- **Public 07.10 recap** `recap_2026-10-07/output/Every_Basket_Recap_public_0510.mp4` (+ WhatsApp copy): every face blurred except
  Barak's, the date rewritten to 05.10.2026 on the title, the nine stat cards and the end card (`tools/publish_recap_0510.py`,
  adaptive to the card fades; the card text x comes from each card's photo width).
- **English coaching clip** `analysis_2026-10-07/clips/drives/drive_c15_en_blur.mp4` from `work/drivevid/spec_c15_en.json`
  (teammates named by role, English simulation still).
- **X thread** (15 posts, one picture or video each) `docs/share/x-thread.md` + `docs/share/attachments/`
  (`tools/make_thread_images.py`); WhatsApp text in Hebrew `docs/share/whatsapp.md`; both state the two open issues (the workflow
  still prompts wrong steps at times; the judgement calls need the premium models, so a game spans several sessions).
- **Rule from Barak**: nothing from the 06.11 Goren run in any public asset; the 07.10 game is shown as 05.10 in public.
- **Laptop handover**: `migration-kit/03-copy-basketball.ps1 -Tier B` (project, repo, skill, memory to the SSD, no frame dump, no
  raw clips) and `migration-kit/restore-basketball.ps1` on the new laptop (four folders, memory under both keys, prints the venv
  rebuild). The raw Goren clips stay on the old laptop only (his call).

## 2026-10-08 - Recap of the 07.10.2026 game (`recap_2026-10-07`)

Outputs in `recap_2026-10-07/output/`: every-basket recap with nine player stats cards, Top 10 countdown (landscape + vertical,
with music), Barak's offense reel with stat pop-ups and stats card, phone-size and WhatsApp-size copies.

Game facts: one fixed side-on half-court camera, 4 on 4, nine players, four live windows given by Barak. 32 live baskets
(37 balls went through the net; 5 were dead-ball shots). Reviewers called 42 makes; 5 were balls passing behind or in front
of a still net and were overturned frame by frame.

### Pipeline changes
- `hoop_features.py`: force 30 fps so row n is t = n/30 on variable-frame-rate phone video.
- `shot_candidates.py`: a hoop can belong to several setups (one camera position split into live-game windows).
- `players.py`, `naming_page.py`, `orange_crops.py`: `game.json` `"plain_players": true` keeps players without a pinnie.
- New `net_strands.py`: strand test (did the net itself move) to separate real makes from balls behind the net.
- New `feet_check.py`: release-frame feet against the 3-point arc.
- New `roster_page.py`: naming page from a hand-built roster (one card per real person) for when tracker tiles are mixed.
- New `body_colors.py` + `user_clf2.py`: find Barak when his clothes differ from the stored model (embedding + clothing colours).
- New `wf/attribute_shots.js`: name every shooter and find assists (two reviewers per make, tie-break).
- New `top10_page.py`: Top 10 approval page with a clip per basket.
- `wf/label_touches.js`: `args.look` describes the user for this game.
- `render_v2.py`: baskets labelled `BUCKET n  NAME`; end-card audio offset taken from the game config.
- `stats_card.py`: optional duration argument; encodes like the clips so cards join without re-encoding.
- New `stats_poster.py`: vertical 1080x1920 box-score image (leader chips + table of all players) -> `output/Box_Score_Vertical.png`;
  optional `data/poster_photos.json` picks and centres each avatar.
- Skill `basketball-recap`: section with the lessons from this game.

## 2026-10-09 - Vertical Top 10 follows the ball

Barak rejected the fixed-crop vertical cut ("doesn't catch the whole action"). The vertical Top 10 of `recap_2026-10-07` was
re-rendered with a window that pans with the ball; the fixed-crop files moved to `output/old/`.

- New `vfollow.py`: focus path per clip (`data/vpaths/<id>.json`) -> smoothed virtual camera with lead room toward the basket;
  `frames` makes gridded annotation sheets, `check` shows exactly what the vertical video will show plus edge margins.
- New `wf/follow_paths.js`: one reviewer per clip marks the ball through the live and replay windows and runs `check` until clean.
- New `render_vertical_follow.py`: cuts live (864x1080 window, pans in x) and replay (640x800, pans in x and y, half speed)
  straight from the source, reuses the cards from `render_vertical.py`, adds music and a WhatsApp-size copy.

## 2026-10-09 - Offense review of the 07.10.2026 reel (`analysis_2026-10-07`)

First "offense review": Barak's offense reel (27 possessions, 13 shots) analysed frame by frame, plus the research on how to
analyse a player's film and what to hand back, plus a decision map on the recurring per-game outputs.

Deliverables: `analysis_2026-10-07/Barak_Offense_Review_2026-10-07.html` (the review: summary, line, three ranked fixes with
cues and frames, strengths, shot chart + graded shot table, counted tendencies with skeptic verdicts, teaching moments, drills
mapped to the fixes with a 25-minute session, next-game targets, possession log, method), five captioned coaching clips in
`analysis_2026-10-07/clips/coach_0N_cXX.mp4`, `docs/research-offense-video-analysis.html` (validated research report) and
`docs/offense-review-outputs-decision-map.html` (seven decisions on the recurring workflow).

### How it was produced
- `make_sheets.py` / `make_briefs.py`: reel decoded at 10 fps; per possession wide "flow" sheets (2 fps), tracked "zoom"
  sheets (5 fps), 10 fps release strips and the full release frame; one brief per possession with the pipeline's touch notes.
- `workflows/clip_analysis.js` (+ `_resume.js`, `_resume2.js`): one vision reviewer per possession -> three lens syntheses
  (shot selection / mechanics / off-ball) -> head-coach report -> a skeptic re-watches the frames behind every claim.
- `workflows/research.js` (+ resume variants): seven research angles -> fact-check of all 44 load-bearing claims -> completeness
  critic with gap-fill -> synthesis (`results/research.md`).
- `make_shot_chart.py` (shots on the real court, players removed), `make_treatments.py` (seven on-screen treatment stills,
  incl. a YOLO11 pose overlay), `make_coaching_clip.py` (live with caption -> slow replay -> freeze with ring; captions wrap
  and are LF-only), `make_clip_specs.py` (specs from the verified report's teaching moments), `build_report.py`,
  `build_research.py`, `build_decision_map.py`, `htmlkit.py`.
- Resume tooling after a dead session: `extract_journal.py`, `prep_resume.py`, `finish_results.py`, `run_stats.py` (finished
  agent results are recovered from the workflow journals; big inputs are written to disk and read by the agents).

### Findings of the game (from the verified report)
5 of 6 when the shot came out of a move or a catch with space, 0 of 7 after a hold, a dead dribble or into a set defender;
10 of 14 check-ball catches still in hand after ~4 s; the long two is the most-taken, least-made shot; the runner is 2 of 2.
Three fixes: decide on the catch when the defender sags (one count), retire the shot over a hand inside the arc (toes behind the
line or paint under the feet), feed the open man when the second defender steps up.
- Decision-map skill (both configs): a lightbox for `img.zoomable` and the pane-legibility rule (real content as text in the 340 px preview, images open full-size, the real file linked) after the first map shrank the whole review into the pane.

## 2026-10-11 - Offense review, round 2: Hebrew, plain language, OKC colours, drive analysis, Weavy simulation

After Barak answered the output-format decision map (review + clips, wide phone only, five metrics + trend, full review with the skeptic
pass, drill table + phone card, pose numbers only on close-up footage, best treatment per insight) and asked for Hebrew, plain wording,
non-Investing colours, a drive analysis and a Weavy test.

- `htmlkit.py`: OKC Thunder palette, Heebo, right-to-left safe CSS, `dir` on the page; top bar keeps its title next to a long nav.
- `build_report_he.py`: the review in Hebrew (`Barak_Offense_Review_2026-10-07.html`); `build_report.py` now writes the English copy
  to `..._en.html`. New sections: game-to-game tracker with a follow-up of earlier findings (`history.json`), drives, glossary; drills
  grouped solo / with a partner / inside a game.
- `workflows/plain_rewrite.js`: plain-Hebrew rewrite of every report block, a faithfulness checker per block, a glossary.
  `workflows/translate_he.js`: the 27 possession narratives and the skeptic corrections. `finish_round2.py` saves both.
- `make_drive_wf.py` -> `workflows/drive_analysis.js`: one reviewer per drive (13): defender's stance, raised hand, lead foot and
  momentum, where the help stood, side attacked, angle past the defender, hesitation moves; then patterns and a skeptic pass. Right and
  left are the player's own; the camera-side mapping is written into the brief. `make_drive_diagrams.py` draws each drive on the court.
- `captions.py`: caption overlays rendered with PIL + python-bidi (ffmpeg drawtext cannot shape Hebrew). `make_coaching_clip.py` uses
  them and can append still images; `make_compare_clip.py` makes a side-by-side of two moments. Clips: five fix/keep clips, the
  same-spot comparison (c007 vs c008), the 4:24 drive clip.
- `build_session_card.py`: phone-size session card with three tabs and a PNG per tab (`session_cards/`).
- Weavy test (9 of the 100 credits he allowed): `make_pose_rig.py` draws the skeleton rig, a reference grid of eight cut-outs is built
  with yolo11s-seg, the tool returned him in the rig's pose on a green background, `make_weavy_sim.py` pastes it onto the real 4:24
  frame in place of the real player (`work/weavy/sim_c23_panel.jpg`).
- Correction found on the way: the first review's records used picture directions for some drives. The 4:24 drive went to his left
  with the ball in his right hand, not "right".
- Drive analysis outcome: the skeptic pass marked all seven checked claims "partly", so `drive_analysis.js` got a Finalize phase in
  which the head coach rewrites the summary, counts, rule check and priorities from the corrected claims and adds a note per drive
  (`results/drive_patterns_final.json`). Corrected headline numbers: open side attacked from the first step 3 of 10, first defender
  passed clearly 3 of 13 plus 2 half-steps (was 4), wide arc 5 / no turn to the basket 3 / straight at a defender 2 / tight 3, shot or
  pass fakes moved the defender 8 of 8 and dribble moves 5 of 18. `drills_drive_he.json` adds three drive drills.
- Simulations, second batch (27 more Weavy credits, 36 of 100 in total): the pose rig now marks the ball and tells near limbs from far
  limbs by colour (`make_pose_rig.py`), which is what made "ball in the far hand" come out right. Three new figures (far-hand drive, set
  shot, kick-out pass). `make_weavy_sim.py` anchors by the planted foot, recolours the bib for game 1 and builds a two-up panel.
  `make_sim_wf.py` -> `workflows/sim_composites.js` built and reviewed seven composites (fix 2, fix 3, drives 11, 13, 15, 24, 25);
  `finish_sims.py` collects them into `work/weavy/sims.json`. The review shows them on the fix and drive cards, the fix 2 and fix 3
  clips end on their simulation, and the combined phone video is now 1:46.

## 2026-10-11 - Follow-the-ball vertical is now the standard flow

- `render_vertical_follow.py` builds its own title / rank / end cards (no `render_vertical.py` run needed) and refuses to start
  when a play has no ball path; `--cards-only` rebuilds just the cards.
- `render_vertical.py` (fixed crop) refuses to run unless `--static` is passed; it stays as the library for cards and overlays.
- Skill `basketball-recap`: new non-negotiable rule 9 (every vertical video follows the ball) and step 7b with the four commands.

## 2026-10-11 - Offense review, round 3: shot analysis removed, plain opening, clean-up decision map

Barak: the analysis has too much going on, no shot analysis from game footage, the opening line was not understandable, and the drives
should get Weavy simulations and video clips like the fixes.

- `analysis_2026-10-07/scope.json` (new): the list of what the review shows, plus the plain-language top block and fix texts.
  `build_report_he.py` reads it: the shot sections, the "step back for a three" fix and every shot item are out; the page opens with
  three plain instructions; the two remaining fixes read "what happened / what to do / how it looks when it is right".
- Clips: the two fix clips re-rendered with the new numbering; the combined phone video is three clips (48 s).
- `clips/drive_c15_0251.mp4`: a sample of the proposed drive format (live, slow motion, stop with a ring, simulation with lines).
- `analysis_2026-10-07/build_cleanup_map.py` -> `docs/offense-review-cleanup-decision-map.html`: every output of the round with a
  proposal to keep, merge or drop it (8 decisions). The review measured 26,452 words; the proposal is three parts and about 1,700.

## 2026-10-12 - Offense review, round 4: the short review, a video per drive, Weavy-drawn simulations

Built from Barak's answers to the clean-up decision map (three parts only; every drive a video; "snatch" = the defender's reaching
hand; one phone card; all numbers with trend graphs; archive the rest) and his note that the videos deserve the most effort.

- New folder `review_2026-10-07/`: the only place he needs to open. The review, the phone card with its three pictures, and `clips/`.
- `analysis_2026-10-07/make_drive_video.py`: coaching videos from a list of segments (live with timed captions, slow motions at any
  view, stops with drawn layers that fade in one after another, a simulation still, a closing card with the sentence to himself).
  `render_all.py` renders several specs at once; `finish_drives.py` makes the phone copies and one video of all drives.
- 13 drive videos (27-31 s each) and one for "decide within a second" (41 s), each built by a helper agent from
  `work/DRIVE_VIDEO_BRIEF.md`: two or three slow motions, a stop on the read (crowded side in red, freer side in green), a stop on
  the hand check, a stop on how it ended, the simulation, the cue. `work/drivevid/card_c*.json` holds the short text per drive.
- The hand check ("snatch"): per drive, which of the defender's hands reached for the ball and what he did about it. The ball was
  exposed in front of a reaching hand in 6 of 13 drives.
- Weavy: two new figures (drive past the hip, pass toward the near side), six new composites, and `weavy_still.py`: the tool redraws
  a simulation still with our marks as clean telestration (his suggestion). 12 of 13 stills use it. 198 of the 200 credits allowed.
- `build_review.py`: the short review (three parts + a closed drills drawer), about 2,500 words instead of 26,000. `history.json` v2
  holds every number per game; the review draws a small trend chart per number.
- `practice.json` + `build_session_card.py`: drills and 25-minute plans rewritten in plain Hebrew without the shooting drills, with
  two new drills for the defender's reaching hand.
- Archive: `analysis_2026-10-07/archive/` and `docs/archive/` (see `archive/MOVED.md`); nothing was deleted.

## 2026-10-12 - Offense review, round 5: read-then-watch videos, clickable clip mentions, clearer tracker cards

Barak after watching the videos and reading the review: the videos go too fast to read and watch at once; a clip mentioned in the
text should be clickable and play next to the text; the percentages and numbers in the "am I improving" cards were not clear.

- Videos re-cut in a "read, then watch" format: text only on frozen pictures, clean motion, slow motion at a third / a quarter
  speed that pauses at each key moment, each stop shown step by step with one short sentence per step, reading time by word count.
  He approved the clip 15 example; all 13 drive videos (87-103 s) and the instruction-1 video (125 s) were then re-cut by one
  helper each from `analysis_2026-10-07/work/DRIVE_VIDEO_BRIEF_V2.md`. First cuts are in `archive/drivevid_v1/`.
- `make_drive_video.py`: segment type `stop` with steps, base layers, `pace` (seconds per word), `caption_size`, seamless pauses,
  a timeline file per video. New `freeze_grid.py`, `qa_parts.py`, `render_queued.py`.
- `build_review.py`: every clip mention in the text becomes a link, checked against `clip_map.json` at build time; a click plays
  that moment of the reel in the card's own video slot (from the start / half speed / back), and the slot stays in view while the
  text scrolls. A mention with no video next to it opens a small floating player. The reel is copied to `review_2026-10-07/clips/`.
- `build_review.py`: tracker cards without percentages: the count and out of what, one circle per time, which direction is better,
  the target as a sentence, one bar per game with the same words beside it.
- Checked in headless Chrome (desktop and phone width): links play and stop at the end of the possession, one video plays at a
  time, the slot is sticky, no horizontal overflow, no page errors.
- 2026-10-13: targets for the next game are percentages (the number of catches, possessions and drives differs every game).
  `history.json` metrics carry `target_pct` / `target_plain`; the cards, the bars and the table show the percent with the count
  it comes from beside it.
