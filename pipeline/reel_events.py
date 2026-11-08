"""Pop-up stat events on the personal reel: when the player scores or assists, show
"+2 PTS" / "ASSIST" with his running line (e.g. "BARAK  4 PTS  3 AST") top-right for 3 s,
then remove it. Works on the rendered reel clips (r000.mov ...) in clip order.

  python reel_events.py clips.json events.json clipdir name
events.json: [{"t": seconds in source video, "type": "2pt"|"3pt"|"assist"}]
Writes r###_ev.mov next to affected clips and prints the concat order to stdout (list file).
"""
import json, os, subprocess, sys

clips = sorted(json.load(open(sys.argv[1])), key=lambda c: c["start"])
events = sorted(json.load(open(sys.argv[2])), key=lambda e: e["t"])
cdir, name = sys.argv[3], sys.argv[4]
FONT = "C\\:/Windows/Fonts/segoeuib.ttf"
pts = ast = 0
line_at = []
for e in events:
    if e["type"] == "assist":
        ast += 1; pop = "ASSIST"
    else:
        pts += 3 if e["type"] == "3pt" else 2; pop = "+3 PTS" if e["type"] == "3pt" else "+2 PTS"
    line_at.append((e["t"], pop, f"{name.upper()}   {pts} PTS   {ast} AST"))

out = []
for i, c in enumerate(clips):
    src = os.path.join(cdir, f"r{i:03d}.mov")
    evs = [x for x in line_at if c["start"] <= x[0] <= c["end"]]
    if not evs:
        out.append(src); continue
    vf = []
    for t, pop, line in evs:
        a, b = t - c["start"] + 0.2, t - c["start"] + 3.2
        alpha = f"if(lt(t,{a}+0.25),(t-{a})/0.25,if(gt(t,{b}-0.3),({b}-t)/0.3,1))"
        vf.append(f"drawtext=fontfile='{FONT}':text='{pop}':fontsize=64:fontcolor=white:box=1:boxcolor=0xE8661A@0.9:"
                  f"boxborderw=14|26:x=w-text_w-70:y=60:alpha='{alpha}':enable='between(t,{a},{b})'")
        vf.append(f"drawtext=fontfile='{FONT}':text='{line}':fontsize=34:fontcolor=white:box=1:boxcolor=black@0.6:"
                  f"boxborderw=10|20:x=w-text_w-70:y=175:alpha='{alpha}':enable='between(t,{a},{b})'")
    dst = os.path.join(cdir, f"r{i:03d}_ev.mov")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", ",".join(vf), "-c:v", "libx264", "-preset", "medium",
                    "-crf", "17", "-g", "60", "-pix_fmt", "yuv420p", "-video_track_timescale", "15360", "-c:a", "copy", dst], check=True)
    out.append(dst)
print("\n".join(f"file '{p}'" for p in out))
