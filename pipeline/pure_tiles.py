"""Pure naming tiles for crowded games / many people: cluster only CLEAN single-person crops, one tile per look.

  python pure_tiles.py [dist=0.22] [min_n=25] [max_tiles=70]   (run from the game folder with BB_GAME set)
  -> data/naming_tiles.json (same format players.py ask writes; naming_page.py and players.py learn read it)

Why: players.py ask groups whole tracker segments, and in a crowded half court the tracker id jumps between people, so
tiles come out mixed (2-3 players). Here only detections that stand alone in the frame (tall box, no other box
overlapping it, good confidence) are used, they are clustered one by one (not per track), and every tile shows 6 samples
spread over different videos / times. One person in two outfits simply becomes two tiles that Barak gives the same name.
"""
import collections, json, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bbconfig

dist = float(sys.argv[1]) if len(sys.argv) > 1 else 0.22
min_n = int(sys.argv[2]) if len(sys.argv) > 2 else 25
max_tiles = int(sys.argv[3]) if len(sys.argv) > 3 else 70

dets = json.load(open(bbconfig.data("people_dets.json")))
E = np.load(bbconfig.data("people_emb.npz"))["emb"].astype(np.float32)
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
            continue  # itself
        ix = max(0, min(x1, a1) - max(x0, a0)) * max(0, min(y1, b1) - max(y0, b0))
        if ix > 0.04 * area:
            return False
    return True


clean = [i for i, d in enumerate(dets) if d["tid"] >= 0 and alone(d)]
print(len(dets), "detections,", len(clean), "clean")
from sklearn.cluster import AgglomerativeClustering
X = E[clean]
X /= np.linalg.norm(X, axis=1, keepdims=True)
lab = AgglomerativeClustering(n_clusters=None, distance_threshold=dist, metric="cosine", linkage="average").fit_predict(X)
groups = collections.defaultdict(list)
for i, l in zip(clean, lab):
    groups[l].append(i)
big = sorted((v for v in groups.values() if len(v) >= min_n), key=lambda v: -len(v))[:max_tiles]
print(len(groups), "clusters,", len(big), "kept (>=", min_n, "crops),", sum(len(v) for v in big), "crops covered")
tiles = []
for n, mem in enumerate(sorted(big, key=lambda v: (-len(v))), 1):
    tiles.append({"n": n, "team": "plain", "members": mem, "secs": len(mem), "samples": 6,
                  "tracks": sorted({f"{dets[i]['setup']}:{dets[i]['tid']}" for i in mem})[:6]})
json.dump(tiles, open(bbconfig.data("naming_tiles.json"), "w"))
print("wrote", len(tiles), "tiles")
