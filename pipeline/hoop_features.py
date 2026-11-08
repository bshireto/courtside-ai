"""Per-frame motion / ball-colour features in the net zones of every hoop.

One ffmpeg pass crops the hoop ROIs out of every frame (30 fps) and pipes them
here as a single horizontal strip. For each hoop we track a slow running
background and measure, per zone (above rim / net / below net):
  fg   - fraction of pixels that differ from the background
  ball - fraction of those that are also basketball-coloured
Output: features.csv (one row per frame).
"""
import subprocess, sys, os, numpy as np, cv2, csv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bbconfig

VIDEO = bbconfig.VIDEO
OUT = bbconfig.data("hoop_features.csv")
W, H = 1920, 1080

# name: (x0, y0, x1, y1, rim_y, net_x0, net_x1, net_y1) in full-frame pixels
HOOPS = {k: (*h["roi"], h["rim_y"], *h["net"]) for k, h in bbconfig.HOOPS.items()}
PADH = max(h[3] - h[1] for h in HOOPS.values())
chain, labels, x_off = [], [], {}
off = 0
for i, (k, (x0, y0, x1, y1, *_)) in enumerate(HOOPS.items()):
    # fps=30 forces constant frame rate, so row n is exactly t = n/30 even when the phone dropped frames
    chain.append(f"[0:v]fps=30,crop={x1-x0}:{y1-y0}:{x0}:{y0},pad={x1-x0}:{PADH}:0:0[c{i}]")
    labels.append(f"[c{i}]")
    x_off[k] = off
    off += x1 - x0
TW = off
if len(HOOPS) > 1:
    fc = ";".join(chain) + ";" + "".join(labels) + f"hstack=inputs={len(HOOPS)}[out]"
else:  # a single hoop: no hstack (ffmpeg needs >= 2 inputs)
    fc = chain[0].replace("[c0]", "[out]")
cmd = ["ffmpeg", "-v", "error", "-threads", "8", "-i", VIDEO, "-filter_complex", fc,
       "-map", "[out]", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=TW * PADH * 3 * 8)

def zones(k):
    x0, y0, x1, y1, rim_y, nx0, nx1, ny1 = HOOPS[k]
    rw = nx1 - nx0
    rh = max(8, int((ny1 - rim_y) * 1.2))
    ox = x_off[k]
    def box(a, b, c, d):
        a, c = max(a, x0), min(c, x1)
        b, d = max(b, y0), min(d, y1)
        return (ox + a - x0, b - y0, ox + c - x0, d - y0)
    return {
        "above": box(nx0 - rw // 2, rim_y - 2 * rh, nx1 + rw // 2, rim_y - 2),
        "net":   box(nx0, rim_y + 2, nx1, ny1),
        "below": box(nx0 - rw // 4, ny1, nx1 + rw // 4, ny1 + rh),
    }

Z = {k: zones(k) for k in HOOPS}
bg = None
fields = ["frame", "t"] + [f"{k}_{z}_{m}" for k in HOOPS for z in ("above", "net", "below") for m in ("fg", "ball")]
f = open(OUT, "w", newline="")
wr = csv.writer(f)
wr.writerow(fields)
n = 0
fsz = TW * PADH * 3
while True:
    buf = proc.stdout.read(fsz)
    if len(buf) < fsz:
        break
    img = np.frombuffer(buf, np.uint8).reshape(PADH, TW, 3)
    if bg is None:
        bg = img.astype(np.float32)
    d = cv2.absdiff(img, cv2.convertScaleAbs(bg))
    dm = cv2.max(cv2.max(d[..., 0], d[..., 1]), d[..., 2])
    fg = (dm > 28).astype(np.uint8)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    ballc = cv2.bitwise_or(cv2.inRange(hsv, (0, 70, 45), (22, 255, 255)),
                           cv2.inRange(hsv, (172, 70, 45), (180, 255, 255)))
    fgb = cv2.bitwise_and(fg, fg, mask=ballc)
    row = [n, round(n / 30.0, 3)]
    for k in HOOPS:
        for zn in ("above", "net", "below"):
            a, b, c, dd = Z[k][zn]
            area = max(1, (c - a) * (dd - b))
            row.append(round(cv2.countNonZero(fg[b:dd, a:c]) / area, 4))
            row.append(round(cv2.countNonZero(fgb[b:dd, a:c]) / area, 4))
    wr.writerow(row)
    # slow background, frozen where foreground (so passing balls don't burn in)
    cv2.accumulateWeighted(img, bg, 0.05, mask=1 - fg)
    cv2.accumulateWeighted(img, bg, 0.002, mask=fg)
    n += 1
    if n % 3000 == 0:
        print(n, flush=True)
f.close()
print("done", n)
