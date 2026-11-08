"""Save the round-2 workflow outputs into results/:
  python finish_round2.py <rewrite_run> <drive_run> <translate_run>
rewrite  -> results/report_plain.json (Hebrew report fields), results/drills_plain.json, results/glossary.json
drive    -> results/drives.json, results/drive_patterns.json, results/drive_verdicts.json
translate-> results/verdicts_he.json, results/log_he.json
"""
import json, os, sys
from extract_journal import load

HERE = os.path.dirname(os.path.abspath(__file__))
R = lambda *p: os.path.join(HERE, "results", *p)


def parse(s):
    try:
        t = str(s).strip()
        if t.startswith("```"):
            t = t.split("\n", 1)[1]
        if t.endswith("```"):
            t = t[:-3]
        return json.loads(t)
    except Exception:
        return None


def dump(obj, name):
    json.dump(obj, open(R(name), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("wrote", name, os.path.getsize(R(name)) // 1000, "KB")


BLOCKS = ["summary", "fixes", "strengths", "weaknesses", "tendencies", "shots", "moments-targets"]

# ---- rewrite
rows = load(os.path.join(sys.argv[1], "journal.jsonl"))
by = {}
for r in rows:
    if r["done"] and r["result"] is not None:
        by[r["label"]] = r["result"]          # the last result per label wins
plain, missing = {}, []
for b in BLOCKS + ["drills"]:
    draft = parse(by.get(f"rewrite:{b}"))
    v = by.get(f"verify:{b}")
    fixed = parse(v["corrected_json"]) if isinstance(v, dict) and v.get("corrected_json") else None
    final = fixed or draft
    if not final:
        missing.append(b); continue
    if b == "drills":
        dump(final, "drills_plain.json")
    else:
        plain.update({k: v2 for k, v2 in final.items()})
base = json.load(open(R("report.json"), encoding="utf-8"))
merged = dict(base); merged.update(plain)
dump(merged, "report_plain.json")
print("rewrite: fields", sorted(plain.keys()), "missing blocks:", missing or "none")
g = by.get("glossary")
if isinstance(g, dict) and g.get("terms"):
    dump(g["terms"], "glossary.json")
else:
    print("glossary: missing")

# ---- drives
if len(sys.argv) > 2 and os.path.exists(os.path.join(sys.argv[2], "journal.jsonl")):
    rows = load(os.path.join(sys.argv[2], "journal.jsonl"))
    by = {}
    for r in rows:
        if r["done"] and r["result"] is not None:
            by[r["label"]] = r["result"]
    drives = sorted([v for k, v in by.items() if k.startswith("drive:r")], key=lambda d: d["clip"])
    if drives:
        dump(drives, "drives.json")
    pat = by.get("drive-patterns")
    if pat:
        dump(pat, "drive_patterns.json")
    dv = sorted([dict(v, index=int(k.split(":")[1])) for k, v in by.items() if k.startswith("verify:")], key=lambda v: v["index"])
    if dv:
        dump(dv, "drive_verdicts.json")
    fin = by.get("drive-final")
    if fin:
        dump(fin, "drive_patterns_final.json")
    print("drives:", len(drives), "patterns:", bool(pat), "verdicts:", len(dv), "final:", bool(fin))

# ---- translations
if len(sys.argv) > 3 and os.path.exists(os.path.join(sys.argv[3], "journal.jsonl")):
    rows = load(os.path.join(sys.argv[3], "journal.jsonl"))
    by = {}
    for r in rows:
        if r["done"] and r["result"] is not None:
            by[r["label"]] = parse(r["result"])
    v = by.get("translate:verdicts")
    if v and v.get("verdicts"):
        dump(v["verdicts"], "verdicts_he.json")
    recs = []
    for k, p in by.items():
        if k.startswith("translate:log") and p and p.get("records"):
            recs += p["records"]
    if recs:
        dump(sorted(recs, key=lambda r: r["clip"]), "log_he.json")
    print("translations: verdicts", len(v["verdicts"]) if v and v.get("verdicts") else 0, "records", len(recs))
