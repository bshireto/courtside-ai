"""Side-by-side comparison clip: two moments of the reel in slow motion next to each other, then both release frames frozen.

  python make_compare_clip.py spec.json
spec = {"reel": "...", "out": "...",
        "left":  {"t": 8.4,  "center": [640, 560], "label": "..."},
        "right": {"t": 19.1, "center": [640, 560], "label": "..."},
        "pre": 1.5, "post": 1.0, "speed": 0.5, "caption": "...", "freeze_caption": "...", "freeze_secs": 2.5,
        "tags": {"replay": "הילוך איטי", "freeze": "סטופ"}}
Each side is a 960x1080 window around its centre; the two windows are joined into one 1920x1080 frame.
"""
import json, os, subprocess, sys, tempfile
from captions import overlay_png

spec = json.load(open(sys.argv[1], encoding="utf-8"))
tmp = tempfile.mkdtemp(prefix="cmp_")
TAGS = {"replay": "הילוך איטי", "freeze": "סטופ"}
TAGS.update(spec.get("tags", {}))
ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-g", "60", "-pix_fmt", "yuv420p", "-video_track_timescale", "15360",
       "-color_range", "tv", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2"]


def run(args, label):
    r = subprocess.run(["ffmpeg", "-v", "error", "-y"] + args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        raise SystemExit(f"{label} failed:\n{r.stderr[-3000:]}")


pre, post, speed = spec.get("pre", 1.5), spec.get("post", 1.0), spec.get("speed", 0.5)
nin = int(round((pre + post) * 30)); nout = int(round(nin / speed))
L, R = spec["left"], spec["right"]


def crop_x(c):
    return int(max(0, min(1920 - 960, c[0] - 480)))


labels = [(40, 40, L["label"]), (1000, 40, R["label"])]
png = overlay_png(os.path.join(tmp, "cap.png"), caption=spec["caption"], tag=TAGS.get("replay"), labels=labels, tag_pos="center")
parts = []
# slow motion, both sides
vf = ""
for k, (side, idx) in enumerate(((L, 0), (R, 1))):
    vf += (f"[{idx}:v]fps=30,trim=end_frame={nin},setpts=N/30/TB,crop=960:1080:{crop_x(side['center'])}:0,hqdn3d=1.5:1.5:6:6,"
           f"minterpolate=fps={int(round(30 / speed))}:mi_mode=mci,setpts={1 / speed}*PTS,fps=30,trim=end_frame={nout},setpts=N/30/TB[s{k}];")
vf += f"[s0][s1]hstack=inputs=2[h];[h][2:v]overlay=0:0:format=auto,fade=t=in:st=0:d=0.2:color=white,format=yuv420p[v]"
rep = os.path.join(tmp, "replay.mov")
run(["-ss", f"{L['t'] - pre:.3f}", "-t", f"{pre + post + 0.3:.3f}", "-i", spec["reel"],
     "-ss", f"{R['t'] - pre:.3f}", "-t", f"{pre + post + 0.3:.3f}", "-i", spec["reel"], "-i", png,
     "-f", "lavfi", "-t", f"{nout / 30:.3f}", "-i", "anullsrc=r=48000:cl=stereo",
     "-filter_complex", vf, "-map", "[v]", "-map", "3:a", "-shortest"] + ENC + [rep], "replay")
parts.append(rep)
# freeze on both release frames
secs = spec.get("freeze_secs", 2.5); nf = int(round(secs * 30))
fpng = overlay_png(os.path.join(tmp, "fcap.png"), caption=spec.get("freeze_caption", spec["caption"]), tag=TAGS.get("freeze"), labels=labels, tag_pos="center")
vf = ""
for k, (side, idx) in enumerate(((L, 0), (R, 1))):
    vf += f"[{idx}:v]fps=30,trim=end_frame=1,setpts=N/30/TB,crop=960:1080:{crop_x(side['center'])}:0,unsharp=5:5:0.6:5:5:0,loop=loop={nf - 1}:size=1:start=0,setpts=N/30/TB[f{k}];"
vf += f"[f0][f1]hstack=inputs=2[h];[h][2:v]overlay=0:0:format=auto,fade=t=out:st={secs - 0.4}:d=0.4,format=yuv420p[v]"
frz = os.path.join(tmp, "freeze.mov")
run(["-ss", f"{L['t']:.3f}", "-t", "0.2", "-i", spec["reel"], "-ss", f"{R['t']:.3f}", "-t", "0.2", "-i", spec["reel"], "-i", fpng,
     "-f", "lavfi", "-t", f"{secs}", "-i", "anullsrc=r=48000:cl=stereo", "-filter_complex", vf, "-map", "[v]", "-map", "3:a", "-shortest"] + ENC + [frz], "freeze")
parts.append(frz)
lst = os.path.join(tmp, "list.txt")
open(lst, "w", encoding="utf-8").write("\n".join(f"file '{p.replace(chr(92), '/')}'" for p in parts))
run(["-f", "concat", "-safe", "0", "-i", lst, "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", spec["out"]], "concat")
print("wrote", spec["out"])
