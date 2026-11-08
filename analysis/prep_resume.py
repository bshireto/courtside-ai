"""Rebuild results/ from the previous session's workflow journals and prepare the inputs for the resume workflows."""
import json, os
from extract_journal import load

JW = "~/.claude/projects/<project-session>/772b263d-140c-4157-b533-c940cf07a4a9/subagents/workflows"
os.makedirs("results/partial/sweep", exist_ok=True)

# ---- clip records
rows = load(f"{JW}/wf_044a5784-b60/journal.jsonl")
recs = [r["result"] for r in rows if r["phase"] == "Clips" and r["done"] and r["result"]]
recs.sort(key=lambda r: r["clip"])
assert [r["clip"] for r in recs] == list(range(27)), [r["clip"] for r in recs]
json.dump(recs, open("results/records.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
# three chunks for the lens agents to Read
for n, lo in enumerate([0, 9, 18], 1):
    part = [r for r in recs if lo <= r["clip"] < lo + 9]
    json.dump(part, open(f"results/records_part{n}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"records_part{n}.json clips {part[0]['clip']}-{part[-1]['clip']} {os.path.getsize(f'results/records_part{n}.json')//1000} KB, "
          f"{sum(1 for _ in open(f'results/records_part{n}.json', encoding='utf-8'))} lines")
print("records.json:", len(recs))

# ---- research sweep + verdicts
rows = load(f"{JW}/wf_92749155-b2f/journal.jsonl")
ANGLES = ["film-frameworks", "feedback-science", "drills-mapping", "output-formats", "cv-feasibility", "benchmarks-shot-quality", "form-rebuild-transfer"]
by_label = {r["label"]: r for r in rows}
sweep = []
for k in ANGLES:
    r = by_label[f"research:{k}"]
    assert r["done"], k
    sweep.append(r["result"])
    p = f"results/partial/sweep/{ANGLES.index(k)+1}_{k}.json"
    json.dump(r["result"], open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(p, os.path.getsize(p)//1000, "KB", sum(1 for _ in open(p, encoding="utf-8")), "lines",
          "findings", len(r["result"]["findings"]), "load-bearing", sum(1 for f in r["result"]["findings"] if f["load_bearing"]),
          "drills", len(r["result"].get("drills") or []), "formats", len(r["result"].get("output_format_ideas") or []))
json.dump(sweep, open("results/research_sweep.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
lb = [dict(f, angle=s["angle"]) for s in sweep for f in s["findings"] if f["load_bearing"]]
print("load-bearing claims:", len(lb))
verdicts, missing = [], []
for i, f in enumerate(lb):
    r = by_label.get(f"verify:{i}")
    if r and r["done"] and r["result"]:
        verdicts.append(dict(r["result"], index=i))
    else:
        missing.append(dict(index=i, claim=f["claim"], detail=f["detail"], source_url=f.get("source_url", ""),
                            source_title=f.get("source_title", ""), angle=f["angle"]))
json.dump(verdicts, open("results/partial/research_verdicts.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(missing, open("results/partial/research_verify_todo.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("verdicts saved:", len(verdicts), "missing:", [m["index"] for m in missing])
for m in missing:
    print(f"  [{m['index']}] {m['angle'][:40]} :: {m['claim'][:110]}")
import collections
print("verdict tally:", collections.Counter(v["verdict"] for v in verdicts))
