"""Write one small brief per clip (briefs/rNNN.json) for the clip-analysis agents."""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.join(HERE, "..", "recap_2026-10-07")
SHEETS = os.path.join(HERE, "sheets")
OUT = os.path.join(HERE, "briefs")
os.makedirs(OUT, exist_ok=True)

clips = json.load(open(os.path.join(HERE, "clip_map.json"), encoding="utf-8"))
index = {e["clip"]: e for e in json.load(open(os.path.join(HERE, "sheets_index.json"), encoding="utf-8"))}
att = {a["id"]: a for a in json.load(open(os.path.join(GAME, "data", "attempts.json"), encoding="utf-8"))}
makes = {m["id"]: m for m in json.load(open(os.path.join(GAME, "data", "makes_final.json"), encoding="utf-8"))}


def game_of(t):
    if 130 <= t < 780: return "G1"
    if 1059 <= t < 1553: return "G2"
    if 1660 <= t < 2170: return "G3"
    return "G4"


TEAMS = {
    "G1": {"barak_team": "no pinnies. Barak's team: Barak, a teammate, a teammate, a teammate. Opponents: the defender, the defender, the defender, the defender."},
    "G2": {"barak_team": "ORANGE pinnies. Barak's team: Barak, a teammate, a teammate, a teammate (a teammate sits out). Opponents in LIME: the defender, the defender, the defender, the defender."},
    "G3": {"barak_team": "ORANGE pinnies. Barak's team: Barak, a teammate, a teammate, a teammate (a teammate sits out). Opponents in LIME: the defender, the defender, the defender, the defender."},
}

for c in clips:
    i = c["i"]
    e = index[i]
    shots = []
    for s in c["shots"]:
        a = att.get(s["id"], {})
        m = makes.get(s["id"], {})
        shots.append({
            "id": s["id"], "release_src": s["t"], "release_reel": round(c["reel_start"] + s["t"] - c["src_start"], 2),
            "made": s.get("made"), "points": s.get("points"), "feet_xy_px": a.get("xy"),
            "pipeline_type": a.get("type", ""), "pipeline_contest": m.get("contest"), "pipeline_play": m.get("play"),
        })
    g = game_of(c["src_start"] + 1)
    brief = {
        "clip": i, "reel_start": c["reel_start"], "reel_end": c["reel_end"], "src_start": c["src_start"], "src_end": c["src_end"],
        "game": g, "teams": TEAMS.get(g, {}).get("barak_team", ""),
        "events": c["events"],
        "pipeline_touch_notes": [{"t_start": t["t_start"], "t_end": t["t_end"], "actions": t["actions"], "shot_result": t.get("shot_result"),
                                  "confidence": t.get("confidence"), "note": t.get("note")} for t in c["touches"]],
        "shots": shots,
        "sheets": {
            "flow": [dict(x, path=os.path.join(SHEETS, x["path"])) for x in e["flow"]],
            "zoom": [dict(x, path=os.path.join(SHEETS, x["path"])) for x in e["zoom"]],
            "shot_strips": [dict(x, path=os.path.join(SHEETS, x["path"])) for x in e["shots"]],
            "release_frames": [dict(x, path=os.path.join(SHEETS, x["path"])) for x in e["release_frames"]],
        },
    }
    json.dump(brief, open(os.path.join(OUT, f"r{i:03d}.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("briefs:", len(clips))
