"""Check sheets for a rendered drive video: one frame per part (late in a stop, so every mark is on; the middle of a motion part),
six parts per sheet at 1280 px each, readable. Also prints the timeline and checks that every pause is seamless.

  python qa_parts.py c15        -> work/drivevid/tmp/qa_c15_0.jpg, qa_c15_1.jpg, ...   (reads clips/drives/drive_c15.mp4 + _timeline.json)
  python qa_parts.py fix1_decide
"""
import json, os, subprocess, sys, tempfile
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
name = sys.argv[1]; base = name if name.startswith(("drive_", "fix")) else f"drive_{name}"
video = os.path.join(HERE, "clips", "drives", base + ".mp4")
T = json.load(open(os.path.join(HERE, "clips", "drives", base + "_timeline.json"), encoding="utf-8"))
outdir = os.path.join(HERE, "work", "drivevid", "tmp"); os.makedirs(outdir, exist_ok=True); tmp = tempfile.mkdtemp(prefix="qa_")
tiles = []
for r in T:
    at = r["start"] + (max(0.1, r["secs"] - 0.6) if r["type"] in ("freeze", "still", "card") else r["secs"] * 0.5)
    fp = os.path.join(tmp, f"{r['n']:02d}.jpg")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{at:.2f}", "-i", video, "-frames:v", "1", "-vf", "scale=1280:720", fp], check=True)
    tiles.append(Image.open(fp).convert("RGB"))
    words = len((r.get("text") or "").split())
    print(f"{r['n']:>2} {r['type']:<6} start {r['start']:>6.2f}  {r['secs']:>5.2f}s  reel {r.get('reel')}  step {r.get('step') or '-':<4} words {words:>2}  {r.get('tag') or ''}")
per = 6
for c in range(0, len(tiles), per):
    chunk = tiles[c:c + per]; rows = (len(chunk) + 1) // 2
    sh = Image.new("RGB", (2560, 720 * rows), (20, 20, 20))
    for k, im in enumerate(chunk):
        sh.paste(im, ((k % 2) * 1280, (k // 2) * 720))
    p = os.path.join(outdir, f"qa_{name}_{c // per}.jpg"); sh.save(p, quality=86); print("sheet", p, f"(parts {c}-{c + len(chunk) - 1})")
total = T[-1]["start"] + T[-1]["secs"]; motion = sum(r["secs"] for r in T if r["type"] in ("live", "slow"))
print(f"total {total:.1f}s | motion {motion:.1f}s | reading {total - motion:.1f}s | parts {len(T)}")
long = [r for r in T if r["type"] == "freeze" and len((r.get("text") or "").split()) > 11]
if long:
    print("TOO LONG (over 11 words):", [(r["n"], len(r["text"].split())) for r in long])
# a stop must sit on the frame the slow motion before it ended on, in the same view, and the next slow motion must start there
spec_path = os.path.join(HERE, "work", "drivevid", f"spec_{'fix1' if name.startswith('fix1') else name}.json")
if os.path.exists(spec_path):
    S = json.load(open(spec_path, encoding="utf-8"))["segments"]
    at = lambda g: g.get("at")
    for a, b in zip(S, S[1:]):
        if a["type"] == "slow" and b["type"] in ("stop", "freeze"):
            if abs(a["end"] - b["at"]) > 0.001:
                print(f"JUMP: slow motion ends at {a['end']} but the stop after it is at {b['at']}")
            elif a.get("view") != b.get("view"):
                print(f"VIEW CHANGE at the stop {b['at']} (fine if meant: the picture cuts to another zoom as it pauses)")
        if a["type"] in ("stop", "freeze") and b["type"] == "slow":
            if abs(a["at"] - b["start"]) > 0.001:
                print(f"JUMP: stop at {a['at']} but the slow motion after it starts at {b['start']}")
        if a["type"] in ("live", "slow") and (a.get("caption") or a.get("captions")):
            print(f"TEXT ON MOTION: the {a['type']} part at {a.get('start')} has a caption; captions belong on stops only")
