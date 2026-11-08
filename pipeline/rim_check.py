"""Frame-by-frame rim check: every source frame around the rim moment, tight crop, upscaled,
plus a difference-vs-empty-rim view so the ball stands out from the net.

  python rim_check.py --t <rim time s> --rim x,y [--half 60] [--span 0.9] [--ref <time of an empty-rim frame>] --out sheet.jpg

Reading it: a MAKE shows the ball (bright blob in the diff row) passing INSIDE the net outline
from the rim down to the bottom opening, net strands in front of AND behind it, the net bulging /
swinging, and the ball leaving through the bottom centre. A MISS shows the blob leaving sideways,
upward, or dropping beside the net silhouette with the net outline unchanged.
"""
import argparse, subprocess, numpy as np, cv2, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bbconfig import VIDEO

ap = argparse.ArgumentParser()
ap.add_argument("--t", type=float, required=True)
ap.add_argument("--rim", required=True)
ap.add_argument("--half", type=int, default=60, help="half width of the crop around the rim (px)")
ap.add_argument("--span", type=float, default=0.9, help="seconds before and after --t")
ap.add_argument("--ref", type=float, default=None, help="time of a frame with an empty, still rim")
ap.add_argument("--tile", type=int, default=240)
ap.add_argument("--cols", type=int, default=9)
ap.add_argument("--out", required=True)
a = ap.parse_args()
rx, ry = (int(v) for v in a.rim.split(","))
hw = a.half
x0, y0 = rx - hw, ry - int(hw * 0.7)
w, h = 2 * hw, int(hw * 2.2)


def grab(start, dur):
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{start:.3f}", "-i", VIDEO, "-t", f"{dur:.3f}",
           "-vf", f"crop={w}:{h}:{x0}:{y0}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    n = len(raw) // (w * h * 3)
    return np.frombuffer(raw[: n * w * h * 3], np.uint8).reshape(n, h, w, 3)


start = a.t - a.span
frames = grab(start, 2 * a.span)
ref_t = a.ref if a.ref is not None else a.t - a.span - 1.5
ref = np.median(grab(ref_t, 0.5).astype(np.float32), axis=0)
tiles = []
for i, f in enumerate(frames):
    t = start + i / 30
    big = cv2.resize(f, (a.tile, int(a.tile * h / w)), interpolation=cv2.INTER_CUBIC)
    d = np.abs(f.astype(np.float32) - ref).max(axis=2)
    d = np.clip(d * 3, 0, 255).astype(np.uint8)
    d = cv2.applyColorMap(d, cv2.COLORMAP_INFERNO)
    dbig = cv2.resize(d, big.shape[1::-1], interpolation=cv2.INTER_NEAREST)
    # rim line guide
    for im in (big, dbig):
        yy = int((ry - y0) * big.shape[0] / h)
        cv2.line(im, (0, yy), (6, yy), (0, 255, 255), 1)
        cv2.line(im, (im.shape[1] - 7, yy), (im.shape[1] - 1, yy), (0, 255, 255), 1)
    col = np.vstack([big, dbig])
    cv2.putText(col, f"{int(t // 60)}:{t % 60:05.2f}", (4, 16), 0, 0.5, (0, 255, 255), 1)
    tiles.append(col)
rows = [np.hstack(tiles[i:i + a.cols] + [np.zeros_like(tiles[0])] * (a.cols - len(tiles[i:i + a.cols])))
        for i in range(0, len(tiles), a.cols)]
cv2.imwrite(a.out, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 88])
print(a.out, len(frames), "frames")
