"""Naming tiles by LOOK, not by shirt: group clean single-person crops by the things that survive a shirt change
(shoes, shorts, legs/socks/knee brace, head: bald or hair, skin tone) and print them on every tile, so Barak sees why
crops were matched. The shirts seen are listed separately (they change between games).

  python look_tiles.py [n_clusters=70] [min_n=25]     (run with BB_GAME set; needs data/people_dets.json + tracks.jsonl)
  -> data/naming_tiles.json  (tiles carry "desc": {"shoes":..,"shorts":..,"legs":..,"head":..,"shirts":..} + "samples": 6)
naming_page.py prints desc under the photos; players.py learn trains from the tiles' members.
"""
import collections, json, os, sys
import numpy as np, cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bbconfig

NCL = int(sys.argv[1]) if len(sys.argv) > 1 else 70
MIN_N = int(sys.argv[2]) if len(sys.argv) > 2 else 25
dets = json.load(open(bbconfig.data("people_dets.json")))
rows = {}
for line in open(bbconfig.data("tracks.jsonl")):
    r = json.loads(line)
    rows[r["k"]] = r["p"]


def alone(d):
    x0, y0, x1, y1 = d["box"]
    if y1 - y0 < 85 or (x1 - x0) < 25:
        return False
    area = (x1 - x0) * (y1 - y0)
    for p in rows.get(d["k"], []):
        a0, b0, a1, b1 = p[2:6]
        if abs(a0 - x0) < 4 and abs(b0 - y0) < 4 and abs(a1 - x1) < 4:
            continue
        if max(0, min(x1, a1) - max(x0, a0)) * max(0, min(y1, b1) - max(y0, b0)) > 0.04 * area:
            return False
    return True


BANDS = {"head": (.30, .00, .70, .12), "torso": (.28, .17, .72, .45), "shorts": (.22, .52, .78, .66),
         "legs": (.15, .72, .85, .90), "shoes": (.05, .93, .95, 1.0)}


def cname(h, s, v):
    if v < 70:
        return "black"
    if s < 45:
        return "white" if v > 185 else ("light grey" if v > 130 else "dark grey")
    if v < 110 and s < 110:
        return "dark " + hue(h)
    return hue(h)


def hue(h):
    h = h * 2
    for hi, n in ((12, "red"), (28, "orange"), (45, "tan/yellow"), (70, "lime"), (165, "green"), (200, "teal"), (255, "blue"), (290, "purple"), (335, "pink")):
        if h < hi:
            return n
    return "red"


def band(img, box, b):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    c = img[int(y0 + h * b[1]):max(int(y0 + h * b[1]) + 2, int(y0 + h * b[3])), int(x0 + w * b[0]):max(int(x0 + w * b[0]) + 2, int(x0 + w * b[2]))]
    return c


clean = [i for i, d in enumerate(dets) if d["tid"] >= 0 and alone(d)]
print(len(clean), "clean crops")
feat, names = [], []
byk = collections.defaultdict(list)
for i in clean:
    byk[dets[i]["k"]].append(i)
pos = {}
for k, ids in byk.items():
    img = cv2.imread(os.path.join(bbconfig.F5, f"{k:05d}.jpg"))
    if img is None:
        continue
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    for i in ids:
        f, nm = [], {}
        ok = True
        for bn, b in BANDS.items():
            ch, cl = band(hsv, dets[i]["box"], b), band(lab, dets[i]["box"], b)
            if ch.size == 0:
                ok = False
                break
            m = np.median(ch.reshape(-1, 3), axis=0)
            nm[bn] = cname(*m)
            f += list(np.median(cl.reshape(-1, 3), axis=0))
            if bn == "head":
                skin = (((ch[..., 0] <= 25) | (ch[..., 0] >= 170)) & (ch[..., 1] >= 35) & (ch[..., 1] <= 170) & (ch[..., 2] >= 90)).mean()
                dark = (ch[..., 2] < 70).mean()
                f += [skin * 100, dark * 100]
                nm["head"] = ("bald/short hair" if skin > 0.45 else ("dark hair" if dark > 0.35 else "light/grey hair")) + f" (skin {int(skin * 100)}%)"
        if ok:
            pos[i] = len(feat)
            feat.append(f)
            names.append(nm)
ids = sorted(pos, key=lambda i: pos[i])
X = np.array(feat, np.float32)
X = (X - X.mean(0)) / (X.std(0) + 1e-6)
# extra identity cues beyond clothing colour: build (box shape) and the DINOv2 look (hair, face, body) reduced by PCA
from sklearn.decomposition import PCA
E = np.load(bbconfig.data("people_emb.npz"))["emb"].astype(np.float32)
Z = E[ids]; Z = Z / np.linalg.norm(Z, axis=1, keepdims=True)
Z = PCA(n_components=16, random_state=0).fit_transform(Z); Z = Z / (Z.std(0) + 1e-6)
shape = np.array([[(dets[i]["box"][2] - dets[i]["box"][0]) / max(1, dets[i]["box"][3] - dets[i]["box"][1])] for i in ids], np.float32)
shape = (shape - shape.mean()) / (shape.std() + 1e-6)
W_COL, W_EMB, W_SHAPE = 1.0, float(os.environ.get("W_EMB", "1.2")), 1.5
X = np.hstack([X * W_COL, Z * W_EMB, shape * W_SHAPE])
from sklearn.cluster import AgglomerativeClustering
SEG = json.load(open(bbconfig.data("live_segments.json")))
VID = {f"S{x['seg']:02d}": x["file"][-8:-4] for x in SEG}
PER = int(os.environ.get("PER_VIDEO", "10"))  # clusters per video
groups = {}
vids = sorted({VID[dets[i]["setup"]] for i in ids})
for v in vids:
    sub = [j for j, i in enumerate(ids) if VID[dets[i]["setup"]] == v]
    if len(sub) < 40:
        continue
    lab = AgglomerativeClustering(n_clusters=min(PER, max(2, len(sub) // 40)), linkage="ward").fit_predict(X[sub])
    for j, l in zip(sub, lab):
        groups.setdefault((v, l), []).append(ids[j])
big = sorted((v for v in groups.values() if len(v) >= MIN_N), key=lambda v: -len(v))
tiles = []
for n, mem in enumerate(big, 1):
    def top(key, k=2):
        c = collections.Counter(names[pos[i]][key] for i in mem)
        return " / ".join(f"{a}" for a, _ in c.most_common(k))
    heads = collections.Counter(names[pos[i]]["head"].split(" (")[0] for i in mem).most_common(1)[0][0]
    tiles.append({"n": n, "team": "plain", "members": mem, "secs": len(mem), "samples": 6,
                  "tracks": sorted({f"{dets[i]['setup']}:{dets[i]['tid']}" for i in mem})[:6],
                  "desc": {"shoes": top("shoes"), "shorts": top("shorts"), "legs": top("legs"), "head": heads,
                           "shirts": top("torso", 3)}})
json.dump(tiles, open(bbconfig.data("naming_tiles.json"), "w"))
print(len(groups), "clusters,", len(tiles), "tiles kept,", sum(len(t["members"]) for t in tiles), "crops")
