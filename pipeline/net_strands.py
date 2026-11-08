"""Strand test: did the NET ITSELF move? (complements net_swing.py; decides "ball behind / in front of a still net")

A ball that drops BEHIND the net shows through the mesh gaps (so a plain difference image "lights up" and reviewers
call it a make) but every strand stays exactly where it was. A ball that goes THROUGH the net drags the strands away.
So: take the pixels that are net strands in an empty-rim reference (bright against the dark background) and, frame by
frame, measure how many of them went dark (= the strand is no longer there).
  moved(f)  = share of reference strand pixels that lost > DROP brightness in frame f
  peak      = max moved over the event            (make: most of the net; behind-the-net: ~0; in front: the ball's disc)
  held      = number of frames with moved > 0.15  (make: the net keeps swinging 10+ frames; in front: 2-4 frames)
  python net_strands.py <hoop> <t1> [<t2> ...]
First calibration (07.10.2026, side view, dark background): makes peak >= 0.45 and held >= 9; "behind a still net"
misses peak <= 0.12 and held 0.
"""
import os, subprocess, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bbconfig

DROP = 45


def frames(t0, dur, box):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(0, t0):.3f}", "-i", bbconfig.VIDEO, "-t", f"{dur:.3f}",
                          "-vf", f"crop={w}:{h}:{x0}:{y0},format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    n = len(raw) // (w * h)
    return np.frombuffer(raw[: n * w * h], np.uint8).reshape(n, h, w).astype(np.float32)


def strands(hoop, t, pre=0.45, post=1.0):
    h = bbconfig.HOOPS[hoop]
    nx0, nx1, ny1 = h["net"]
    ry = h["rim_y"]
    box = (nx0 - 4, ry + 8, nx1 + 4, ny1 + 2)
    # reference: the quietest half second in the 3 s before the shot (a ball bouncing on the rim must not be in it)
    pre_seq = frames(t - 3.2, 2.4, box)
    best, ref = None, None
    for i in range(0, max(1, len(pre_seq) - 15), 5):
        chunk = pre_seq[i:i + 15]
        v = float(chunk.std(axis=0).mean())
        if best is None or v < best:
            best, ref = v, np.median(chunk, axis=0)
    mask = ref > max(95.0, float(np.percentile(ref, 60)))  # strand pixels: bright against the dark background
    seq = frames(t - pre, pre + post, box)
    moved = np.array([float(((ref - f) > DROP)[mask].mean()) for f in seq])
    return {"peak": round(float(moved.max()), 2), "held": int((moved > 0.15).sum()),
            "strand_px": int(mask.sum()), "ref_noise": round(best, 2), "series": [round(float(m), 2) for m in moved]}


if __name__ == "__main__":
    hoop = sys.argv[1]
    for t in sys.argv[2:]:
        r = strands(hoop, float(t))
        print(t, {k: v for k, v in r.items() if k != "series"})
