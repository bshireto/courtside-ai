"""Game-specific "is this the user?" model: DINOv2 embedding + clothing colours (body_colors.py), boosted trees.

Use when the user's look this game is not the stored one (different shirt, no pinnie). Labels come from
data/user_labels.json ([{"det", "y"}], e.g. the bb-label-user-crops workflow). Writes data/user_prob.npy, which
user_clf.py timeline reads unchanged.
  python user_clf2.py            -> 5-fold report (grouped by 20 s, so near-duplicate frames never straddle a fold) + probs
"""
import json, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bbconfig
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

emb = np.load(bbconfig.data("orange_emb.npz"))["emb"].astype(np.float32)
col = np.load(bbconfig.data("orange_col.npz"))["col"]
dets = json.load(open(bbconfig.data("orange_dets.json")))
lab = json.load(open(bbconfig.data("user_labels.json")))
idx = np.array([l["det"] for l in lab]); y = np.array([l["y"] for l in lab])
grp = np.array([int(dets[i]["t"] // 20) for i in idx])


def models():
    return (HistGradientBoostingClassifier(max_iter=300, learning_rate=0.06, max_leaf_nodes=15, l2_regularization=1.0,
                                           class_weight="balanced", random_state=0),
            make_pipeline(StandardScaler(), LogisticRegression(C=0.3, max_iter=5000, class_weight="balanced")))


def fit_predict(tr, te):
    gb, lr = models()
    gb.fit(col[tr[0]], tr[1])
    lr.fit(np.hstack([emb[tr[0]], col[tr[0]]]), tr[1])
    return 0.6 * gb.predict_proba(col[te])[:, 1] + 0.4 * lr.predict_proba(np.hstack([emb[te], col[te]]))[:, 1]


p = np.zeros(len(y))
for a, b in GroupKFold(5).split(idx, y, grp):
    p[b] = fit_predict((idx[a], y[a]), idx[b])
for thr in (0.3, 0.5, 0.7):
    pred = p >= thr
    tp = int((pred & (y == 1)).sum()); fp = int((pred & (y == 0)).sum()); fn = int((~pred & (y == 1)).sum())
    print(f"thr {thr}: precision {tp / max(1, tp + fp):.3f} recall {tp / max(1, tp + fn):.3f} (tp {tp} fp {fp} fn {fn}; n={len(y)}, pos={int(y.sum())})")
json.dump([(int(i), int(t), round(float(q), 2)) for i, t, q in zip(idx, y, p) if (q >= 0.5) != (t == 1)],
          open(bbconfig.data("user_clf_cv_errors.json"), "w"))
prob = fit_predict((idx, y), np.arange(len(dets)))
# the user is only on court in some setups (game.json user.setups); elsewhere nobody is him
on = set(bbconfig.CFG["user"].get("setups") or [s["name"] for s in bbconfig.SETUPS])
for i, d in enumerate(dets):
    if bbconfig.setup_of(d["t"]) not in on:
        prob[i] = 0.0
np.save(bbconfig.data("user_prob.npy"), prob.astype(np.float32))
print("saved probs for", len(prob), "detections; >0.5:", int((prob > 0.5).sum()))
