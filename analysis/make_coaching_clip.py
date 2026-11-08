"""Render one captioned coaching clip from the offense reel (captions in Hebrew or English, rendered as PNG overlays).

  python make_coaching_clip.py spec.json
spec = {
  "reel": "<path to reel mp4>", "out": "<out.mp4>",
  "live": {"start": 189.78, "end": 199.73,
           "captions": [{"from": 0.0, "to": 4.0, "text": "..."}, ...]},      # times relative to live start
  "replay": {"t": 194.75, "pre": 1.5, "post": 1.0, "speed": 0.5, "center": [470, 560], "crop_w": 960,
             "caption": "...", "freeze": {"at": 194.75, "secs": 1.6, "ring": [470, 440], "caption": "..."}},
  "tags": {"live": "לייב", "replay": "הילוך איטי", "freeze": "סטופ"},         # optional corner tags
  "stills": [{"image": "<png/jpg>", "secs": 3.5, "caption": "...", "tag": "סימולציה"}]   # optional, shown after the freeze
}
Output: live (with caption bar) -> slow-motion replay (crop + caption) -> freeze frame with a ring -> fade.
All intermediates are 1920x1080 30 fps, x264 crf 18, pcm audio; joined with the concat demuxer.
"""
import json, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw
from captions import overlay_png

spec = json.load(open(sys.argv[1], encoding="utf-8"))
tmp = tempfile.mkdtemp(prefix="coach_")
TAGS = {"live": "לייב", "replay": "הילוך איטי", "freeze": "סטופ"}
TAGS.update(spec.get("tags", {}))
ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-g", "60", "-pix_fmt", "yuv420p", "-video_track_timescale", "15360",
       "-color_range", "tv", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2"]


def run(args, label):
    r = subprocess.run(["ffmpeg", "-v", "error", "-y"] + args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        raise SystemExit(f"{label} failed:\n{r.stderr[-3000:]}")


parts = []
# 1. live segment with timed caption overlays
lv = spec["live"]
dur = lv["end"] - lv["start"]
n = int(round(dur * 30))
caps = lv.get("captions", [])
inputs = ["-ss", f"{lv['start']:.3f}", "-t", f"{dur + 0.3:.3f}", "-i", spec["reel"]]
chain = [f"[0:v]fps=30,trim=end_frame={n},setpts=N/30/TB[v0]"]
last = "v0"
for i, c in enumerate(caps):
    png = overlay_png(os.path.join(tmp, f"cap{i}.png"), caption=c["text"], tag=TAGS.get("live") if i == 0 else None)
    inputs += ["-i", png]
    chain.append(f"[{last}][{i + 1}:v]overlay=0:0:format=auto:enable='between(t,{c['from']},{c['to']})'[v{i + 1}]")
    last = f"v{i + 1}"
chain.append(f"[{last}]format=yuv420p[v]")
af = f"[0:a]aresample=48000,aformat=sample_fmts=s16:channel_layouts=stereo,atrim=end_sample={n * 1600},asetpts=N/SR/TB,afade=t=in:d=0.05,afade=t=out:st={dur - 0.05}:d=0.05[a]"
live = os.path.join(tmp, "live.mov")
run(inputs + ["-filter_complex", ";".join(chain) + ";" + af, "-map", "[v]", "-map", "[a]"] + ENC + [live], "live")
parts.append(live)

# 2. slow-motion replay on a crop around the shooter
rp = spec.get("replay")
if rp:
    s, e = rp["t"] - rp["pre"], rp["t"] + rp["post"]
    nin = int(round((e - s) * 30))
    speed = rp.get("speed", 0.5)
    nout = int(round(nin / speed))
    cw = rp.get("crop_w", 960); ch = int(cw * 9 / 16)
    cx, cy = rp["center"]
    x0 = int(max(0, min(1920 - cw, cx - cw / 2))); y0 = int(max(0, min(1080 - ch, cy - ch / 2)))
    png = overlay_png(os.path.join(tmp, "rcap.png"), caption=rp["caption"], tag=TAGS.get("replay"))
    vf = (f"[0:v]fps=30,trim=end_frame={nin},setpts=N/30/TB,crop={cw}:{ch}:{x0}:{y0},hqdn3d=1.5:1.5:6:6,"
          f"minterpolate=fps={int(round(30 / speed))}:mi_mode=mci,setpts={1 / speed}*PTS,fps=30,scale=1920:1080:flags=lanczos,"
          f"unsharp=5:5:0.6:5:5:0,trim=end_frame={nout},setpts=N/30/TB,fade=t=in:st=0:d=0.2:color=white[base];"
          f"[base][1:v]overlay=0:0:format=auto,format=yuv420p[v]")
    af = (f"[0:a]aresample=48000,aformat=sample_fmts=s16:channel_layouts=stereo,atrim=end_sample={nin * 1600},asetpts=N/SR/TB,"
          f"atempo={speed},volume=0.3,afade=t=in:d=0.2,apad,atrim=end_sample={nout * 1600},asetpts=N/SR/TB[a]")
    rep = os.path.join(tmp, "replay.mov")
    run(["-ss", f"{s:.3f}", "-t", f"{e - s + 0.3:.3f}", "-i", spec["reel"], "-i", png, "-filter_complex", f"{vf};{af}",
         "-map", "[v]", "-map", "[a]"] + ENC + [rep], "replay")
    parts.append(rep)

    # 3. freeze frame with a ring + caption
    fz = rp.get("freeze")
    if fz:
        secs = fz.get("secs", 1.6)
        nf = int(round(secs * 30))
        rx, ry = fz["ring"]
        ring = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
        d = ImageDraw.Draw(ring)
        sx, sy = 1920 / cw, 1080 / ch
        px, py = (rx - x0) * sx, (ry - y0) * sy
        r = 90
        for wdt, col in ((10, (0, 0, 0, 160)), (6, (239, 59, 36, 255))):
            d.ellipse([px - r, py - r, px + r, py + r], outline=col, width=wdt)
        rpng = os.path.join(tmp, "ring.png"); ring.save(rpng)
        fpng = overlay_png(os.path.join(tmp, "fcap.png"), caption=fz["caption"], tag=TAGS.get("freeze"))
        vf = (f"[0:v]fps=30,trim=end_frame=1,setpts=N/30/TB,crop={cw}:{ch}:{x0}:{y0},scale=1920:1080:flags=lanczos,unsharp=5:5:0.6:5:5:0,"
              f"loop=loop={nf - 1}:size=1:start=0,setpts=N/30/TB[base];[base][1:v]overlay=0:0:format=auto[b2];[b2][2:v]overlay=0:0:format=auto,"
              f"fade=t=out:st={secs - 0.4}:d=0.4,format=yuv420p[v]")
        frz = os.path.join(tmp, "freeze.mov")
        run(["-ss", f"{fz['at']:.3f}", "-t", "0.2", "-i", spec["reel"], "-i", rpng, "-i", fpng, "-f", "lavfi", "-t", f"{secs}", "-i", "anullsrc=r=48000:cl=stereo",
             "-filter_complex", vf, "-map", "[v]", "-map", "3:a", "-shortest"] + ENC + [frz], "freeze")
        parts.append(frz)

# 4. optional still images (e.g. a simulation composite), each held for a few seconds with its own caption and tag
for i, st in enumerate(spec.get("stills", [])):
    secs = st.get("secs", 3.5)
    img = Image.open(st["image"]).convert("RGB").resize((1920, 1080), Image.LANCZOS)
    ipng = os.path.join(tmp, f"still{i}.png"); img.save(ipng)
    cpng = overlay_png(os.path.join(tmp, f"stillcap{i}.png"), caption=st.get("caption"), tag=st.get("tag"))
    out = os.path.join(tmp, f"still{i}.mov")
    vf = (f"[0:v]fps=30,loop=loop={int(round(secs * 30)) - 1}:size=1:start=0,setpts=N/30/TB[base];[base][1:v]overlay=0:0:format=auto,"
          f"fade=t=in:st=0:d=0.3,fade=t=out:st={secs - 0.4}:d=0.4,format=yuv420p[v]")
    run(["-i", ipng, "-i", cpng, "-f", "lavfi", "-t", f"{secs}", "-i", "anullsrc=r=48000:cl=stereo",
         "-filter_complex", vf, "-map", "[v]", "-map", "2:a", "-shortest"] + ENC + [out], "still")
    parts.append(out)

lst = os.path.join(tmp, "list.txt")
open(lst, "w", encoding="utf-8").write("\n".join(f"file '{p.replace(chr(92), '/')}'" for p in parts))
run(["-f", "concat", "-safe", "0", "-i", lst, "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", spec["out"]], "concat")
print("wrote", spec["out"], "parts", len(parts))
