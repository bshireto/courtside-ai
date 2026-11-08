"""Net-swing score: how much the NET itself moves after the ball reaches the rim.

A ball that goes through pushes the whole net down and it keeps swinging ~0.3-0.8 s.
A ball that rolls off / drops beside the net leaves the net nearly still.
  python net_swing.py <hoop> <t1> [<t2> ...]      -> prints score per time
  (import) swing(hoop, t) -> dict(score, peak, after)
Score = mean pixel change inside the net rectangle, in the 0.25-0.75 s after the rim moment,
relative to an empty-rim reference, divided by the same measure 1.5-1.0 s before the shot (noise).
"""
import os, sys, subprocess, numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bbconfig


def frames(t0, dur, box):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(0, t0):.3f}", "-i", bbconfig.VIDEO, "-t", f"{dur:.3f}",
                          "-vf", f"crop={w}:{h}:{x0}:{y0},format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    n = len(raw) // (w * h)
    return np.frombuffer(raw[: n * w * h], np.uint8).reshape(n, h, w).astype(np.float32)


def swing(hoop, t):
    h = bbconfig.HOOPS[hoop]
    nx0, nx1, ny1 = h["net"]
    ry = h["rim_y"]
    box = (nx0 - 6, ry + 6, nx1 + 6, ny1 + 4)  # the net body below the rim
    ref = np.median(frames(t - 2.2, 0.6, box), axis=0)
    noise = np.abs(frames(t - 1.6, 0.5, box) - ref).mean()
    seq = frames(t - 0.2, 1.4, box)
    d = np.abs(seq - ref).mean(axis=(1, 2))
    after = d[int(0.45 * 30):int(0.95 * 30)].mean()  # 0.25-0.75 s after the rim moment
    return {"score": round(float(after / max(noise, 1.0)), 2), "after": round(float(after), 2),
            "peak": round(float(d.max()), 2), "noise": round(float(noise), 2)}


if __name__ == "__main__":
    hoop = sys.argv[1]
    for t in sys.argv[2:]:
        print(t, swing(hoop, float(t)))
