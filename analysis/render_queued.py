"""Render one video spec, at most three renders at a time across all helpers (a render is CPU-heavy, about 1.5-3 minutes).

  python render_queued.py work/drivevid/spec_c15.json        (waits for a free slot, then runs make_drive_video.py)
"""
import os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
LOCKS = os.path.join(HERE, "work", "drivevid", "tmp", "locks"); os.makedirs(LOCKS, exist_ok=True)
got = None
while got is None:
    for k in range(3):
        p = os.path.join(LOCKS, f"slot{k}.lock")
        try:
            if os.path.exists(p) and time.time() - os.path.getmtime(p) > 900:      # a render that died: free its slot
                os.remove(p)
            fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY); os.write(fd, str(os.getpid()).encode()); os.close(fd)
            got = p; break
        except (FileExistsError, PermissionError):
            continue
    if got is None:
        time.sleep(4)
try:
    rc = subprocess.run([sys.executable, os.path.join(HERE, "make_drive_video.py"), sys.argv[1]], cwd=HERE, env=dict(os.environ, PYTHONUTF8="1")).returncode
finally:
    try:
        os.remove(got)
    except OSError:
        pass
sys.exit(rc)
