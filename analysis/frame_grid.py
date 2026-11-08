"""Zoomed crops of reel frames with a pixel grid, for reading full-frame coordinates off a picture.

  python frame_grid.py <out.jpg> <x0> <y0> <x1> <y1> <reel_t> [<reel_t> ...] [--scale 3] [--step 40] [--plain]
Each time becomes one tile (stacked top to bottom): the crop of work/frames/<k>.jpg, enlarged, with grid lines every `step`
full-frame pixels labelled with FULL-FRAME coordinates. --plain leaves the grid out (for judging the picture itself).
Frames exist every 0.1 s: k = round(reel_t * 10) + 1.
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[1:]
scale, step, plain = 3.0, 40, False
if "--scale" in args:
    i = args.index("--scale"); scale = float(args[i + 1]); del args[i:i + 2]
if "--step" in args:
    i = args.index("--step"); step = int(args[i + 1]); del args[i:i + 2]
if "--plain" in args:
    plain = True; args.remove("--plain")
out = args[0]; x0, y0, x1, y1 = (int(float(a)) for a in args[1:5]); times = [float(a) for a in args[5:]]
x0, y0, x1, y1 = max(0, x0), max(0, y0), min(1920, x1), min(1080, y1)
W, H = int((x1 - x0) * scale), int((y1 - y0) * scale)
f = ImageFont.truetype("arial.ttf", 15)
sheet = Image.new("RGB", (W, H * len(times)))
for n, t in enumerate(times):
    k = int(round(t * 10)) + 1
    im = Image.open(os.path.join(HERE, "work", "frames", f"{k:05d}.jpg")).crop((x0, y0, x1, y1)).resize((W, H), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    if not plain:
        gx = x0 - x0 % step + (step if x0 % step else 0)
        for x in range(gx, x1, step):
            X = (x - x0) * scale; d.line([(X, 0), (X, H)], fill=(255, 255, 255), width=1); d.text((X + 3, 2), str(x), fill=(255, 255, 0), font=f)
        gy = y0 - y0 % step + (step if y0 % step else 0)
        for y in range(gy, y1, step):
            Y = (y - y0) * scale; d.line([(0, Y), (W, Y)], fill=(255, 255, 255), width=1); d.text((3, Y + 2), str(y), fill=(255, 255, 0), font=f)
    d.rectangle([W - 150, 0, W, 26], fill=(0, 0, 0)); d.text((W - 144, 4), f"reel {t:.1f}", fill=(255, 90, 90), font=f)
    sheet.paste(im, (0, n * H))
sheet.save(out, quality=86)
print("wrote", out, sheet.size)
