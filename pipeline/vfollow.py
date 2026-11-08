"""Follow-the-action framing for the vertical videos: the crop window pans with the ball instead of sitting still.

A vertical 4:5 window is only 45% of the source width, so a fixed crop loses the passer, the shooter or the rim.
Here every clip gets a FOCUS PATH (where the viewer should look - normally the ball; the ball handler's chest when
the ball is hidden) as keyframes [t, x, y] in source seconds / pixels, stored in data/vpaths/<id>.json:
  {"id", "T", "t_release", "t_pass", "rim": [x, y], "shooter_xy", "play",
   "live": {"start", "end"}, "replay": {"start", "end"},
   "live_focus": [[t, x, y], ...], "replay_focus": [[t, x, y], ...]}
The virtual camera is derived from the path: lead room toward the basket, zero-phase smoothing (so it anticipates a
pass instead of chasing it), and a hard rule that the focus stays inside the central part of the window.

  python vfollow.py init data/top10.json            -> skeleton files (existing focus paths are kept)
  python vfollow.py frames <id> live|replay         -> WORK/vpath/<id>_<kind>_NN.jpg  annotation sheets (grid = source px)
  python vfollow.py check  <id> live|replay         -> WORK/vpath/<id>_<kind>_check.jpg = what the vertical video shows,
                                                       plus a table of margins (focus distance from the window edges)
Windows: live 864x1080 (full height, pans in x); replay 640x800 (pans in x and y, shown at half speed).
"""
import glob, json, os, subprocess, sys, tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bbconfig

SRC_W, SRC_H = 1920, 1080
WIN = {"live": (864, 1080), "replay": (640, 800)}
FPS = {"live": 30, "replay": 60}          # camera samples per SOURCE second (the replay is shown at half speed)
SIGMA = {"live": 0.34, "replay": 0.17}    # smoothing, source seconds
LEAD_K, LEAD_MAX = 0.25, 0.10             # lead room toward the basket: share of the distance, capped at a share of the width
SAFE = {"live": 0.25, "replay": 0.25}     # the focus stays within +-SAFE * window size of the window centre
#   (0.30 / 0.16 left a three-point shooter 12-16% from the edge at the release: his body was nearly cut)
Y_OFF = 0.14                              # replay: keep the ball this share of the height above the centre (body below it)
LIVE_LEAD, LIVE_TAIL, REPLAY_POST = 5.0, 1.5, 0.5
VP = bbconfig.data("vpaths")
OUT = os.path.join(bbconfig.WORK, "vpath")


def path_file(cid):
    return os.path.join(VP, f"{cid}.json")


def load(cid):
    return json.load(open(path_file(cid), encoding="utf-8"))


def init(top_path):
    os.makedirs(VP, exist_ok=True)
    for m in json.load(open(top_path, encoding="utf-8")):
        T = m["t_through"]
        su = next(s for s in bbconfig.SETUPS if s["start"] <= T < s["end"] + 1)
        lead = min(6.0, max(LIVE_LEAD, m.get("lead", LIVE_LEAD)))
        spec = {"id": m["id"], "rank": m.get("rank"), "T": T, "t_release": m["t_release"], "t_pass": m.get("t_pass"),
                "rim": list(bbconfig.RIM[m["hoop"]]), "shooter_xy": m.get("shooter_xy"), "play": m.get("play"),
                "name": m.get("name"), "assist": m.get("assist"),
                "live": {"start": round(max(su["start"] + 0.5, T - lead), 2), "end": round(T + LIVE_TAIL, 2)},
                "replay": {"start": round(T - m.get("replay_pre", 2.0), 2), "end": round(T + REPLAY_POST, 2)},
                "live_focus": [], "replay_focus": []}
        if os.path.exists(path_file(m["id"])):
            old = load(m["id"])
            spec["live_focus"], spec["replay_focus"] = old.get("live_focus", []), old.get("replay_focus", [])
        json.dump(spec, open(path_file(m["id"]), "w", encoding="utf-8"), indent=1)
        print(m["id"], "live", spec["live"], "replay", spec["replay"], "keys", len(spec["live_focus"]), len(spec["replay_focus"]))


def _smooth(a, sigma_frames):
    if sigma_frames < 0.5:
        return a
    r = int(3 * sigma_frames) + 1
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma_frames) ** 2)
    k /= k.sum()
    return np.convolve(np.pad(a, r, mode="edge"), k, mode="valid")


def camera(spec, kind):
    """-> dict(t = source time per sample, fx, fy = focus, cx, cy = window centre, w, h, fps)."""
    keys = sorted(spec[kind + "_focus"])
    if len(keys) < 2:
        raise SystemExit(f"{spec['id']} {kind}: no focus path yet")
    seg = spec[kind]
    fps = FPS[kind]
    w, h = WIN[kind]
    n = int(round((seg["end"] - seg["start"]) * fps))
    t = seg["start"] + np.arange(n) / float(fps)
    kt = np.array([k[0] for k in keys], float)
    fx = np.interp(t, kt, [k[1] for k in keys])
    fy = np.interp(t, kt, [k[2] for k in keys])
    rx, ry = spec["rim"]
    sig = SIGMA[kind] * fps

    def solve(f, target, half, size, lim):
        lo, hi = half, lim - half
        c = _smooth(np.clip(target, lo, hi), sig)
        for _ in range(4):                       # focus inside the safe zone, then re-smooth the corrections
            c = np.clip(c, f - SAFE[kind] * size, f + SAFE[kind] * size)
            c = _smooth(np.clip(c, lo, hi), sig * 0.45)
        c = np.clip(c, f - (SAFE[kind] + 0.06) * size, f + (SAFE[kind] + 0.06) * size)
        return _smooth(np.clip(c, lo, hi), 1.5)

    cx = solve(fx, fx + np.clip((rx - fx) * LEAD_K, -LEAD_MAX * w, LEAD_MAX * w), w / 2.0, w, SRC_W)
    if kind == "live":
        cy = np.full(n, SRC_H / 2.0)
    else:
        cy = solve(np.clip(fy, 0, SRC_H), np.clip(fy, 0, SRC_H) + Y_OFF * h, h / 2.0, h, SRC_H)
    return dict(t=t, fx=fx, fy=fy, cx=cx, cy=cy, w=w, h=h, fps=fps)


def expr(values, out_fps=30, step=3):
    """ffmpeg expression in t (output seconds) for a per-output-frame array: piecewise linear, a knot every `step` frames."""
    idx = list(range(0, len(values), step))
    if idx[-1] != len(values) - 1:
        idx.append(len(values) - 1)
    terms = []
    for a, b in zip(idx[:-1], idx[1:]):
        ta, tb = a / float(out_fps), b / float(out_fps)
        va, vb = float(values[a]), float(values[b])
        terms.append(f"gte(t,{ta:.4f})*lt(t,{tb:.4f})*({va:.1f}+{(vb - va) / (tb - ta):.3f}*(t-{ta:.4f}))")
    terms.append(f"gte(t,{idx[-1] / float(out_fps):.4f})*{float(values[-1]):.1f}")
    return "+".join(terms)


# ----------------------------------------------------------------------------------------------- sheets
def _font(sz):
    try:
        return ImageFont.truetype("arialbd.ttf", sz)
    except OSError:
        return ImageFont.load_default()


def _fmt(t):
    return f"{int(t // 60)}:{t % 60:05.2f}"


def _frames(times, hires):
    """{t: PIL image} - 5 fps dump when the times sit on it, otherwise decoded from the source video."""
    out = {}
    if not hires:
        for t in times:
            p = os.path.join(bbconfig.F5, "%05d.jpg" % (int(round(t * 5)) + 1))
            if os.path.exists(p):
                out[t] = Image.open(p).convert("RGB")
        return out
    tmp = tempfile.mkdtemp()
    step = times[1] - times[0]
    subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{times[0]:.3f}", "-i", bbconfig.VIDEO, "-t", f"{times[-1] - times[0] + step:.3f}",
                    "-vf", f"fps={1 / step:.4f}", "-q:v", "2", os.path.join(tmp, "%04d.jpg")], check=True)
    for t, f in zip(times, sorted(glob.glob(os.path.join(tmp, "*.jpg")))):
        out[t] = Image.open(f).convert("RGB")
    return out


def _times(spec, kind):
    seg = spec[kind]
    step = 0.2 if kind == "live" else 0.1
    n = int(round((seg["end"] - seg["start"]) / step)) + 1
    if kind == "live":   # snap to the 5 fps dump
        return sorted({round(round((seg["start"] + i * step) * 5) / 5.0, 2) for i in range(n)})
    return [round(seg["start"] + i * step, 2) for i in range(n)]


def frames(cid, kind):
    """Annotation sheets: the whole frame with a pixel grid, six tiles per sheet."""
    spec = load(cid)
    os.makedirs(OUT, exist_ok=True)
    times = _times(spec, kind)
    imgs = _frames(times, kind == "replay")
    f1, f2 = _font(20), _font(15)
    TW, TH = 1280, 720
    paths = []
    for s in range(0, len(times), 6):
        chunk = times[s:s + 6]
        sheet = Image.new("RGB", (TW * 2, TH * ((len(chunk) + 1) // 2)), "black")
        for j, t in enumerate(chunk):
            if t not in imgs:
                continue
            im = imgs[t].resize((TW, TH), Image.LANCZOS)
            d = ImageDraw.Draw(im, "RGBA")
            sc = TW / float(SRC_W)
            for x in range(100, SRC_W, 100):
                d.line([x * sc, 0, x * sc, TH], fill=(0, 255, 255, 70 if x % 500 else 150), width=1)
                d.text((x * sc + 2, TH - 18), str(x), fill=(255, 255, 0, 255), font=f2)
            for y in range(100, SRC_H, 100):
                d.line([0, y * sc, TW, y * sc], fill=(0, 255, 255, 70 if y % 500 else 150), width=1)
                d.text((2, y * sc + 1), str(y), fill=(255, 255, 0, 255), font=f2)
            d.rectangle([0, 0, 250, 26], fill=(0, 0, 0, 255))
            d.text((4, 2), f"{_fmt(t)}  t={t:.2f}", fill="yellow", font=f1)
            sheet.paste(im, ((j % 2) * TW, (j // 2) * TH))
        p = os.path.join(OUT, f"{cid}_{kind}_{s // 6:02d}.jpg")
        sheet.save(p, quality=86)
        paths.append(p)
    print(f"{cid} {kind}: {len(times)} frames from {times[0]} to {times[-1]} s")
    for p in paths:
        print(" ", p)


def check(cid, kind):
    """What the vertical video shows (one tile per sample) + margins of the focus inside the window."""
    spec = load(cid)
    os.makedirs(OUT, exist_ok=True)
    cam = camera(spec, kind)
    times = _times(spec, kind)
    imgs = _frames(times, kind == "replay")
    w, h = cam["w"], cam["h"]
    tw_ = 240
    th_ = int(round(tw_ * h / float(w)))
    cols = 8
    sheet = Image.new("RGB", (cols * tw_, th_ * ((len(times) + cols - 1) // cols)), "black")
    f1 = _font(16)
    keys = sorted(spec[kind + "_focus"])
    kt = [k[0] for k in keys]
    worst = 1.0
    rows = []
    for j, t in enumerate(times):
        i = int(np.argmin(np.abs(cam["t"] - t)))
        cx, cy, fx, fy = cam["cx"][i], cam["cy"][i], cam["fx"][i], cam["fy"][i]
        x0, y0 = int(round(cx - w / 2.0)), int(round(cy - h / 2.0))
        mx = min(fx - x0, x0 + w - fx) / float(w)
        my = min(fy - y0, y0 + h - fy) / float(h) if kind == "replay" else 0.5
        inside = 0 <= fy <= SRC_H
        m = min(mx, my) if inside else mx
        worst = min(worst, m)
        rows.append((t, fx, fy, cx, cy, mx, my, m))
        if t not in imgs:
            continue
        im = imgs[t].crop((x0, y0, x0 + w, y0 + h)).resize((tw_, th_), Image.LANCZOS)
        d = ImageDraw.Draw(im, "RGBA")
        sc = tw_ / float(w)
        px, py = (fx - x0) * sc, (fy - y0) * sc
        d.ellipse([px - 9, py - 9, px + 9, py + 9], outline=(0, 255, 255, 255), width=2)
        d.rectangle([0, 0, 96, 20], fill=(0, 0, 0, 255))
        d.text((3, 1), f"{t:.2f}", fill="yellow" if m >= 0.12 else "red", font=f1)
        if any(abs(t - k) < 0.051 for k in kt):
            d.rectangle([tw_ - 14, 0, tw_, 14], fill=(0, 255, 255, 255))      # a keyframe sits here
        sheet.paste(im, ((j % cols) * tw_, (j // cols) * th_))
    p = os.path.join(OUT, f"{cid}_{kind}_check.jpg")
    sheet.save(p, quality=88)
    span = cam["cx"].max() - cam["cx"].min()
    speed = np.abs(np.diff(cam["cx"])).max() * cam["fps"]
    print(f"{cid} {kind}: window {w}x{h}; camera x {cam['cx'].min():.0f}..{cam['cx'].max():.0f} (pans {span:.0f} px, top speed {speed:.0f} px/s)")
    print("   t      focus(x,y)    camera(x,y)   margin")
    for t, fx, fy, cx, cy, mx, my, m in rows:
        flag = "  <-- focus near the edge" if m < 0.12 else ""
        print(f"  {t:8.2f}  {fx:5.0f},{fy:5.0f}   {cx:5.0f},{cy:5.0f}   {m * 100:4.0f}%{flag}")
    print(f"worst margin {worst * 100:.0f}% of the window  ->  {p}")
    return worst


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "init":
        init(sys.argv[2])
    elif cmd == "frames":
        frames(sys.argv[2], sys.argv[3])
    elif cmd == "check":
        check(sys.argv[2], sys.argv[3])
    else:
        raise SystemExit(__doc__)
