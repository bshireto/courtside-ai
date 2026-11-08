"""Render several video specs at once: python render_all.py c2 c9 fix1 ... (three at a time; logs in work/drivevid/tmp/)."""
import os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))


def one(name):
    log = os.path.join(HERE, "work", "drivevid", "tmp", f"render_{name}.log")
    with open(log, "w", encoding="utf-8") as f:
        r = subprocess.run([sys.executable, os.path.join(HERE, "make_drive_video.py"), os.path.join(HERE, "work", "drivevid", f"spec_{name}.json")],
                           stdout=f, stderr=subprocess.STDOUT, cwd=HERE, env=dict(os.environ, PYTHONUTF8="1"))
    return name, r.returncode


with ThreadPoolExecutor(3) as ex:
    for name, rc in ex.map(one, sys.argv[1:]):
        print(name, "ok" if rc == 0 else f"FAILED ({rc})", flush=True)
