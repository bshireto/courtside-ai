"""Agent counts and wall-clock minutes of the clip-analysis pipeline, from the workflow run folders -> results/run_stats.json.

Timing comes from file times in each run folder: an agent's .meta.json is written when it starts, its .jsonl is last
written when it ends. The full pipeline was split over two runs (clips in the first session, lenses/report/verify here).
"""
import json, os, sys
from extract_journal import load

OLD = "~/.claude/projects/<project-session>/772b263d-140c-4157-b533-c940cf07a4a9/subagents/workflows/wf_044a5784-b60"
NEW = sys.argv[1] if len(sys.argv) > 1 else None


def span(folder, labels):
    """(start, end, count) over the agents whose label is in labels."""
    rows = {r["agentId"]: r for r in load(os.path.join(folder, "journal.jsonl"))}
    starts, ends, n = [], [], 0
    for f in os.listdir(folder):
        if f.endswith(".meta.json"):
            aid = f[len("agent-"):-len(".meta.json")]
            r = rows.get(aid)
            if not r or not labels(r["label"]):
                continue
            n += 1
            starts.append(os.path.getmtime(os.path.join(folder, f)))
            ends.append(os.path.getmtime(os.path.join(folder, f"agent-{aid}.jsonl")))
    return (min(starts), max(ends), n) if starts else (None, None, 0)


s0, e0, n_clips = span(OLD, lambda l: l.startswith("clip:"))
clips_min = (e0 - s0) / 60
# shots-only estimate: the 13 clips with a shot, same per-agent duration, same concurrency
shot_clips = {0, 3, 5, 8, 9, 13, 14, 16, 18, 19, 23, 26}
out = {"clips": {"agents": n_clips, "minutes": round(clips_min)}}
if NEW:
    s1, e1, n_l = span(NEW, lambda l: l.startswith("lens:"))
    s2, e2, n_r = span(NEW, lambda l: l == "aggregate-report")
    # verify: the claims were re-run across several resumes (session limits), so count one agent per claim (the last
    # successful one) and estimate wall-clock as the sum of their durations at the observed concurrency of 6
    rows = load(os.path.join(NEW, "journal.jsonl"))
    last_ok = {}
    for r in rows:
        if r["label"].startswith("verify:") and r["done"] and r["result"]:
            last_ok[r["label"]] = r["agentId"]
    durs = []
    for aid in last_ok.values():
        m, j = os.path.join(NEW, f"agent-{aid}.meta.json"), os.path.join(NEW, f"agent-{aid}.jsonl")
        if os.path.exists(m) and os.path.exists(j):
            durs.append(max(0, os.path.getmtime(j) - os.path.getmtime(m)))
    n_v = len(last_ok)
    ver_min = sum(durs) / 60 / 6
    lens_min, rep_min = (e1 - s1) / 60, (e2 - s2) / 60
    out.update({
        "lenses": {"agents": n_l, "minutes": round(lens_min)}, "report": {"agents": n_r, "minutes": round(rep_min)},
        "verify": {"agents": n_v, "minutes": round(ver_min)},
        "full_verify": {"agents": n_clips + n_l + n_r + n_v, "minutes": round(clips_min + lens_min + rep_min + ver_min)},
        "full_no_verify": {"agents": n_clips + n_l + n_r, "minutes": round(clips_min + lens_min + rep_min)},
        "shots_only": {"agents": len(shot_clips) + n_r, "minutes": round(clips_min * len(shot_clips) / max(1, n_clips) + rep_min)},
    })
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "run_stats.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
