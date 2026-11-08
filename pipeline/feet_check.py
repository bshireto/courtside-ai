"""2-vs-3 check at the release frame (rule 1b): the shooter's feet against the 3-point arc.

  python feet_check.py --t <release s> --xy <shooter x,y (feet)> [--half 170] [--span 0.27] --out sheet.jpg
Top row: raw 30 fps frames around the release (so the painted line itself is visible).
Bottom row: the same frames with the arc from game.json (hoops.<h>.arc) drawn in cyan, to read where the line runs
when a foot or a shadow hides it. A 3 needs BOTH feet outside the arc on the floor at the last frame before take-off.
"""
import argparse, os, subprocess, sys
import numpy as np, cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bbconfig

ap = argparse.ArgumentParser()
ap.add_argument("--t", type=float, required=True)
ap.add_argument("--xy", required=True)
ap.add_argument("--half", type=int, default=170)
ap.add_argument("--span", type=float, default=0.27)
ap.add_argument("--post", type=float, default=0.1)
ap.add_argument("--hoop", default=None)
ap.add_argument("--scale", type=float, default=2.0)
ap.add_argument("--out", required=True)
a = ap.parse_args()
sx, sy = (int(float(v)) for v in a.xy.split(","))
hw = a.half
x0, y0 = max(0, min(1920 - 2 * hw, sx - hw)), max(0, min(1080 - int(1.3 * hw), sy - int(0.95 * hw)))
w, h = 2 * hw, int(1.3 * hw)
hoop = a.hoop or next(iter(bbconfig.HOOPS))
arc = bbconfig.HOOPS[hoop].get("arc") or {}
start = a.t - a.span
raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{start:.3f}", "-i", bbconfig.VIDEO, "-t", f"{a.span + a.post:.3f}",
                      "-vf", f"fps=30,crop={w}:{h}:{x0}:{y0}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True).stdout
n = len(raw) // (w * h * 3)
frames = np.frombuffer(raw[: n * w * h * 3], np.uint8).reshape(n, h, w, 3)
S = a.scale
top, bot = [], []
for i, f in enumerate(frames):
    t = start + i / 30
    big = cv2.resize(f, None, fx=S, fy=S, interpolation=cv2.INTER_CUBIC)
    ov = big.copy()
    for key in ("near", "far"):
        pts = arc.get(key) or []
        if key == "near" and arc.get("apex"):
            pts = [arc["apex"]] + pts
        if key == "far" and arc.get("apex"):
            pts = [arc["apex"]] + pts
        if len(pts) >= 2:
            p = np.array([[(x - x0) * S, (y - y0) * S] for x, y in pts], np.int32)
            cv2.polylines(ov, [p], False, (255, 255, 0), 1, cv2.LINE_AA)
    for im in (big, ov):
        cv2.putText(im, f"{int(t // 60)}:{t % 60:05.2f} f{int(round(t * 30))}", (4, 18), 0, 0.55, (0, 255, 255), 1, cv2.LINE_AA)
    top.append(big); bot.append(ov)
cv2.imwrite(a.out, np.vstack([np.hstack(top), np.hstack(bot)]), [cv2.IMWRITE_JPEG_QUALITY, 90])
print(a.out, n, "frames; crop", (x0, y0, x0 + w, y0 + h))
