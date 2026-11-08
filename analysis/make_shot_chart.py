"""Shot chart drawn on the real court: median background (players removed) + the 3-point arc + one dot per shot.
Writes shot_chart_full.jpg (1920x1080) and shot_chart.jpg (zoomed crop of the half court, 2x).
"""
import json, os, glob
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.join(HERE, "..", "recap_2026-10-07")
FR = os.path.join(HERE, "work", "frames")
cfg = json.load(open(os.path.join(GAME, "game.json"), encoding="utf-8"))
arc = cfg["hoops"]["A"]["arc"]
GREEN, RED, WHITE = (0, 124, 50), (217, 20, 0), (255, 255, 255)

# 1. background = per-pixel median of 25 frames spread over the reel (moving players vanish)
files = sorted(glob.glob(os.path.join(FR, "*.jpg")))
pick = files[20:-120:max(1, (len(files) - 140) // 25)][:25]
stack = np.stack([np.asarray(Image.open(f).convert("RGB")) for f in pick])  # (n,1080,1920,3) uint8
bg = np.empty(stack.shape[1:], np.uint8)
for y in range(0, 1080, 90):
    bg[y:y + 90] = np.median(stack[:, y:y + 90], axis=0).astype(np.uint8)
bg = Image.fromarray(bg)
bg = Image.blend(bg, Image.new("RGB", bg.size, (0, 0, 0)), 0.25)
d = ImageDraw.Draw(bg)

# 2. court lines from game.json
near = [tuple(arc["apex"])] + [tuple(p) for p in arc["near"]]
far = [tuple(arc["apex"])] + [tuple(p) for p in arc["far"]]
d.line(near, fill=WHITE, width=3)
d.line(far, fill=WHITE, width=3)
d.line([tuple(p) for p in arc["baseline"]], fill=WHITE, width=2)

# 3. shots, chronological (feet position at release, full-frame px). s011/s018 positions come from the reviewers' notes.
shots = [
    ("c007", 648, 638, True, 2, "pull-up long 2, top"),
    ("c008", 633, 630, False, 2, "pull-up long 2, top"),
    ("c013", 528, 597, False, 3, "pull-up 3, top, off the check"),
    ("c017", 463, 600, False, 3, "deep 3, contested, airball"),
    ("c035", 822, 596, True, 2, "one-foot runner, far elbow"),
    ("c036", 803, 585, False, 2, "catch-and-shoot long 2, far wing"),
    ("s011", 853, 585, False, 2, "two-hand shot at the FT line, altered"),
    ("c049", 1133, 648, False, 2, "driving layup through contact"),
    ("s018", 1120, 565, False, 2, "pull-up long 2, far side"),
    ("c077", 462, 650, True, 3, "pull-up 3, top, open"),
    ("c078", 470, 643, True, 3, "pull-up 3, top"),
    ("c089", 1040, 597, True, 2, "running hook in the lane"),
    ("c107", 820, 606, False, 2, "pull-up, far elbow, contested"),
]
font = ImageFont.truetype("arialbd.ttf", 20)
font_s = ImageFont.truetype("arialbd.ttf", 16)
# nudge dots that would sit on top of an earlier one (same spot, different possession)
placed = []
drawn = []
for n, (sid, x, y, made, pts, lab) in enumerate(shots, 1):
    dx = 0
    while any(abs(x + dx - px) < 30 and abs(y - py) < 30 for px, py in placed):
        dx += 34
    placed.append((x + dx, y))
    drawn.append((sid, x + dx, y, made, pts, lab))
for n, (sid, x, y, made, pts, _) in enumerate(drawn, 1):
    r = 15
    col = GREEN if made else RED
    d.ellipse([x - r - 2, y - r - 2, x + r + 2, y + r + 2], fill=(0, 0, 0))
    if made:
        d.ellipse([x - r, y - r, x + r, y + r], fill=col, outline=WHITE, width=2)
    else:
        d.ellipse([x - r, y - r, x + r, y + r], fill=(40, 40, 40), outline=col, width=4)
    lab = str(n)
    w = d.textlength(lab, font=font_s)
    d.text((x - w / 2, y - 9), lab, fill=WHITE, font=font_s)

# legend
d.rectangle([40, 940, 760, 1050], fill=(0, 0, 0))
d.ellipse([60, 965, 84, 989], fill=GREEN, outline=WHITE, width=2); d.text((95, 965), "make (5)", fill=WHITE, font=font)
d.ellipse([230, 965, 254, 989], fill=(40, 40, 40), outline=RED, width=4); d.text((265, 965), "miss (8)", fill=WHITE, font=font)
d.text((60, 1005), "numbers = order in the game  |  dot = feet at the release (dots from the same spot are nudged right)  |  white = 3-point line", fill=(220, 220, 220), font=font_s)
bg.save(os.path.join(HERE, "shot_chart_full.jpg"), quality=90)
crop = bg.crop((380, 430, 1400, 790)).resize((2040, 720), Image.LANCZOS)
crop.save(os.path.join(HERE, "shot_chart.jpg"), quality=90)
json.dump([{"n": n, "id": s[0], "x": s[1], "y": s[2], "made": s[3], "points": s[4], "label": s[5]} for n, s in enumerate(shots, 1)],
          open(os.path.join(HERE, "shot_chart.json"), "w"), indent=1)
print("ok", len(pick), "background frames")
