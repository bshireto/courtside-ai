"""Pull finished agent results out of a Workflow journal.jsonl.

  python extract_journal.py <journal.jsonl> [--list]
Prints one line per agent (label, phase, done?) and returns a dict label -> result via load().
"""
import json, sys


def load(path):
    started, results, order = {}, {}, []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            e = json.loads(line)
            if e.get("type") == "started":
                started[e["agentId"]] = e
                order.append(e["agentId"])
            elif e.get("type") == "result":
                results[e["agentId"]] = e.get("result")
    out = []
    for aid in order:
        s = started[aid]
        out.append({"label": s.get("label"), "phase": s.get("phase"), "key": s.get("key"), "agentId": aid,
                    "done": aid in results, "result": results.get(aid)})
    return out


if __name__ == "__main__":
    rows = load(sys.argv[1])
    for r in rows:
        n = len(json.dumps(r["result"])) if r["done"] else 0
        print(f'{r["phase"]:10} {r["label"]:36} {"done" if r["done"] else "----":4} {n:7} key={r["key"]}')
