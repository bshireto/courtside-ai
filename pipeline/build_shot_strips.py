"""Pre-render review images for every shot candidate into WORK/shots:
  cNNN_hoop.jpg - rim close-up at 15 fps, peak-1.3s .. peak+1.1s
  cNNN_ctx.jpg  - wider play context at 2.5 fps, peak-4s .. peak+4s
"""
import json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bbconfig

OUTDIR = os.path.join(bbconfig.WORK, "shots")
os.makedirs(OUTDIR, exist_ok=True)
cands = json.load(open(bbconfig.data("shot_candidates.json")))
here = os.path.dirname(os.path.abspath(__file__))
env = dict(os.environ, BB_GAME=bbconfig.GAME_DIR)


def crop(v):
    return ",".join(str(x) for x in v) if v else None


def run(c):
    p = c["peak_t"]
    hc = bbconfig.HOOPS[c["hoop"]]
    h = os.path.join(OUTDIR, f"{c['id']}_hoop.jpg")
    x = os.path.join(OUTDIR, f"{c['id']}_ctx.jpg")
    if not os.path.exists(h):
        subprocess.run([sys.executable, os.path.join(here, "sheet.py"), "--start", f"{max(0, p - 1.3):.2f}", "--end", f"{p + 1.1:.2f}",
                        "--fps", "15", "--hires", "--crop", crop(hc["strip_crop"]), "--cols", "9", "--tile-w", "220", "--out", h],
                       check=True, capture_output=True, env=env)
    if not os.path.exists(x):
        args = [sys.executable, os.path.join(here, "sheet.py"), "--start", f"{max(0, p - 4):.2f}", "--end", f"{p + 4:.2f}",
                "--fps", "2.5", "--cols", "5", "--tile-w", "480", "--out", x]
        if hc.get("ctx_crop"):
            args += ["--crop", crop(hc["ctx_crop"])]
        subprocess.run(args, check=True, capture_output=True, env=env)
    return c["id"]


with ThreadPoolExecutor(3) as ex:
    for i, cid in enumerate(ex.map(run, cands)):
        if i % 20 == 0:
            print(i, cid, flush=True)
print("done", len(cands))
