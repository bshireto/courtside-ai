"""Turn per-frame hoop features into shot candidates (high recall, low precision).

For each hoop (game.json), only frames inside its camera setup count.
  normal hoops : net-motion events (net_fg > 0.04) + onset pass that splits long events
  small hoops  : ball-coloured motion above the rim + strong net motion
Writes data/shot_candidates.json
"""
import csv, json, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bbconfig

rows = list(csv.DictReader(open(bbconfig.data("hoop_features.csv"))))
A = {k: np.array([float(r[k]) for r in rows]) for k in rows[0].keys()}
t = A["t"]


def events(sig, mask, thr, gap, src):
    ev = []
    for i in np.where(mask & (sig > thr))[0]:
        if ev and t[i] - ev[-1]["end"] <= gap:
            ev[-1]["end"] = float(t[i])
        else:
            ev.append({"start": float(t[i]), "end": float(t[i]), "peak_t": float(t[i]), "peak": 0.0, "src": [src]})
        if sig[i] > ev[-1]["peak"]:
            ev[-1]["peak"], ev[-1]["peak_t"] = float(sig[i]), float(t[i])
    return ev


def merge(evs, gap):
    out = []
    for e in sorted(evs, key=lambda e: e["start"]):
        if out and e["start"] - out[-1]["end"] <= gap:
            o = out[-1]
            o["end"] = max(o["end"], e["end"]); o["src"] = sorted(set(o["src"] + e["src"]))
            if e["peak"] > o["peak"]:
                o["peak"], o["peak_t"] = e["peak"], e["peak_t"]
        else:
            out.append(dict(e))
    return out


cands = []
for h, cfg in bbconfig.HOOPS.items():
    # every setup that uses this hoop counts (one camera position can be split into several live-game windows)
    mask = np.zeros(len(t), bool)
    for su in bbconfig.SETUPS:
        if h in su["hoops"]:
            mask |= (t >= su["start"] + 0.5) & (t < su["end"])
    if cfg.get("small"):
        ev = merge(events(A[f"{h}_above_ball"], mask, 0.02, 0.7, "above_ball") +
                   events(A[f"{h}_net_fg"], mask, 0.3, 0.5, "net"), 1.5)
    else:
        ev = merge(events(A[f"{h}_net_fg"], mask, 0.04, 1.0, "net"), 1.0)
        # onset pass: a long event can hide several shots
        s = A[f"{h}_net_fg"]
        mn = np.array([s[max(0, i - 8):i].min() if i > 0 else s[0] for i in range(len(s))])
        on = events(s - mn, mask, 0.08, 1.0, "net_onset")
        for o in on:
            if min((abs(o["start"] - e["peak_t"]) for e in ev), default=99) > 1.5:
                o["peak_t"] = o["start"]
                ev.append(o)
    for e in ev:
        cands.append(dict(e, hoop=h))
cands.sort(key=lambda c: c["peak_t"])
for i, c in enumerate(cands):
    c["id"] = f"c{i:03d}"
    for k in ("start", "end", "peak_t", "peak"):
        c[k] = round(c[k], 2)
json.dump(cands, open(bbconfig.data("shot_candidates.json"), "w"), indent=1)
from collections import Counter
print(len(cands), Counter(c["hoop"] for c in cands))
