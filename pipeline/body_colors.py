"""Clothing-colour descriptor for every detection in data/orange_dets.json -> data/orange_col.npz

DINOv2 alone confuses players of the same build (two bald men, one in maroon and one in black). This adds what a
person actually looks at: the colour of the head, sleeves, torso, shorts, legs and shoes.
Per body band: an HSV histogram (8 hues x 2 saturation levels for coloured pixels + dark / mid / bright for grey ones).
  python body_colors.py
"""
import json, os, sys
import numpy as np, cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bbconfig

# (name, x0, y0, x1, y1) as fractions of the person box
BANDS = [("head", .30, .00, .70, .13), ("torso_up", .28, .17, .72, .33), ("torso_lo", .28, .33, .72, .48),
         ("sleeve_l", .00, .17, .26, .38), ("sleeve_r", .74, .17, 1.0, .38), ("shorts", .22, .50, .78, .66),
         ("legs", .15, .70, .85, .90), ("shoes", .05, .92, .95, 1.0)]
NB = 19


def hist(hsv):
    h, s, v = hsv[..., 0].ravel().astype(int), hsv[..., 1].ravel().astype(int), hsv[..., 2].ravel().astype(int)
    out = np.zeros(NB, np.float32)
    if h.size == 0:
        return out
    col = (s >= 70) & (v >= 45)
    hb = (h[col] * 8 // 180).clip(0, 7)
    sb = (s[col] >= 150).astype(int)
    np.add.at(out, hb * 2 + sb, 1)
    g = v[~col]
    out[16] = (g < 60).sum(); out[17] = ((g >= 60) & (g < 150)).sum(); out[18] = (g >= 150).sum()
    return out / h.size


def main():
    dets = json.load(open(bbconfig.data("orange_dets.json")))
    by_k = {}
    for i, d in enumerate(dets):
        by_k.setdefault(d["k"], []).append(i)
    F = np.zeros((len(dets), NB * len(BANDS) + 4), np.float32)
    for n, (k, ids) in enumerate(sorted(by_k.items())):
        img = cv2.imread(os.path.join(bbconfig.F5, f"{k:05d}.jpg"))
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        H, W = hsv.shape[:2]
        for i in ids:
            x0, y0, x1, y1 = dets[i]["box"]
            bw, bh = x1 - x0, y1 - y0
            f = []
            for _, fx0, fy0, fx1, fy1 in BANDS:
                a, b = max(0, int(x0 + bw * fx0)), max(0, int(y0 + bh * fy0))
                c, e = min(W, int(x0 + bw * fx1) + 1), min(H, int(y0 + bh * fy1) + 1)
                f.append(hist(hsv[b:e, a:c]))
            F[i] = np.concatenate(f + [np.array([bh / 400.0, bw / max(1, bh), (x0 + x1) / 2 / W, y1 / H], np.float32)])
        if n % 1000 == 0:
            print(n, len(by_k), flush=True)
    np.savez_compressed(bbconfig.data("orange_col.npz"), col=F)
    print("done", F.shape)


if __name__ == "__main__":
    main()
