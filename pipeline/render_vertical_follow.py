"""Vertical (1080x1920) Top N where the 4:5 action window FOLLOWS the ball (see vfollow.py) instead of a fixed crop.

  python render_vertical_follow.py data/top10.json output/Top10_Baskets_Vertical.mp4 [--only <id> | --cards-only]

Every play is cut straight from the source video (not from the landscape intermediates, whose burned-in labels
would slide through a moving window):
  live   : full-height 864x1080 window panning in x, graded like the landscape cut
  replay : 640x800 window panning in x and y at half speed (motion-interpolated on a fixed region first, then cropped)
Title, #N and end cards are built here too (portrait versions of the landscape cards), so this is the ONLY vertical
render to run. It needs:
  - the landscape countdown rendered first (render_v2.py top5: its intermediates give the card stills and audio);
  - data/vpaths/<id>.json with a focus path for every play (vfollow.py init, wf/follow_paths.js, vfollow.py check).
It refuses to start when a play has no focus path, so a fixed-crop vertical can never be produced by accident.
"""
import json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bbconfig
import vfollow
import render_vertical as RV
if os.environ.get('BB_MUSIC'):
    RV.MUSIC = os.environ['BB_MUSIC']  # per-game song (the old default path was the first game's)
from render_v2 import ENC, GRADE, NORM_A, NORM_V, SRC, run

W, H, FW, FH, FY = RV.W, RV.H, RV.FW, RV.FH, RV.FY
OUT = RV.OUT
BG = "boxblur=24:2,eq=brightness=-0.12:saturation=0.8"


def _graph(path, text):
    with open(path, "w") as f:
        f.write(text)
    return path


def live_segment(spec, png, out):
    cam = vfollow.camera(spec, "live")
    seg = spec["live"]
    n = len(cam["cx"])
    d = n / 30.0
    x = vfollow.expr(cam["cx"] - cam["w"] / 2.0)
    v = (f"[0:v]{NORM_V.format(n=n)},{GRADE},split[a][b];"
         f"[a]scale=-2:{H},crop={W}:{H}:(iw-{W})/2:0,{BG}[bg];"
         f"[b]crop=w={cam['w']}:h={cam['h']}:x='{x}':y=0:exact=1,scale={FW}:{FH}:flags=lanczos[fg];"
         f"[bg][fg]overlay=0:{FY},fade=t=in:st=0:d=0.15[c];[c][1:v]overlay=0:0:shortest=1,format=yuv420p[v];"
         f"[0:a]{NORM_A.format(ns=n * 1600)},afade=t=in:d=0.05,afade=t=out:st={d - 0.05:.3f}:d=0.05[a]")
    run(["-ss", f"{seg['start']:.3f}", "-t", f"{d + 0.3:.3f}", "-i", SRC, "-loop", "1", "-framerate", "30", "-i", png,
         "-/filter_complex", _graph(out + ".graph.txt", v), "-map", "[v]", "-map", "[a]", "-t", f"{d:.3f}"] + ENC + [out],
        "vlive " + os.path.basename(out))


def replay_segment(spec, png, out):
    cam = vfollow.camera(spec, "replay")          # one sample per OUTPUT frame (60 per source second, shown at 30 fps)
    seg = spec["replay"]
    n_in = int(round((seg["end"] - seg["start"]) * 30))
    n_out = len(cam["cx"])
    dur = n_out / 30.0
    w, h = cam["w"], cam["h"]
    # fixed region that holds every window position: interpolate motion there once, then move the window inside it
    rx0 = int(max(0, min(cam["cx"]) - w / 2.0 - 8)) // 2 * 2
    ry0 = int(max(0, min(cam["cy"]) - h / 2.0 - 8)) // 2 * 2
    rx1 = int(min(vfollow.SRC_W, max(cam["cx"]) + w / 2.0 + 10) + 1) // 2 * 2
    ry1 = int(min(vfollow.SRC_H, max(cam["cy"]) + h / 2.0 + 10) + 1) // 2 * 2
    x = vfollow.expr(cam["cx"] - w / 2.0 - rx0)
    y = vfollow.expr(cam["cy"] - h / 2.0 - ry0)
    grade = GRADE.replace("0.6:5:5:0", "0.8:5:5:0")
    v = (f"[0:v]{NORM_V.format(n=n_in)},crop={rx1 - rx0}:{ry1 - ry0}:{rx0}:{ry0},hqdn3d=1.5:1.5:6:6,"
         f"minterpolate=fps=60:mi_mode=mci,setpts=2*PTS,fps=30,split[a][b];"
         f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},{BG}[bg];"
         f"[b]crop=w={w}:h={h}:x='{x}':y='{y}':exact=1,scale={FW}:{FH}:flags=lanczos,{grade},vignette=angle=PI/6[fg];"
         f"[bg][fg]overlay=0:{FY},tpad=stop_mode=clone:stop=6,trim=end_frame={n_out},setpts=N/30/TB,"
         f"fade=t=in:st=0:d=0.2:color=white,fade=t=out:st={dur - 0.15:.3f}:d=0.15[c];"
         f"[c][1:v]overlay=0:0:shortest=1,format=yuv420p[v];"
         f"[0:a]{NORM_A.format(ns=n_in * 1600)},atempo=0.5,volume=0.3,afade=t=in:d=0.2,"
         f"afade=t=out:st={dur - 0.4:.3f}:d=0.4,apad,atrim=end_sample={n_out * 1600},asetpts=N/SR/TB[a]")
    run(["-ss", f"{seg['start']:.3f}", "-t", f"{n_in / 30.0 + 0.3:.3f}", "-i", SRC, "-loop", "1", "-framerate", "30", "-i", png,
         "-/filter_complex", _graph(out + ".graph.txt", v), "-map", "[v]", "-map", "[a]", "-t", f"{dur:.3f}"] + ENC + [out],
        "vreplay " + os.path.basename(out))


def finish(parts, out):
    lst = os.path.join(OUT, "follow_list.txt")
    with open(lst, "w") as fh:
        fh.writelines(f"file '{x}'\n" for x in parts)
    joined = os.path.join(OUT, "follow_joined.mov")
    run(["-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined], "concat")
    D = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", joined],
                             capture_output=True, text=True).stdout)
    fc = (f"[0:a]volume=0.45[g];[1:a]atrim=0:{D:.3f},asetpts=N/SR/TB,volume=0.55,afade=t=in:d=1.0,"
          f"afade=t=out:st={D - 2.5:.3f}:d=2.5[m];[g][m]amix=inputs=2:duration=first:normalize=0,"
          f"loudnorm=I=-14:TP=-2:LRA=11,aresample=48000[a]")
    run(["-i", joined, "-i", RV.MUSIC, "-filter_complex", fc, "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-preset", "medium",
         "-crf", "22", "-maxrate", "8M", "-bufsize", "16M", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", out], "final")
    # WhatsApp-size copy (two passes, about 27 MB for 2.5 minutes)
    wa = out.replace(".mp4", "_WhatsApp.mp4")
    vb = max(600, int(27 * 8192 / D) - 110)
    log = os.path.join(OUT, "follow_2pass")
    base = ["-i", out, "-vf", "scale=720:1280", "-c:v", "libx264", "-preset", "slow", "-b:v", f"{vb}k", "-maxrate", f"{int(vb * 1.6)}k",
            "-bufsize", f"{vb * 3}k", "-pix_fmt", "yuv420p", "-passlogfile", log]
    run(base + ["-pass", "1", "-an", "-f", "null", "NUL" if os.name == "nt" else "/dev/null"], "whatsapp pass 1")
    run(base + ["-pass", "2", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", wa], "whatsapp pass 2")
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", out, "-f", "null", "-"], capture_output=True, text=True)
    print("decode check:", "clean" if not r.stderr.strip() else r.stderr[:400])
    print(f"done {D:.1f} s | {os.path.getsize(out) / 1e6:.0f} MB | WhatsApp copy {os.path.getsize(wa) / 1e6:.1f} MB")


def main():
    top = json.load(open(sys.argv[1], encoding="utf-8"))
    out = sys.argv[2]
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    RV.N = len(top)
    os.makedirs(OUT, exist_ok=True)
    # every play needs a focus path: no path = no vertical video (never fall back to a fixed crop)
    bad = []
    for m in top:
        pf = vfollow.path_file(m["id"])
        spec = vfollow.load(m["id"]) if os.path.exists(pf) else {}
        for kind in ("live", "replay"):
            keys = sorted(spec.get(kind + "_focus") or [])
            seg = spec.get(kind) or {}
            if len(keys) < 4 or keys[0][0] > seg.get("start", 0) + 0.5 or keys[-1][0] < seg.get("end", 0) - 0.5:
                bad.append(f"{m['id']} {kind}")
    if bad:
        raise SystemExit("no usable focus path for: " + ", ".join(bad) + ". Run vfollow.py init <top10.json>, "
                         "then the wf/follow_paths.js workflow, then vfollow.py check <id> live|replay")
    SEG = RV.SEG
    still = os.path.join(SEG, "still.png")
    need = [still, os.path.join(SEG, "s000_title.mov")] + [os.path.join(SEG, f"s{1 + 3 * i:03d}_rank.mov") for i in range(len(top))]
    if not all(os.path.exists(x) for x in need):
        raise SystemExit("render the landscape countdown first (render_v2.py top5 ...): the vertical cards reuse its stills and audio")
    white, grey = (255, 255, 255), (225, 225, 225)
    cards_only = "--cards-only" in sys.argv
    parts, jobs, card_jobs = [os.path.join(OUT, "v000_title.mov")], [], []
    if not only:
        tp = os.path.join(OUT, "title.png")
        RV.card_png(tp, still, [(f"TOP {len(top)}", 230, True, white), ("BUCKETS", 120, True, white), (f"Pickup run  |  {RV.DATE}", 44, False, grey)])
        card_jobs.append(lambda tp=tp: RV.card_segment(tp, os.path.join(SEG, "s000_title.mov"), parts[0], 3.0, 0.3))
    for i, m in enumerate(top):
        b = 1 + 3 * i
        spec = vfollow.load(m["id"])
        parts.append(os.path.join(OUT, f"v{b:03d}_rank.mov"))
        if not only:
            rk = os.path.join(OUT, f"rank{i}.png")
            RV.card_png(rk, os.path.join(SEG, f"s{b:03d}_rankstill.png"),
                        [(f"#{m['rank']}", 420, True, white), (m["caption"].upper(), 60, True, white), (m["sub"], 42, False, (220, 220, 220))])
            card_jobs.append(lambda rk=rk, b=b: RV.card_segment(rk, os.path.join(SEG, f"s{b:03d}_rank.mov"),
                                                                os.path.join(OUT, f"v{b:03d}_rank.mov"), 1.6, 0.18, white=True))
        ol, orp = os.path.join(OUT, f"ol{i}_live.png"), os.path.join(OUT, f"ol{i}_replay.png")
        RV.overlay_png(ol, m, False)
        RV.overlay_png(orp, m, True)
        pl, pr = os.path.join(OUT, f"f{b + 1:03d}_live.mov"), os.path.join(OUT, f"f{b + 2:03d}_replay.mov")
        parts += [pl, pr]
        if only in (None, m["id"]):
            jobs.append(lambda spec=spec, ol=ol, pl=pl: live_segment(spec, ol, pl))
            jobs.append(lambda spec=spec, orp=orp, pr=pr: replay_segment(spec, orp, pr))
    endp = os.path.join(OUT, f"v{1 + 3 * len(top):03d}_end.mov")
    parts.append(endp)
    if not only:
        ep = os.path.join(OUT, "end.png")
        RV.card_png(ep, still, [("THAT'S THE RUN", 110, True, white), (f"Pickup run  |  {RV.DATE}", 44, False, grey), (RV.CREDIT, 30, False, (190, 190, 190))])
        card_jobs.append(lambda ep=ep: RV.card_segment(ep, os.path.join(SEG, f"s{1 + 3 * len(top):03d}_end.mov"), endp, 5.0, 1.0))
    with ThreadPoolExecutor(int(os.environ.get("RENDER_WORKERS", "3"))) as ex:
        list(ex.map(lambda j: j(), card_jobs + ([] if cards_only else jobs)))
    if only:
        print("rendered only", only)
        return
    if cards_only:
        print("cards rebuilt:", len(card_jobs))
        return
    missing = [p for p in parts if not os.path.exists(p)]
    if missing:
        raise SystemExit("missing segments: " + ", ".join(os.path.basename(p) for p in missing))
    finish(parts, out)


if __name__ == "__main__":
    main()
