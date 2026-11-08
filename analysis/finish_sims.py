"""Collect the simulation composites built by workflows/sim_composites.js into work/weavy/sims.json (read by the review builder).

  python finish_sims.py <run_folder> [--include id1,id2] [--exclude id3]
A simulation is kept when its builder returned "done" and the reviewer said "ok", or said "fix" and a repair ran.
--include / --exclude override that after looking at the panels by eye.
"""
import json, os, sys
from extract_journal import load

HERE = os.path.dirname(os.path.abspath(__file__))
run = sys.argv[1]
inc = set(); exc = set()
for i, a in enumerate(sys.argv):
    if a == "--include":
        inc = set(sys.argv[i + 1].split(","))
    if a == "--exclude":
        exc = set(sys.argv[i + 1].split(","))
by = {}
for r in load(os.path.join(run, "journal.jsonl")):
    if r["done"] and r["result"] is not None:
        by[r["label"]] = r["result"]
reviews = {x["id"]: x for x in (by.get("review-all") or {}).get("reviews", [])}
sims_path = os.path.join(HERE, "work", "weavy", "sims.json")
sims = json.load(open(sims_path, encoding="utf-8")) if os.path.exists(sims_path) else {}
report = []
for label, res in by.items():
    if not label.startswith("build:"):
        continue
    sid = label.split(":", 1)[1]
    rep = by.get(f"repair:{sid}")
    final = rep or res
    v = reviews.get(sid, {}).get("verdict", "not_reviewed")
    keep = final.get("status") == "done" and (v == "ok" or (v == "fix" and rep is not None))
    if sid in inc:
        keep = final.get("status") == "done"
    if sid in exc:
        keep = False
    key = sid.split("_")[0] if sid.startswith("fix") else str(int(sid.split("_c")[1]))
    panel = final.get("panel_jpg", "")
    exists = bool(panel) and os.path.exists(os.path.join(HERE, panel))
    report.append((sid, final.get("status"), v, "repaired" if rep else "", "KEPT" if keep and exists else "left out", final.get("reason", "")[:120]))
    if keep and exists:
        extra = sims.get(key, {}).get("cap_extra")
        sims[key] = {"img": panel, "title": final["title_he"], "cap": final["caption_he"]}
        if extra:
            sims[key]["cap_extra"] = extra
    elif key in sims and key != "23":
        sims.pop(key)
json.dump(sims, open(sims_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for r in sorted(report):
    print(" | ".join(str(x) for x in r))
for sid, rv in reviews.items():
    if rv.get("problems"):
        print(f"  review {sid} [{rv['verdict']}]:", "; ".join(rv["problems"])[:400])
print("sims.json keys:", sorted(sims.keys()))
