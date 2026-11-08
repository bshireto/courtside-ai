"""Turn labelled user touches into reel clip windows -> data/user_clips_final.json

Rules (research_style_guide.md, section 3):
  keep touches whose context is live_offense / starts_offense (and unclear unless low confidence)
  start = first touch - 2.0 s
  end   = shot: release + 2.5 s (result + ~1.5 s); pass: release + 1.5 s, extended to 1.0 s after
          the result of a shot taken within 3 s of the pass; otherwise last touch + 1.5 s
  merge windows < 3 s apart; min 3 s; never cross the camera move (968-981 s)
"""
import json, sys
import sys as _s, os as _o
_s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
import bbconfig

TOUCHES = sys.argv[1]
d = json.load(open(TOUCHES, encoding="utf-8"))
batches = d.get("result", d)["batches"]
shots = json.load(open("data/makes_merge.json"))["sweep_shots"]

DROP = set(json.load(open("data/touch_drops.json"))) if __import__("os").path.exists("data/touch_drops.json") else set()  # manual reviews
touches = []
for b in batches:
    for t in b["touches"]:
        ok = t["context"] in ("live_offense", "starts_offense") or (t["context"] == "unclear" and t["confidence"] != "low")
        if round(t["t_start"], 1) in DROP:  # manual review: defensive contest / reach with no touch
            ok = False
        t["kept"] = ok
        touches.append(t)
touches.sort(key=lambda t: t["t_start"])
json.dump(touches, open("data/user_touches_all.json", "w"), indent=1)

wins = []
for t in touches:
    if not t["kept"]:
        continue
    s, e = t["t_start"] - 2.0, t["t_end"] + 2.5
    # play the possession out: run to 1.5 s after the result of the next shot (his or a teammate's),
    # if one comes within 10 s of his last touch
    nxt = sorted((x for x in shots if -0.5 < x["t_release"] - t["t_end"] <= 10.0), key=lambda x: x["t_release"])
    if nxt:
        e = max(e, nxt[0]["t"] + 1.5)
    e = min(e, max(s + 20.0, nxt[0]["t"] + 1.5 if nxt else 0))  # never cut before the outcome
    wins.append([s, e, t])

clips = []
for s, e, t in wins:
    if clips and s - clips[-1]["end"] < 3.0 and bbconfig.setup_of(clips[-1]["end"] - 0.01) == bbconfig.setup_of(s):
        clips[-1]["end"] = max(clips[-1]["end"], e)
        clips[-1]["touches"].append(t)
    else:
        clips.append({"start": s, "end": e, "touches": [t]})
for c in clips:
    if c["end"] - c["start"] < 3.0:
        c["end"] = c["start"] + 3.0
    su = next(x for x in bbconfig.SETUPS if x["name"] == bbconfig.setup_of(c["start"] + 2.0))
    c["start"], c["end"] = max(c["start"], su["start"]), min(c["end"], su["end"])
    c["start"], c["end"] = round(max(0, c["start"]), 2), round(c["end"], 2)
json.dump(clips, open("data/user_clips_final.json", "w"), indent=1)
kept = sum(t["kept"] for t in touches)
print(f"touches {len(touches)} (kept {kept}), clips {len(clips)}, total {sum(c['end'] - c['start'] for c in clips):.0f}s")
