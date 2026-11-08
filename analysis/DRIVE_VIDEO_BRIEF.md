# Brief v2: re-cut one coaching video in the "read, then watch" format

Barak plays weekly pickup basketball and studies his own offense from short coaching videos we make for him. About the first
generation of these videos (28 seconds, captions over moving pictures) he wrote:

> "The video goes too fast and Im not able to both read and view. you need to slow down more with more freezes."

We rebuilt one video (clip 15) in a new format and he answered **"video is great"**. Your job: re-cut the video named in your task
in exactly that format. The facts, the sides, the names and most of the drawn marks already exist and were checked; you are
changing the **pacing and the wording**, not the analysis.

Folder A = `<project>/analysis_2026-10-07`.
Run everything from inside A (Git Bash) as `PYTHONUTF8=1 ../.venv/Scripts/python.exe <script> ...`.
**Do not edit any script. Write only the files listed under "What you deliver".** Scratch pictures go to `work/drivevid/tmp/`
with your clip name in the file name (other helpers are working in the same folder on other clips right now).

## Read first (in this order)
1. `work/drivevid/spec_c15.json`: the approved example, new format. Its check sheets (one frame per part):
   `work/drivevid/example_c15/qa_c15_0.jpg` ... `qa_c15_3.jpg`. Look at all four.
2. `archive/drivevid_v1/spec_c15.json`: the same clip in the OLD format, so you can see what changed.
3. The header of `make_drive_video.py` (spec format; the part headed "Read-then-watch pacing").
4. For your clip: the OLD spec `archive/drivevid_v1/spec_<name>.json` (times, views, marks, captions: all checked last round),
   its check sheet `archive/drivevid_v1/drive_<name>_sheet.jpg`, the card `work/drivevid/card_<name>.json`, and the verified record:
   the entry with your clip number in `results/drives.json` plus the note for your clip in `results/drive_patterns_final.json`
   (`drive_notes`). The record is the source of truth for sides, names, counts, times and what would have been better.

## The one rule everything follows from
**Text and moving pictures never share the screen.** He reads on a frozen picture, then watches clean motion.
- `live` and `slow` parts carry only a short `tag` (top corner). No `caption`, no `captions`.
- Every sentence sits on a frozen picture: a `freeze`, a step of a `stop`, the `still`, the `card`.
- No `secs` anywhere. The spec has `"pace": {"per_word": 0.38, "look": 1.4, "min": 3.0}` and `"caption_size": 54`, and the tool
  gives every frozen part `1.4 s + 0.38 s per word` (caption + the labels that part adds). Fewer words = a shorter, better video.

## The order of the parts (copy the example's skeleton)
1. **Opening** `freeze` on the first frame of the live window, whole frame (no `view`): tag `קליפ N · M:SS`; caption
   `חדירה לסל מול <שם המגן>. קודם תראה אותה במהירות רגילה.`; one layer with two labels, `אתה` and the defender's name, centred
   above their heads (`"anchor": "c", "size": 44`).
2. `live`: the same window as the old spec, tag `מהירות רגילה`.
3. **Stop-and-go slow motion, in time order, never jumping back.** The slow motion runs to a key moment, the picture pauses there
   (a `stop`), then the slow motion continues from that same frame:
   - a cue `freeze` on the first frame of the slow motion, same view: `עכשיו לאט. תסתכל ...` (tell him the ONE thing to watch);
   - `slow` (`"speed": 0.333, "flash": false`, tag `הילוך איטי`) from there to the key moment;
   - `stop` at that moment: **`at` = the `end` of the slow part before it = the `start` of the slow part after it, same `view`**;
   - and so on through the drive. For the hand check: a cue `freeze` in the close-up view (`עכשיו תקריב, לאט מאוד. תסתכל על ...`),
     `slow` at `"speed": 0.25` (tag `הילוך איטי מאוד`), then the stop `עצירה N · היד שבדרך`;
   - the last stop or freeze says how it ended.
4. `live` again, same window, tag `שוב · מהירות רגילה`.
5. `still`: the simulation picture from the old spec, same tag, plus `"words": <number of words written inside the picture>`.
   If the old spec has no still, leave it out.
6. `card`: title, text and foot from the old spec.

## Stops
- **3 to 5 stops** per video, each at a moment that matters (the read, the wrong turn, the hand, the end). Number the tags:
  `עצירה 1 · <שתי מילים>`, `עצירה 2 · ...`.
- A stop has **1 to 3 steps**. Each step = **one sentence of at most 9 words, one idea**, and may add ONE drawn layer.
  Marks of earlier steps stay on screen. Split the old 14-word captions into two steps instead of shortening them into riddles.
- Labels on the picture: **at most 4 words, best a name** (`חבר לקבוצה`, `המגן`, `הכדור`, `יד ימין של המגן`). A label never repeats
  the caption. When the caption names several players, ring each one and label each with his name.
- Reel time of a slow part: 0.4 to 1.3 s. Speeds: 0.333, or 0.25 for a close-up. Nothing faster.
- Keep one view through a slow part and the stop that ends it. Change the zoom only at a cue freeze or exactly at a stop.
- Whole video: **70 to 110 seconds**.

## Marks and coordinates
- All coordinates are FULL-FRAME pixels of the 1920x1080 reel. Colours: green = the better path / free space, red = what went
  wrong / the crowded side, yellow = the ball, blue = a free teammate.
- A stop at the same `at` as an old freeze: reuse the old marks, after checking them on your render.
- A stop at a NEW time: read the coordinates from the frame the tool really freezes on:
  `freeze_grid.py work/drivevid/tmp/<name>_g.jpg <reel_t> x0 y0 x1 y1 [--scale 2] [--step 40]`
  (the 10 fps pictures in `work/frames/` can be one frame off; do not use them for coordinates).
- Arrows lie on the floor (start at the feet). A ring sits on the right person, hand or ball. A label never covers a player or
  the ball. Captions take the bottom 240 output pixels and the tag the top right corner: keep marks out of both.
- Real footage is never altered. Only the `still` shows something that did not happen.

## Wording (he was angry about unclear text)
- Hebrew, everyday words, short sentences. Say what happened, then what to do. He was not part of the analysis: no codes, no
  shorthand, no clever lines. Write to him as `אתה`.
- **Right and left are always his own, facing the basket**: `ימין שלך` (the side near the camera, lower in the picture) and
  `שמאל שלך` (the far side, higher in the picture). A defender facing him is mirrored: the defender's RIGHT arm is the far one.
- Names: ברק, המגן, המגן, המגן, המגן, חבר לקבוצה, חבר לקבוצה, חבר לקבוצה, חבר לקבוצה. Times as `2:51`. Numbers as `3 מתוך 10`.
- English only for a move with no Hebrew name (crossover, pull-up, floater).
- **No shot analysis.** `זרקת` is an event; never grade a shot or its technique.
- **Faithful.** Every side, name, count and time agrees with the verified record or with what the frames clearly show. Do not
  add a claim that is in neither. Keep the record's limits (`פנוי עד המגן ליד הסל` is not `ריק`). A count of players is a claim:
  count them on the frozen frame or name them instead.

## Render and check (at most 4 rounds)
1. `render_queued.py work/drivevid/spec_<name>.json` (waits for a free slot; give the command a 10-minute timeout).
   It writes `clips/drives/drive_<name>.mp4`, `_sheet.jpg`, `_timeline.json`.
2. `qa_parts.py <name>` prints the timeline, the total length and warnings (`JUMP`, `TEXT ON MOTION`, `TOO LONG`), and writes
   `work/drivevid/tmp/qa_<name>_0.jpg`, `_1.jpg`, ... (six parts per sheet). **Read every sheet.** Check on each part:
   the ring is on the right person / hand / ball; every label is readable and covers nobody; the caption is one line and one idea;
   the cue freeze really shows the players it talks about; the picture of a stop is the moment the caption describes.
3. Fix and render again until it is clean. `JUMP` and `TEXT ON MOTION` must be gone. `VIEW CHANGE` is fine when you meant it.

## What you deliver
1. `work/drivevid/spec_<name>.json`: new, with `"out": "<A>/clips/drives/drive_<name>.mp4"`, the `reel` path copied from the
   example, `pace` and `caption_size` as in the example, and an `"_about"` line saying what you changed and anything unusual.
2. The rendered `clips/drives/drive_<name>.mp4`.
3. In `work/drivevid/card_<name>.json` change only `"seconds"` to the new length (drive clips only; leave every other key alone).
4. Your final answer, short: the video length, the list of stops (time + what each one says), anything you could not make
   faithful or had to leave out, and any place where the frames contradicted the old spec.
