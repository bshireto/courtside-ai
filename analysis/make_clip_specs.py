"""Build coaching-clip specs (for make_coaching_clip.py) from the verified report's teaching moments.

  python make_clip_specs.py            -> writes clips/spec_<nn>_c<clip>.json for the chosen moments and prints them
  python make_clip_specs.py --render   -> also renders each spec with make_coaching_clip.py

Selection: one moment per priority fix (corrective, from that fix's evidence clips) plus the best positive moments,
5 clips in total, ordered by reel time. Captions are copied verbatim from results/report.json (the verified report):
live caption = the teaching-moment caption, replay caption = the same, freeze caption = the fix's cue (corrective) or
"What to keep" (positive). Crop centre and ring come from the pipeline's tracked box of Barak at that source time.
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.join(HERE, "..", "recap_2026-10-07")
REEL = os.path.join(GAME, "output", "Barak_Offense_Reel_master.mp4")
report = json.load(open(os.path.join(HERE, "results", "report_plain.json" if os.path.exists(os.path.join(HERE, "results", "report_plain.json")) else "report.json"), encoding="utf-8"))
clips = json.load(open(os.path.join(HERE, "clip_map.json"), encoding="utf-8"))
tl = json.load(open(os.path.join(GAME, "data", "user_timeline_v2.json"), encoding="utf-8"))["frames"]
tl.sort(key=lambda f: f["t"])
PY = sys.executable


def clip_of_reel(rt):
    for c in clips:
        if c["reel_start"] - 0.05 <= rt <= c["reel_end"] + 0.05:
            return c
    return None


def box_at(src_t, max_dt=0.9):
    best, bd = None, 1e9
    for f in tl:
        d = abs(f["t"] - src_t)
        if d < bd:
            bd, best = d, f
        if f["t"] > src_t + max_dt:
            break
    return best["box"] if best and bd <= max_dt else None


def choose(moments, fixes, n_total=5):
    chosen = []
    used_clips = set()
    # one corrective moment per fix, from that fix's evidence clips, nearest to the fix's first evidence clip
    for f in sorted(fixes, key=lambda f: f["rank"]):
        cands = [m for m in moments if m["kind"] == "corrective" and m["clip"] in f["evidence_clips"] and m["clip"] not in used_clips]
        if cands:
            m = cands[0]
            chosen.append(dict(m, fix=f["rank"], cue=f["cue"]))
            used_clips.add(m["clip"])
    # fill with positives (keep roughly 1 positive per 2 corrective), then any remaining corrective
    pos = [m for m in moments if m["kind"] == "positive" and m["clip"] not in used_clips]
    for m in pos:
        if len(chosen) >= n_total:
            break
        chosen.append(dict(m, fix=None, cue=None)); used_clips.add(m["clip"])
    for m in moments:
        if len(chosen) >= n_total:
            break
        if m["clip"] not in used_clips:
            chosen.append(dict(m, fix=None, cue=None)); used_clips.add(m["clip"])
    return sorted(chosen, key=lambda m: m["reel_time"])


def _sim_still(fix):
    """A fix clip ends on its Weavy simulation still (work/weavy/sim_fix<N>_still.jpg) when one exists."""
    if not fix:
        return {}
    still = os.path.join(HERE, "work", "weavy", f"sim_fix{fix}_still.jpg")
    if not os.path.exists(still):
        return {}
    try:
        title = json.load(open(os.path.join(HERE, "work", "weavy", "sims.json"), encoding="utf-8"))[f"fix{fix}"]["title"]
    except Exception:
        title = "סימולציה"
    return {"stills": [{"image": still.replace("\\", "/"), "secs": 4.5, "tag": title}]}


def spec_for(m, idx):
    c = clip_of_reel(m["reel_time"]) or clips[m["clip"]]
    t = m["reel_time"]
    start = max(c["reel_start"], t - 7.0)
    end = min(c["reel_end"], t + 3.0)
    if end - start < 5.0:
        start, end = c["reel_start"], c["reel_end"]
    src_t = c["src_start"] + (t - c["reel_start"])
    b = box_at(src_t)
    if b:
        cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2 - 20
        ring = [int((b[0] + b[2]) / 2), int(b[1] + (b[3] - b[1]) * 0.22)]   # around the head / shooting pocket
    else:
        cx, cy, ring = 900, 560, [900, 450]
    cx = max(480, min(1440, cx)); cy = max(270, min(810, cy))
    label = f"קליפ {m['clip']} · " + ("מה לשנות" if m["kind"] == "corrective" else "מה לשמור")
    if m.get("fix"):
        label = f"קליפ {m['clip']} · תיקון {m['fix']}"
    freeze_caption = f"משפט לעצמך: {m['cue']}" if m.get("cue") else m["caption"]
    return {
        "reel": REEL.replace("\\", "/"),
        "out": os.path.join(HERE, "clips", f"coach_{idx:02d}_c{m['clip']:02d}.mp4").replace("\\", "/"),
        "live": {"start": round(start, 2), "end": round(end, 2),
                 "captions": [{"from": 0.0, "to": round(end - start, 2), "text": f"{label}: {m['caption']}"}]},
        "replay": {"t": round(t, 2), "pre": 1.5, "post": 1.0, "speed": 0.5, "center": [int(cx), int(cy)], "crop_w": 960,
                   "caption": m["caption"],
                   "freeze": {"at": round(t, 2), "secs": 1.8, "ring": ring, "caption": freeze_caption}},
        "_moment": m,
        **_sim_still(m.get("fix")),
    }


if __name__ == "__main__":
    chosen = choose(report["teaching_moments"], report["priority_fixes"])
    os.makedirs(os.path.join(HERE, "clips"), exist_ok=True)
    specs = []
    for i, m in enumerate(chosen, 1):
        s = spec_for(m, i)
        p = os.path.join(HERE, "clips", f"spec_{i:02d}_c{m['clip']:02d}.json")
        json.dump(s, open(p, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        specs.append(p)
        print(f"{i}. clip {m['clip']:2} t={m['reel_time']:6.1f} {m['kind']:10} fix={m.get('fix')} live {s['live']['start']}-{s['live']['end']} :: {m['caption']}")
    if "--render" in sys.argv:
        for p in specs:
            print("rendering", os.path.basename(p), flush=True)
            r = subprocess.run([PY, os.path.join(HERE, "make_coaching_clip.py"), p], capture_output=True, text=True)
            print(r.stdout.strip() or r.stderr[-800:])
