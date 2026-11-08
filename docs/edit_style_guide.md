# Style guide: pickup-game recap (A: every made basket with effects, B: plain personal reel)

I checked this guide against the source file, not just the three reports.
- **Test script:** `~\AppData\Local\Temp\claude\<project-session>\0e52b78f-3aba-4f3d-8324-de9d186d2b25\scratchpad\stylecheck\spec_test.py`. Its functions `live_segment`, `replay_segment`, `card_segment` and `title_png` produce every filter string below.
- **What it built:** title card, then a live clip, a replay, a second live clip and an end card, joined into one file (same folder, `recap_test.mp4`).
- **Result:** video and audio are both exactly 26.000 s. A full decode reported zero errors. Loudness came out at -14.4 LUFS with a true peak of -1.2 dBTP.

## 0. What I found in the footage that the reports don't cover

1. **The camera moves partway through, between 15:00 and 20:00 of the source.** Frames at 900 s and 1200 s show two different setups.
   - **Setup 1** (start of the file to about 15:00): the camera is at a baseline corner.
     - Near rim at about (1290,470).
     - Far rim small, at about (1110,605).
   - **Setup 2** (about 20:00 to the end): the camera is under one basket.
     - That near rim sits at the top-right edge and is partly out of frame (about x 1500–1920, y 0–200).
     - Far rim at about (975,570).
   - Rim coordinates must therefore be looked up per setup, never set once for the whole file.
   - No clip may include the footage of the camera being moved.
2. **At the far rim, 2.0x zoom is not enough.** Players there are only about 70 px tall in the source.
   - At 2.0x they are about 130 px, still too small. At 2.5x they are about 180 px: soft but readable.
   - Comparison image: `stylecheck\cmp.png`.
   - The reports say to stay at or below 2x. I raise that to 2.5x for far-rim replays only.
3. **Loudness:** the natural audio measures about -28 LUFS, so it needs about +14 dB of gain.
   - At that gain, loudnorm pass 2 switches to its dynamic mode on its own.
   - That is acceptable. Use TP=-2 so the true peak lands below -1 dBTP; the test with TP=-1.5 came out at -1.2.
4. **File size:** the CRF 17 intermediates of this noisy night footage run 20–23 Mbps.
   - Joining them with `-c:v copy` gives about 13 Mbps, roughly 100 MB per minute.
   - A separate share encode is needed. At CRF 23 the test came out at 4.6 Mbps.

## 1. How recaps are made (sources)

### Pro and broadcast

- **ESPN basket clips:** 6–7 s long, ending 1–1.5 s after the make. About 10 baskets per game, in chronological order.
  - Dunks are 8% of all baskets but 37% of highlight baskets. Free throws are almost never shown.
  - Excitement ranking: dunk > putback > 3PT > layup > jumper.
  - Source: Bettadapura et al. 2016, https://arxiv.org/abs/1606.08955
- **Total length, measured:**
  - NBA full-game highlights: median 9.65 min (https://www.youtube.com/playlist?list=PLlVlyGVtvuVkxr3RnRwVqtuWR7BSBE0tD).
  - FIBA short highlights: about 3.2 min. It cold-opens, uses short cross-dissolves, has no replays in the first 100 s and only 16 hard cuts in 182 s (https://www.youtube.com/watch?v=DRFjrSyIaSg).
  - EuroLeague recap: 8.6 min, with replays only on dunks, about 1–2 per 3 min (https://www.youtube.com/watch?v=AEqOzTt3y0o).
- **Top-10 packages replay every play** (https://www.youtube.com/watch?v=Gnq_Nhv-ZAM).
  - Structure: live shot 7–11 s, reaction 1–2 s, then one or two tight replays of 3–7 s each.
  - There is no "REPLAY" label. A stinger of about 0.3 s marks the replay, and the score bug is hidden during it.
- **Replay speed:** classic broadcast replays run at half speed (https://www.mediacollege.com/video/production/vt/slow-motion-replay.html). Super slow motion runs 3–6x (https://www.creativebroadcast.ae/understanding-replay-in-live-sports-replay/).
  - EVS makes 2–3x slow motion from normal-frame-rate cameras (https://evs.com/products/live-replays-storytelling/xtramotion).
  - EVS zooms only by cropping 4K to 1080p, so at most 2x without loss (https://www.tvbeurope.com/live-production/evs-zooms-in-on-replays).
- **Replay transitions:** traditionally a logo wipe or dissolve of 0.4–1.2 s placed before and after the replay (https://link.springer.com/chapter/10.1007/11893257_50).

### Amateur and automatic

- **Veo** (https://www.veo.com/en-us/sport/basketball):
  - Its follow-cam is a virtual crop of a panoramic recording.
  - Player Moments filters by distance to the ball, time on the ball and a buffer before and after each moment (https://updates.veo.co/announcements/veo-player-moments).
- **Pixellot:** automatic recaps of 2–10 min, built from the plays its AI scores as most important (https://www.pixellot.tv/products/automatic-highlights/).
- **Hudl:**
  - Autogen game recaps include threes, steals, dunks, runs and fast breaks.
  - Manual clips default to 7 s, and clips should run no longer than 10 s.
  - Spot shadows are used sparingly (https://www.hudl.com/blog/tips-to-create-a-fire-highlight).
- **Per-player reels:**
  - Trace and SportsVisio build a reel for every player from touches, shots, assists, rebounds and "involvements" (https://traceup.com/sports/basketball, https://www.sportsvisio.com/stories/how-ai-basketball-analysis-works).
  - Hudl Assist includes misses (https://www.hudl.com/blog/play-hard-watch-smart-with-new-automatic-playlists).
- **Recruiting and plain reels:**
  - 3–7 s per play (https://basketball.scouting4u.com/blog/basketball-highlight-reel-tips-create-impactful-reels).
  - No slow motion, music, circles or arrows (https://proskillsbasketball.com/basketball-highlight-video/).
- **Social edits:** a flash of 0.2–0.4 s only on key hits, shake or glitch at most 2–3 times per edit, and one or two overlays at most (https://store.hollyland.com/blogs/creator-hub/make-sports-edits-on-capcut).

## 2. Edit spec for deliverable A (every made basket, with effects)

### Structure
- Title card (3.0 s), then every make in chronological order, then an end card (5.0 s).
- No cold-open teaser. It would repeat a play that appears again later anyway.
- Game separators are optional. Use them only if game boundaries are confirmed: a 1.5 s "GAME N" card that also resets the running tally.
- Length estimate: 3 + 6.5 × makes + 5.3 × replays + 5 seconds. For example, 40 makes with 12 replays comes to about 5.5 min.

### Live clip per make (T = the moment the ball goes through the net)
- **Start:**
  - Default is T − 5.0 s, but never earlier than the change of possession minus 0.5 s.
  - The lead-in is at least 3.0 s.
  - Fast breaks and assisted plays may go up to T − 6.0 s.
- **End:** T + 1.5 s. A typical clip is 6.5 s, with a hard maximum of 10 s.
- **Overlapping windows** (a quick score back, or a putback): merge them into one clip that carries both tally updates.
- **The camera stays wide.** No zoom and no Ken Burns move on live clips.

### Which makes get a replay
- Target 25–35% of makes, with a hard cap of 40%.
- **Replay these:**
  - threes
  - and-ones, contested or acrobatic finishes (reverse, euro, scoop)
  - putbacks and tip-ins
  - finishes off a steal or fast break
  - highlight assists (no-look, behind the back, long outlet pass)
  - the winning basket of each game, if game boundaries are known
- **Never replay:**
  - uncontested open layups
  - free throws
  - makes where the ball or rim is hidden, or where the ball leaves the top of the frame (common at the setup-2 near rim)
  - plays too dark or blurred to read
- One replay per play. There is only one camera angle, so never two replays.

### Replay
- **Source window:**
  - Default: T − 2.0 s to T + 0.5 s, covering gather, release and net.
  - Assists and putbacks: T − 3.0 s to T + 0.5 s.
- **Speed and method:**
  - 0.5x using motion-compensated interpolation (`minterpolate mci`), applied to the crop before any zoom.
  - Never 0.25x: the ball and hands warp.
  - If the ball smears in the output, fall back to `framerate` blend for that clip.
- **Output length:** 5.0 s by default, 7.0 s for assists and putbacks. The package cannot exceed 7 s.
- **Zoom and framing:** the replay is a 16:9 crop, then an eased push-in toward the rim.
  - Crop widths: 1280 (1.5x), 1152 (1.67x), 960 (2.0x), 768 (2.5x). Heights are width × 9/16.
  - **Near rim, setup 1:** 1280 crop plus a push to 1.2, about 1.8x in total.
  - **Far rim, either setup:** 960 crop plus a push to 1.25, about 2.5x in total. That is the ceiling.
  - **Setup-2 near rim (at the frame edge):** 1280 crop centred on the shooter, no push.
  - **Horizontal centre:** 0.6 × rim_x + 0.4 × shooter_x at the release.
  - **Vertical centre:** rim_y + crop_height/6, which puts the rim in the upper third.
  - Clamp the crop to the frame. If the shooter at release and the rim don't both fit with about 8% margin, step down one crop size.
  - **Push-in:** a cosine ease over the whole replay toward the rim point. Never pan across the court and never zoom out.
- **Look:**
  - Denoise the crop before interpolating.
  - Scale up with lanczos, then use a slightly stronger unsharp (0.8) than the live grade (0.6).
  - Add a subtle vignette (angle PI/6).
- **No freeze frames or spotlight rings.** That is a recruiting-reel device, not a game-recap one.

### Transitions
- No xfade anywhere. Every transition is a fade inside its own segment, so the concat demuxer needs no offset math.
- **Live → live:** a dip to black. The first clip ends with a 0.15 s fade-out and the next starts with a 0.15 s fade-in.
- **Live → replay:** the live clip ends with no fade, the cut lands on the replay, and the replay opens with a 0.2 s fade from white. This is the only flash in the video.
- **Replay → next clip:** the replay ends with a 0.15 s fade to black, and the next clip fades in over 0.15 s.
- **Title → first clip:** the title fades out to black over 0.3 s, and the first clip fades in over 0.15 s.
- **Last clip → end card:** the last clip fades out over 0.15 s. The end card fades in from black over 0.4 s and fades out to black over 1.0 s.

### On-screen text
- One font throughout: Segoe UI Bold, `C:\Windows\Fonts\segoeuib.ttf`; the subtitle uses Segoe UI, `segoeui.ttf`.
- **Keep orange and lime out of the text styling,** because those are the team colours.
- **Running tally, live clips only:**
  - Text like `ORANGE 4   LIME 2`, 34 px, white on black@0.55.
  - Box border 12|20, bottom-left at x=48, y=h−text_h−60.
  - It switches to the new count exactly at T.
  - It counts **baskets, not points**, because pickup scoring rules are unknown.
  - Hide it during replays and on cards.
  - Leave it out entirely if the scoring team is not confirmed for every make.
- **REPLAY tag:**
  - 34 px, same style, top-right at x=w−text_w−60, y=56.
  - Visible from 0.15 s to 0.2 s before the end of the replay.
  - Report 3's orange box (0xFF6B00) clashes with the orange pinnies, so don't use it.
- **Title card (Pillow PNG):**
  - Background: a still frame from the game, Gaussian blur 18, blended 55% toward black.
  - "PICKUP RUN" at 130 px bold, centred, starting at y=430.
  - Subtitle "23.09.2026  |  Orange vs Lime  |  Every basket" at 46 px regular, colour (230,230,230).
- **End card:** "THAT'S THE RUN" at 110 px, with "Orange N baskets  |  Lime M baskets" at 46 px. If team counts aren't confirmed, use "Every basket  |  23.09.2026".

### Audio
- **Live clips:** natural audio with 0.05 s fades at every cut, to prevent clicks.
- **Replay:** `atempo=0.5`, which keeps the pitch, at volume 0.3 (about −10.5 dB), fading in over 0.2 s and out over 0.4 s.
  - **Never pitch it down.** This overrides report 3's `asetrate` recipe, which makes the "whale" sound.
- **Cards:** 3–5 s of ambient court audio taken from the source (for example the few seconds before the first clip) at volume 0.5, with fades.
- **No music and no sound effects**, including whooshes.
- **Master:** `highpass=f=70`, then two-pass loudnorm at I=−14, TP=−2, LRA=11.

### Colour grade
- Live clips: the light grade (curves, saturation 1.25, unsharp 0.6).
- Replays: the same grade plus the denoise and the stronger unsharp.
- Cards: no grade.

### Encode
- **Intermediates:**
  - x264 at CRF 17, preset medium, g 60, high profile level 4.1, yuv420p TV range, bt709 tags, timescale 15360.
  - Audio: pcm_s16le, 48 kHz stereo.
  - Every segment has exactly N frames and N × 1600 audio samples.
- **Master:** concat demuxer with `-c:v copy`, audio through the loudnorm chain and out as AAC 192k, plus `+faststart`.
  - Tested: the join is exact and takes about 6 s.
  - It comes out around 13 Mbps.
- **Share copy:** re-encode at CRF 23, preset medium, maxrate 8M. The test came out at 4.6 Mbps, about 35 MB per minute.

## 3. Edit spec for deliverable B (plain involvement reel)

### What counts as an involvement on offence
- He catches, dribbles or passes the ball.
- He takes a shot, made or missed.
- He makes an assist.
- He gets an offensive rebound or a tip.
- He sets an on-ball screen for the ball handler.
- He draws a foul.
- He turns the ball over.
- He is the intended target of a pass that gets deflected or stolen.
- **Excluded:** off-ball movement without the ball, and simply being near the ball carrier.

### Clip window
- **Start:** 2.0 s before his first touch. For a screen, 1.0 s before contact.
- **End depends on the action:**
  - **Shot:** 1.5 s after the result (net, or rebound secured).
  - **Pass:** 1.5 s after release. If the receiver shoots within 3.0 s, extend to 1.0 s after that shot's result.
  - **Screen:** 1.5 s after the ball handler's next action, with a 4 s cap after contact.
- **Merging:** merge windows less than 3.0 s apart.
- **Limits:** minimum clip 3.0 s. Maximum 20 s; split longer ones at a dead ball.

### Treatment
- Straight hard cuts, chronological order.
- No title card, text, grade, zoom, slow motion, rings, freeze frames or transitions.
- Only the 0.05 s audio fades at each cut, which are not audible, and the same loudness mastering as A.
- Normalizing the video (colour range and frame rate) and the master encode are the same as in A.

## 4. ffmpeg recipes (strings exactly as they ran in the test)

Placeholders are in CAPS. Times are measured wall-clock on this machine (8 threads).

### 4.1 Normalize any cut (A and B)
Put `-ss` and `-t` before `-i`: `-ss START -t D+0.3 -i SRC`.
```
[0:v]fps=30,trim=end_frame=N,setpts=N/30/TB,scale=1920:1080:in_range=full:out_range=tv:flags=lanczos,setsar=1[,...],format=yuv420p[v];[0:a]aresample=48000,aformat=sample_fmts=s16:channel_layouts=stereo,atrim=end_sample=N*1600,asetpts=N/SR/TB,afade=t=in:d=0.05,afade=t=out:st=D-0.05:d=0.05[a]
```
Encode flags:
```
-c:v libx264 -preset medium -crf 17 -g 60 -pix_fmt yuv420p -profile:v high -level 4.1 -video_track_timescale 15360 -color_range tv -colorspace bt709 -color_primaries bt709 -color_trc bt709 -c:a pcm_s16le -ar 48000 -ac 2
```
Cost: a plain B clip is about 10–12 s. Most of that is the roughly 9 s seek into the 4.3 GB file, so run 4–6 cuts in parallel.

### 4.2 Live clip for A: add after `setsar=1`
```
curves=master='0/0 0.12/0.10 0.5/0.58 0.85/0.9 1/1',eq=saturation=1.25,unsharp=5:5:0.6:5:5:0,fade=t=in:st=0:d=0.15,fade=t=out:st=D-0.15:d=0.15,drawtext=fontfile='C\:/Windows/Fonts/segoeuib.ttf':fontsize=34:fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=12|20:x=48:y=h-text_h-60:text='ORANGE 3   LIME 2':enable='lt(t,LEAD)',drawtext=fontfile='C\:/Windows/Fonts/segoeuib.ttf':fontsize=34:fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=12|20:x=48:y=h-text_h-60:text='ORANGE 4   LIME 2':enable='gte(t,LEAD)'
```
- Leave out the `fade=t=out` when a replay follows.
- Cost: 16.6–19.9 s per 6.5 s clip, seek included.
- The grade by itself costs about 2.9 s per 2 s of 1080p.

### 4.3 Replay package
Tested: 2.5 s of source becomes exactly 150 frames (5.000 s) and 240000 audio samples. Put the graph in a file and pass it with `-/filter_complex FILE`.
```
[0:v]fps=30,trim=end_frame=NIN,setpts=N/30/TB,scale=1920:1080:in_range=full:out_range=tv:flags=lanczos,setsar=1,crop=CW:CH:CX:CY,hqdn3d=1.5:1.5:6:6,minterpolate=fps=60:mi_mode=mci,setpts=2*PTS,fps=30,scale=1920:1080:flags=lanczos,PERSPECTIVE,curves=master='0/0 0.12/0.10 0.5/0.58 0.85/0.9 1/1',eq=saturation=1.25,unsharp=5:5:0.8:5:5:0,vignette=angle=PI/6,tpad=stop_mode=clone:stop=6,trim=end_frame=NOUT,setpts=N/30/TB,fade=t=in:st=0:d=0.2:color=white,fade=t=out:st=DUR-0.15:d=0.15,drawtext=fontfile='C\:/Windows/Fonts/segoeuib.ttf':text='REPLAY':fontsize=34:fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=10|18:x=w-text_w-60:y=56:enable='between(t,0.15,DUR-0.2)',format=yuv420p[v];[0:a]aresample=48000,aformat=sample_fmts=s16:channel_layouts=stereo,atrim=end_sample=NIN*1600,asetpts=N/SR/TB,atempo=0.5,volume=0.3,afade=t=in:d=0.2,afade=t=out:st=DUR-0.4:d=0.4,apad,atrim=end_sample=NOUT*1600,asetpts=N/SR/TB[a]
```
- **PERSPECTIVE:** substitute Z, L and T as text before running.
  - TX = (rim_x − CX) × 1920/CW and TY = (rim_y − CY) × 1080/CH.
  - `max(in-1,0)` compensates for the frame counter starting at 1 in this build.
  - Leave the filter out entirely when PUSH is 1.0.
```
Z = (1+(PUSH-1)*(1-cos(PI*min(max(in-1,0)/NOUT,1)))/2)
L = max(0,min(W-W/Z,TX-W/Z/2))
T = max(0,min(H-H/Z,TY-H/Z/2))
perspective=eval=frame:interpolation=cubic:sense=source:x0='L':y0='T':x1='L+W/Z':y1='T':x2='L':y2='T+H/Z':x3='L+W/Z':y3='T+H/Z'
```
- **Cost:** 42–54 s per replay.
  - `minterpolate` uses one thread, so run about 6 replays in parallel.
  - Always interpolate before any zoom, text or flash. The other order was about 2.4x slower.
- **Fallback if the ball smears:** replace `minterpolate=fps=60:mi_mode=mci,setpts=2*PTS,fps=30` with `framerate=fps=60,setpts=2*PTS,fps=30`. That takes about 1 s but ghosts moving limbs.
- A working example graph: `stylecheck\s02_replay.mov.graph.txt`.

### 4.4 Title and end card
The inputs are the Pillow PNG and the source as the audio input.
```
-loop 1 -framerate 30 -t SECS+0.2 -i card.png -ss AMB_START -t SECS+0.3 -i SRC
[0:v]fps=30,trim=end_frame=N,setpts=N/30/TB,scale=1920:1080:out_range=tv,setsar=1,fade=t=in:st=0:d=0.4,fade=t=out:st=SECS-FO:d=FO,format=yuv420p[v];[1:a]aresample=48000,aformat=sample_fmts=s16:channel_layouts=stereo,atrim=end_sample=N*1600,asetpts=N/SR/TB,volume=0.5,afade=t=in:d=0.5,afade=t=out:st=SECS-FO:d=FO[a]
```
FO is 0.3 for the title and 1.0 for the end card. Cost: 3.5–8.6 s.

### 4.5 Joining and mastering
- **List file:** one line per segment, `file 'ABS_PATH.mov'`.
- **Pass 1** (measure loudness):
```
ffmpeg -f concat -safe 0 -i list.txt -vn -af highpass=f=70,loudnorm=I=-14:TP=-2:LRA=11:print_format=json -f null -
```
- **Pass 2** (the master):
```
ffmpeg -f concat -safe 0 -i list.txt -c:v copy -af "highpass=f=70,loudnorm=I=-14:TP=-2:LRA=11:measured_I=..:measured_TP=..:measured_LRA=..:measured_thresh=..:offset=..:linear=true,aresample=48000" -c:a aac -b:a 192k -ar 48000 -movflags +faststart recap_master.mp4
```
- **Share copy:**
```
-c:v libx264 -preset medium -crf 23 -maxrate 8M -bufsize 16M -g 60 -pix_fmt yuv420p -profile:v high -level 4.1 -color_range tv -colorspace bt709 -color_primaries bt709 -color_trc bt709 -c:a copy -movflags +faststart
```
  Cost: about 1.6 s of encoding per second of video (preset slow at CRF 20 took about 3.3 s per second).
- **Check the result:** `ffmpeg -v error -i out.mp4 -f null -` must print nothing.

### 4.6 Alternatives (tested in report 3, not used by default)
- **Crossfade between two clips:** `xfade=transition=fade:duration=0.25:offset=OFF` with `acrossfade=d=0.25:c1=tri:c2=tri`.
  - Both inputs need `fps=30,settb=AVTB` first.
  - Offsets chain as off_i = off_{i−1} + d_{i−1} − xf_{i−1}.
- **Freeze frame:** `loop=loop=45:size=1:start=F,setpts=N/30/TB`.
- **Flash on a freeze:** `eq=brightness='0.5*max(0,1-(t-T0)/0.12)*between(t,T0,T0+0.12)':eval=frame`.
- **Fallback zoom:**
```
scale=3840:-2,zoompan=z='1+(1-cos(PI*min(on/45,1)))/2':x='max(0,min(iw-iw/zoom,2*TX-iw/zoom/2))':y='max(0,min(ih-ih/zoom,2*TY-ih/zoom/2))':d=1:s=1920x1080:fps=30
```
  It wobbles 0.73 px RMS, against 0.01 px for `perspective`.

## 5. What looks cheap or amateurish, so avoid it
1. **Slowed audio pitched down** (the `asetrate` "whale" sound). Use `atempo`, or mute.
2. **Slowing to 0.25x or below with `minterpolate`** on a 30 fps source. The ball and hands warp. Also never interpolate across a cut or flash.
3. **Zooming too far:** above 1.8x at the near rim, or above 2.5x at the far rim. `zoompan` at native 1080p shudders. Zoom moves on live clips, pans or zoom-outs all look wrong too.
4. **A replay on every basket, or two replays of one play.** Full-game recaps replay only standout plays.
5. **White flashes on every cut, shake or glitch effects, speed ramps everywhere, or flashy xfades** (pixelize, circlecrop, radial, squeeze, wind, slide). The only flash is the one into a replay.
6. **Hard cuts between two wide shots in version A.** From a fixed camera they read as jump cuts, so use the 0.3 s dip. Version B keeps pure cuts because it was asked for with no effects.
7. **Stacked overlays, a replay tag in team colour** (orange), a tally that shows during replays, or a tally counting "points" under unknown pickup rules.
8. **Recruiting-reel devices in a game recap or the plain reel:** freeze frames, spotlight rings, arrows, a heavy vignette.
9. **Music beds, whooshes or rewind sound effects.** This edit uses natural audio only.
10. **Long lead-ins over 6 s, or clips over 10 s in A.** Also including the camera being moved, or dead time between games.