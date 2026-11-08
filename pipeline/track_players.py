"""YOLO11s person (+ball) detection and ByteTrack over the 5 fps frame dump.

Writes data/tracks.jsonl - one line per frame:
  {"k": frame_index_5fps, "t": seconds, "p": [[tid, conf, x0, y0, x1, y1, feats...], ...], "b": [[conf, x0, y0, x1, y1], ...]}
feats = [orange, lime, navy, skin_head, dark_head, red_shoe] (fractions of the
relevant body region), used later to pick out the player in the orange pinnie
over a navy shirt with a bald head.
The tracker is reset at the camera move (16:09-16:20).
"""
import os, sys, json, cv2, numpy as np
from ultralytics import YOLO

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bbconfig

F5 = bbconfig.F5
OUT = bbconfig.data("tracks.jsonl")
MODEL = sys.argv[1] if len(sys.argv) > 1 else os.path.join(bbconfig.PIPELINE, "models", "yolo11s_openvino_model")

model = YOLO(MODEL, task="detect")
files = sorted(f for f in os.listdir(F5) if f.endswith(".jpg"))


def frac(mask):
    return round(float(np.count_nonzero(mask)) / max(1, mask.size), 3)


def feats(hsv, x0, y0, x1, y1):
    H, W = hsv.shape[:2]
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
    bw, bh = x1 - x0, y1 - y0
    if bw < 6 or bh < 12:
        return [0, 0, 0, 0, 0, 0]
    def reg(fx0, fy0, fx1, fy1):
        return hsv[y0 + int(bh * fy0):y0 + max(int(bh * fy0) + 1, int(bh * fy1)),
                   x0 + int(bw * fx0):x0 + max(int(bw * fx0) + 1, int(bw * fx1))]
    torso = reg(0.25, 0.18, 0.75, 0.50)
    h, s, v = torso[..., 0], torso[..., 1], torso[..., 2]
    orange = ((h <= 14) | (h >= 172)) & (s >= 110) & (v >= 110)
    lime = (h >= 24) & (h <= 45) & (s >= 90) & (v >= 100)
    arms = np.concatenate([reg(0.0, 0.18, 0.28, 0.40).reshape(-1, 3), reg(0.72, 0.18, 1.0, 0.40).reshape(-1, 3)])
    ah, as_, av = arms[:, 0], arms[:, 1], arms[:, 2]
    navy = (ah >= 100) & (ah <= 150) & (as_ >= 40) & (av >= 25) & (av <= 140)
    head = reg(0.3, 0.0, 0.7, 0.07)
    hh, hs, hv = head[..., 0], head[..., 1], head[..., 2]
    skin = ((hh <= 25) | (hh >= 170)) & (hs >= 35) & (hs <= 170) & (hv >= 90)
    dark = hv < 60
    shoe = reg(0.0, 0.93, 1.0, 1.0)
    sh, ss, sv = shoe[..., 0], shoe[..., 1], shoe[..., 2]
    red = ((sh <= 10) | (sh >= 170)) & (ss >= 100) & (sv >= 50)
    return [frac(orange), frac(lime), frac(navy), frac(skin), frac(dark), frac(red)]


out = open(OUT, "w")
cur_setup = None
for i, f in enumerate(files):
    k = int(f[:-4])
    t = (k - 1) / 5.0
    su = bbconfig.setup_of(t)
    if su is None:  # camera moving / outside any setup
        continue
    if su != cur_setup:
        if cur_setup is not None:
            model = YOLO(MODEL, task="detect")  # fresh tracker state after a camera move
        cur_setup = su
    img = cv2.imread(os.path.join(F5, f))
    r = model.track(img, imgsz=1280, conf=0.2, classes=[0, 32], persist=True,
                    tracker="bytetrack.yaml", verbose=False)[0]
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    P, B = [], []
    ids = r.boxes.id.int().tolist() if r.boxes.id is not None else [-1] * len(r.boxes)
    for tid, c, cl, xy in zip(ids, r.boxes.conf.tolist(), r.boxes.cls.int().tolist(), r.boxes.xyxy.tolist()):
        x0, y0, x1, y1 = [int(round(v)) for v in xy]
        if cl == 0:
            P.append([tid, round(c, 2), x0, y0, x1, y1] + feats(hsv, x0, y0, x1, y1))
        else:
            B.append([round(c, 2), x0, y0, x1, y1])
    out.write(json.dumps({"k": k, "t": round(t, 2), "p": P, "b": B}) + "\n")
    if i % 500 == 0:
        out.flush()
        print(i, len(files), flush=True)
out.close()
print("done")
