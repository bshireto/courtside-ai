"""After the drive videos are rendered (work/drivevid/spec_*.json -> clips/drives/*.mp4): make the phone-size copies the review plays,
and one video with every drive in a row.

  python finish_drives.py [--only c15,c2]
Writes ../review_2026-10-07/clips/drive_c<N>.mp4, fix1_decide.mp4 (720p, crf 25) and all_drives.mp4, and prints what is missing.
"""
import glob, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FULL = os.path.join(HERE, "clips", "drives")
OUT = os.path.join(HERE, "..", "review_2026-10-07", "clips")      # the clean folder Barak opens
os.makedirs(OUT, exist_ok=True)
only = None
force = "--force" in sys.argv          # re-encode every phone copy
if "--only" in sys.argv:
    only = set(sys.argv[sys.argv.index("--only") + 1].split(","))


def run(args):
    r = subprocess.run(["ffmpeg", "-v", "error", "-y"] + args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        raise SystemExit(r.stderr[-2000:])


def dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


def phone(src, dst):
    run(["-i", src, "-vf", "scale=1280:720:flags=lanczos,setsar=1", "-c:v", "libx264", "-preset", "medium", "-crf", "25", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "96k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", dst])


cards = sorted((json.load(open(p, encoding="utf-8")) for p in glob.glob(os.path.join(HERE, "work", "drivevid", "card_c*.json"))), key=lambda c: c["clip"])
made = []
for c in cards:
    src = os.path.join(FULL, f"drive_c{c['clip']}.mp4"); dst = os.path.join(OUT, f"drive_c{c['clip']}.mp4")
    if not os.path.exists(src):
        print("MISSING video for clip", c["clip"]); continue
    if (only is None or f"c{c['clip']}" in only) and (force or not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src)):
        phone(src, dst)
    made.append(dst)
f1 = os.path.join(FULL, "fix1_decide.mp4")
if os.path.exists(f1):
    d1 = os.path.join(OUT, "fix1_decide.mp4")
    if force or not os.path.exists(d1) or os.path.getmtime(d1) < os.path.getmtime(f1):
        phone(f1, d1)
else:
    print("MISSING fix1_decide.mp4")
if made:
    args = []
    for p in made:
        args += ["-i", p]
    n = len(made)
    fc = "".join(f"[{i}:v]setsar=1[v{i}];" for i in range(n)) + "".join(f"[v{i}][{i}:a]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v][a]"
    run(args + ["-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "25", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", os.path.join(OUT, "all_drives.mp4")])
total = sum(dur(p) for p in made)
print(f"phone copies: {len(made)} drives, {total:.0f} s in all; all_drives.mp4 {dur(os.path.join(OUT, 'all_drives.mp4')) if made else 0:.0f} s")
for c in cards:
    print(f"  c{c['clip']:<3} {c['time']:>5}  {dur(os.path.join(OUT, 'drive_c%d.mp4' % c['clip'])) if os.path.exists(os.path.join(OUT, 'drive_c%d.mp4' % c['clip'])) else 0:5.1f}s  hand: {c.get('hand', {}).get('what_barak_did', '?'):<16} {c['title_he']}")
