"""Save the outputs of the two resume workflows from their journals into results/.

  python finish_results.py <clip_run_folder> <research_run_folder>

clip run    -> results/lenses.json, results/report.json, results/verdicts.json
research run-> results/research_verdicts.json (28 saved + the new ones), results/research_critique.json,
               results/research.md (only if the synthesizer did not write it itself)
"""
import json, os, sys
from extract_journal import load

HERE = os.path.dirname(os.path.abspath(__file__))
R = lambda *p: os.path.join(HERE, "results", *p)


def dump(obj, name):
    json.dump(obj, open(R(name), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("wrote", name, os.path.getsize(R(name)) // 1000, "KB")


clip_dir, res_dir = sys.argv[1], sys.argv[2]

# ---- clip analysis
rows = load(os.path.join(clip_dir, "journal.jsonl"))
lenses = [r["result"] for r in rows if r["phase"] == "Lenses" and r["done"] and r["result"]]
report = next((r["result"] for r in rows if r["label"] == "aggregate-report" and r["done"] and r["result"]), None)
verdicts = [r["result"] for r in rows if r["phase"] == "Verify" and r["done"] and r["result"]]
# a claim re-run after a failed attempt can appear twice in the journal: keep the last verdict per claim
by_claim = {}
for v in verdicts:
    by_claim[v["claim"].strip()[:160]] = v
verdicts = list(by_claim.values())
print(f"clip run: lenses {len(lenses)}/3, report {'yes' if report else 'NO'}, verdicts {len(verdicts)}")
if lenses:
    dump(lenses, "lenses.json")
if report:
    dump(report, "report.json")
    print("  headline:", report.get("headline", "")[:160])
    print("  fixes:", [f["what"][:70] for f in report.get("priority_fixes", [])])
    print("  teaching moments:", len(report.get("teaching_moments", [])), "shots:", len(report.get("shot_by_shot", [])))
if verdicts:
    dump(verdicts, "verdicts.json")
    tally = {}
    for v in verdicts:
        tally[v["verdict"]] = tally.get(v["verdict"], 0) + 1
    print("  verdict tally:", tally)

# ---- research
rows = load(os.path.join(res_dir, "journal.jsonl"))
new = [dict(r["result"], index=int(r["label"].split(":")[1])) for r in rows if r["phase"] == "Verify" and r["done"] and r["result"]]
old = json.load(open(R("partial", "research_verdicts.json"), encoding="utf-8"))
allv = sorted(old + new, key=lambda v: v["index"])
print(f"research run: new verdicts {len(new)}, total {len(allv)}")
dump(allv, "research_verdicts.json")
tally = {}
for v in allv:
    tally[v["verdict"]] = tally.get(v["verdict"], 0) + 1
print("  research verdict tally:", tally)
crit = next((r["result"] for r in rows if r["label"] == "critic+gapfill" and r["done"] and r["result"]), None)
if crit:
    dump(crit, "research_critique.json")
    print("  critique findings:", len(crit.get("findings", [])), "gaps:", len(crit.get("gaps", [])))
synth = next((r["result"] for r in rows if r["label"] == "synthesize-report" and r["done"] and r["result"]), None)
md_path = R("research.md")
if os.path.exists(md_path):
    print("  research.md written by the agent:", os.path.getsize(md_path) // 1000, "KB")
elif synth:
    open(md_path, "w", encoding="utf-8").write(synth if isinstance(synth, str) else json.dumps(synth, ensure_ascii=False, indent=1))
    print("  research.md saved from the journal:", os.path.getsize(md_path) // 1000, "KB")
else:
    print("  research.md: not available yet")
