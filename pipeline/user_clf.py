"""Train the "is this the user?" classifier and build the per-frame user timeline.

  python user_clf.py train     -> cross-validated report + data/user_prob.npy
  python user_clf.py timeline  -> data/user_timeline_v2.json (5 fps, with track propagation)

Labels: data/user_labels.json  [{"det": i, "y": 1|0}, ...]
"""
import json, sys, collections
import sys as _s, os as _o
_s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
import bbconfig
import numpy as np


def feats():
    emb = np.load("data/orange_emb.npz")["emb"].astype(np.float32)
    dets = json.load(open("data/orange_dets.json"))
    col = np.array([d["col"] for d in dets], np.float32)
    h = np.array([[(d["box"][3] - d["box"][1]) / 400.0] for d in dets], np.float32)
    return np.hstack([emb, col * 2.0, h]), dets


def train():
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import make_pipeline
    from sklearn.model_selection import StratifiedKFold, cross_val_predict
    X, dets = feats()
    lab = json.load(open("data/user_labels.json"))
    idx = np.array([l["det"] for l in lab])
    y = np.array([l["y"] for l in lab])
    clf = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=5000, class_weight="balanced"))
    p = cross_val_predict(clf, X[idx], y, cv=StratifiedKFold(5, shuffle=True, random_state=0), method="predict_proba")[:, 1]
    for thr in (0.3, 0.5, 0.7):
        pred = p >= thr
        tp = int((pred & (y == 1)).sum()); fp = int((pred & (y == 0)).sum()); fn = int((~pred & (y == 1)).sum())
        print(f"thr {thr}: precision {tp / max(1, tp + fp):.3f} recall {tp / max(1, tp + fn):.3f} (tp {tp} fp {fp} fn {fn}; n={len(y)}, pos={int(y.sum())})")
    wrong = [(int(i), int(t), round(float(q), 2)) for i, t, q in zip(idx, y, p) if (q >= 0.5) != (t == 1)]
    json.dump(wrong, open("data/user_clf_cv_errors.json", "w"))
    # add this game's labels to the player's stored training set, so later games need no labelling
    store = _o.path.join(bbconfig.PIPELINE, "players", "barak_train.npz")
    _o.makedirs(_o.path.dirname(store), exist_ok=True)
    Xs, ys = X[idx], y
    if _o.path.exists(store):
        old = np.load(store)
        Xs, ys = np.vstack([old["X"], Xs]), np.concatenate([old["y"], ys])
    np.savez_compressed(store, X=Xs.astype(np.float32), y=ys)
    clf.fit(Xs, ys)
    prob = clf.predict_proba(X)[:, 1]
    np.save("data/user_prob.npy", prob.astype(np.float32))
    print("stored training set", len(ys), "| saved probs for", len(prob), "detections; >0.5:", int((prob > 0.5).sum()))


def apply():
    """Score this game's detections with the stored training set (no new labels needed)."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import make_pipeline
    X, dets = feats()
    st = np.load(_o.path.join(bbconfig.PIPELINE, "players", "barak_train.npz"))
    clf = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=5000, class_weight="balanced"))
    clf.fit(st["X"], st["y"])
    prob = clf.predict_proba(X)[:, 1]
    np.save("data/user_prob.npy", prob.astype(np.float32))
    print("applied stored model:", len(st["y"]), "training crops;", int((prob > 0.5).sum()), "of", len(prob), "detections > 0.5")


def timeline():
    dets = json.load(open("data/orange_dets.json"))
    prob = np.load("data/user_prob.npy")
    # per (segment, tid): mean prob over embedded frames
    tp = collections.defaultdict(list)
    for d, p in zip(dets, prob):
        if d["tid"] >= 0:
            tp[(d["tid"], bbconfig.setup_of(d["t"]))].append(float(p))
    tmean = {k: (float(np.mean(v)), len(v)) for k, v in tp.items()}
    embedded = {(d["k"], tuple(d["box"])): float(p) for d, p in zip(dets, prob)}
    rows = [json.loads(l) for l in open("data/tracks.jsonl")]
    frames = []
    for r in rows:
        best = None
        for pp in r["p"]:
            tid, box = pp[0], tuple(pp[2:6])
            own = embedded.get((r["k"], box))
            tm, n = tmean.get((tid, bbconfig.setup_of(r["t"])), (0.0, 0))
            if own is not None and n >= 2:
                s = 0.5 * own + 0.5 * tm
            elif own is not None:
                s = own
            elif n >= 2:
                s = tm * 0.95
            else:
                continue
            if best is None or s > best[0]:
                best = (s, list(box), tid, own, tm, n)
        if best and best[0] >= 0.5:
            s, box, tid, own, tm, n = best
            frames.append({"t": r["t"], "box": box, "p": round(s, 3), "tid": tid,
                           "own": None if own is None else round(own, 3), "track_mean": round(tm, 3), "track_n": n})
    gaps, prev = [], None
    for f in frames:
        if prev is not None and f["t"] - prev > 1.0:
            gaps.append([prev, f["t"]])
        prev = f["t"]
    json.dump({"frames": frames, "gaps": gaps}, open("data/user_timeline_v2.json", "w"))
    print(f"frames {len(rows)}, user found in {len(frames)} ({len(frames) / len(rows):.0%}); gaps>1s {len(gaps)} totalling {sum(b - a for a, b in gaps):.0f}s")


if __name__ == "__main__":
    {"train": train, "apply": apply, "timeline": timeline}[sys.argv[1]]()
