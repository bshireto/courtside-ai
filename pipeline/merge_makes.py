"""Reconcile the two make-detection routes.

Route 1: hoop-motion candidates -> first pass + blind recheck + tie-break  (verify workflow)
Route 2: agents watching the whole game in 45 s windows                   (sweep workflow)

Writes data/makes_merge.json:
  confirmed   - route-1 final verdict "make"
  disputed    - route-1 reviewers never converged (disputed / unclear)
  conflicts   - route 2 says make (or unclear) where route 1 said miss / no_shot
  sweep_only  - route 2 make / unclear with no route-1 candidate nearby
"""
import json, sys

VERIFY = sys.argv[1]
SWEEP = sys.argv[2]


def load(p):
    d = json.load(open(p, encoding="utf-8"))
    return d.get("result", d)


summary = load(VERIFY)["summary"]
windows = load(SWEEP)["windows"]


def best(x):
    for k in ("third", "second", "first"):
        if x.get(k):
            return x[k]
    return None


confirmed, disputed, judged = [], [], []
for x in summary:
    b = best(x)
    rec = {"id": x["id"], "hoop": x["hoop"], "peak_t": x["peak_t"], "final": x["final"], "verdict": b,
           "votes": [v["verdict"] if v else None for v in (x.get("first"), x.get("second"), x.get("third"))]}
    judged.append(rec)
    if x["final"] == "make":
        mk = [v for v in (x.get("third"), x.get("second"), x.get("first")) if v and v["verdict"] == "make"]
        rec["verdict"] = mk[0]
        confirmed.append(rec)
    elif x["final"] in ("disputed", "unclear"):
        disputed.append(rec)

# dedupe sweep shots across overlapping windows
shots = []
for w in windows:
    for s in w["shots"]:
        t = s["t_rim"] if s.get("t_rim") is not None else s["t_release"] + 1.0
        s = dict(s, t=t, window=w["window"])
        dup = next((o for o in shots if o["hoop"] == s["hoop"] and abs(o["t"] - t) < 1.5), None)
        if dup:
            rank = {"make": 2, "unclear": 1, "miss": 0}
            if rank[s["result"]] > rank[dup["result"]]:
                dup.update(s)
            continue
        shots.append(s)


def near_confirmed(t, hoop):
    for c in confirmed:
        tt = c["verdict"].get("t_through") or c["peak_t"]
        if abs(tt - t) <= 2.5 and (hoop in (c["hoop"], "other")):
            return c
    return None


def near_judged(t, hoop):
    for j in judged:
        if abs(j["peak_t"] - t) <= 2.5 and hoop in (j["hoop"], "other"):
            return j
    return None


conflicts, sweep_only, matched = [], [], 0
for s in shots:
    if s["result"] not in ("make", "unclear"):
        continue
    c = near_confirmed(s["t"], s["hoop"])
    if c:
        matched += 1
        continue
    j = near_judged(s["t"], s["hoop"])
    (conflicts if j else sweep_only).append({"sweep": s, "route1": j})

out = {"confirmed": confirmed, "disputed": disputed, "conflicts": conflicts, "sweep_only": sweep_only,
       "sweep_shots": shots, "windows_covered": sorted(w["window"] for w in windows)}
json.dump(out, open("data/makes_merge.json", "w"), indent=1)
print(f"route1 confirmed {len(confirmed)}, disputed {len(disputed)}; sweep shots {len(shots)} "
      f"(makes {sum(1 for s in shots if s['result'] == 'make')}); matched {matched}; "
      f"conflicts {len(conflicts)}; sweep-only {len(sweep_only)}; sweep windows {len(windows)}")
