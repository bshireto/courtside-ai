"""The exact frame make_drive_video.py freezes on at a reel time, as a zoomed crop with a pixel grid (FULL-FRAME coordinates).
Use it for every stop: the 10 fps pictures in work/frames/ are up to one frame (0.033 s) away from what the video tool shows.

  python freeze_grid.py <out.jpg> <reel_t> <x0> <y0> <x1> <y1> [--scale 2] [--step 40] [--plain]
"""
import os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REEL = os.path.join(HERE, "..", "recap_2026-10-07", "output", "Barak_Offense_Reel_master.mp4")
args = sys.argv[1:]
scale, step, plain = 2.0, 40, False
if "--scale" in args:
    i = args.index("--scale"); scale = float(args[i + 1]); del args[i:i + 2]
if "--step" in args:
    i = args.index("--step"); step = int(args[i + 1]); del args[i:i + 2]
if "--plain" in args:
    plain = True; args.remove("--plain")
out, at = args[0], float(args[1]); x0, y0, x1, y1 = (int(float(a)) for a in args[2:6])
x0, y0, x1, y1 = max(0, x0), max(0, y0), min(1920, x1), min(1080, y1)
full = os.path.join(tempfile.mkdtemp(prefix="fz_"), "f.png")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{at:.3f}", "-t", "0.2", "-i", REEL, "-vf", "fps=30,trim=end_frame=1", "-frames:v", "1", full], check=True)
W, H = int((x1 - x0) * scale), int((y1 - y0) * scale)
im = Image.open(full).convert("RGB").crop((x0, y0, x1, y1)).resize((W, H), Image.LANCZOS)
if not plain:
    d = ImageDraw.Draw(im); f = ImageFont.truetype("arial.ttf", 15)
    gx = (x0 // step + 1) * step
    while gx < x1:
        X = (gx - x0) * scale; d.line([X, 0, X, H], fill=(255, 255, 255), width=1); d.text((X + 2, 2), str(gx), fill="yellow", font=f); gx += step
    gy = (y0 // step + 1) * step
    while gy < y1:
        Y = (gy - y0) * scale; d.line([0, Y, W, Y], fill=(255, 255, 255), width=1); d.text((2, Y + 2), str(gy), fill="yellow", font=f); gy += step
im.save(out, quality=88)
print("wrote", out, im.size, f"reel {at}")
