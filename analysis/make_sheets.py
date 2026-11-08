"""Build review sheets for Barak's offense reel (recap_2026-10-07).

Inputs : clip_map.json (reel<->source mapping + touches + shots), the reel master mp4,
         ../recap_2026-10-07/data/user_timeline_v2.json (Barak's tracked box, source time),
         ../recap_2026-10-07/data/attempts.json (feet xy at release for his shots).
Step 1 : decode the whole reel at 10 fps -> work/frames/%05d.jpg  (frame k = reel time (k-1)/10)
Step 2 : per clip -> sheets/rNNN_flow_k.jpg  (wide court crop, 2 fps, 2x4 tiles)
                     sheets/rNNN_zoom_k.jpg  (640x560 window following his box, 5 fps, 4x3 tiles)
                     sheets/rNNN_shot_<id>_k.jpg (10 fps, release-1.4s .. release+1.0s, same window)
         sheets_index.json lists everything with time ranges.
"""
import json, os, subprocess, glob, sys, math
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.join(HERE, "..", "recap_2026-10-07")
REEL = os.path.join(GAME, "output", "Barak_Offense_Reel_master.mp4")
FR = os.path.join(HERE, "work", "frames")
OUT = os.path.join(HERE, "sheets")
FPS = 10
os.makedirs(FR, exist_ok=True)
os.makedirs(OUT, exist_ok=True)

clips = json.load(open(os.path.join(HERE, "clip_map.json"), encoding="utf-8"))
tl = json.load(open(os.path.join(GAME, "data", "user_timeline_v2.json"), encoding="utf-8"))["frames"]
tl.sort(key=lambda f: f["t"])
att = {a["id"]: a for a in json.load(open(os.path.join(GAME, "data", "attempts.json"), encoding="utf-8"))}
font = ImageFont.truetype("arialbd.ttf", 22)
font_s = ImageFont.truetype("arialbd.ttf", 18)


def fmt(t):
    m = int(t // 60)
    return f"{m}:{t - 60 * m:04.1f}"


def decode():
    if len(glob.glob(os.path.join(FR, "*.jpg"))) > 3000:
        print("frames already decoded"); return
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", REEL, "-vf", f"fps={FPS}", "-q:v", "3",
                    os.path.join(FR, "%05d.jpg")], check=True)
    print("decoded", len(glob.glob(os.path.join(FR, "*.jpg"))), "frames")


def frame_at(reel_t):
    k = int(round(reel_t * FPS)) + 1
    p = os.path.join(FR, f"{k:05d}.jpg")
    return Image.open(p).convert("RGB") if os.path.exists(p) else None


def box_at(src_t, max_dt=0.9):
    best, bd = None, 1e9
    for f in tl:
        d = abs(f["t"] - src_t)
        if d < bd:
            bd, best = d, f
        if f["t"] > src_t + max_dt:
            break
    return best["box"] if best and bd <= max_dt else None


def label(im, text, sub=None):
    d = ImageDraw.Draw(im)
    w = d.textlength(text, font=font)
    d.rectangle([0, 0, w + 12, 30], fill="black")
    d.text((6, 3), text, fill="yellow", font=font)
    if sub:
        w2 = d.textlength(sub, font=font_s)
        d.rectangle([0, 30, w2 + 12, 54], fill="black")
        d.text((6, 32), sub, fill="white", font=font_s)
    return im


def grid(tiles, cols, path):
    if not tiles:
        return None
    tw, th = tiles[0].size
    rows = math.ceil(len(tiles) / cols)
    sheet = Image.new("RGB", (cols * tw, rows * th), "black")
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % cols) * tw, (i // cols) * th))
    sheet.save(path, quality=86)
    return path


def flow_sheets(c):
    """Wide court crop (380,150)-(1920,950) -> 960x499 tiles, 2 fps, 8 per sheet."""
    out = []
    times = []
    t = c["reel_start"]
    while t < c["reel_end"] - 0.05:
        times.append(round(t, 2)); t += 0.5
    for s in range(0, len(times), 8):
        tiles = []
        for rt in times[s:s + 8]:
            im = frame_at(rt)
            if im is None:
                continue
            im = im.crop((380, 150, 1920, 950)).resize((960, 499), Image.LANCZOS)
            src = c["src_start"] + (rt - c["reel_start"])
            label(im, f"r{c['i']:03d}  reel {fmt(rt)}  src {fmt(src)}")
            tiles.append(im)
        p = os.path.join(OUT, f"r{c['i']:03d}_flow_{s // 8 + 1}.jpg")
        if grid(tiles, 2, p):
            out.append({"path": os.path.basename(p), "reel_from": times[s], "reel_to": times[min(s + 7, len(times) - 1)], "fps": 2,
                        "view": "wide court crop x380-1920 y150-950, 2 cols x 4 rows, read left-right then down"})
    return out


def zoom_tile(rt, src_t, c, note, xy_hint=None, W=640, H=560):
    im = frame_at(rt)
    if im is None:
        return None
    b = box_at(src_t)
    if b:
        cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2 - 40
    elif xy_hint:
        cx, cy = xy_hint[0], xy_hint[1] - 150
    else:
        cx, cy = 900, 560
    x0 = int(max(0, min(1920 - W, cx - W / 2)))
    y0 = int(max(0, min(1080 - H, cy - H / 2)))
    tile = im.crop((x0, y0, x0 + W, y0 + H))
    tag = "box" if b else ("xy" if xy_hint else "fallback")
    label(tile, f"r{c['i']:03d}  reel {fmt(rt)}  src {fmt(src_t)}", f"{note}  [{tag}]")
    return tile


def zoom_sheets(c):
    """5 fps over each non-shot touch window, following his box. 12 tiles per sheet (4x3)."""
    out = []
    n = 0
    for ti, t in enumerate(c["touches"]):
        if "shot" in t["actions"]:
            continue  # shots get their own strips
        a = max(c["src_start"], t["t_start"] - 0.6)
        b = min(c["src_end"], t["t_end"] + 1.4)
        times = []
        s = a
        while s < b:
            times.append(round(s, 2)); s += 0.2
        for k in range(0, len(times), 12):
            tiles = []
            for st in times[k:k + 12]:
                rt = c["reel_start"] + (st - c["src_start"])
                tile = zoom_tile(rt, st, c, "/".join(t["actions"]))
                if tile is not None:
                    tiles.append(tile)
            n += 1
            p = os.path.join(OUT, f"r{c['i']:03d}_zoom_{n}.jpg")
            if grid(tiles, 4, p):
                out.append({"path": os.path.basename(p), "src_from": times[k], "src_to": times[min(k + 11, len(times) - 1)], "fps": 5,
                            "touch_actions": t["actions"], "view": "640x560 window following Barak (4 cols x 3 rows, read left-right then down)"})
    return out


def shot_strips(c):
    """10 fps, release-1.4 .. release+1.0, following the box / release xy. 12 tiles per sheet (4x3)."""
    out = []
    for sh in c["shots"]:
        a = att.get(sh["id"], {})
        xy = a.get("xy")
        rel = sh["t"]
        times = [round(rel - 1.4 + i * 0.1, 2) for i in range(25)]
        for k in range(0, len(times), 12):
            tiles = []
            for st in times[k:k + 12]:
                if st < c["src_start"] or st > c["src_end"]:
                    continue
                rt = c["reel_start"] + (st - c["src_start"])
                if abs(st - rel) < 0.06:
                    mark = "RELEASE"
                elif st > rel:
                    mark = "+%.1f" % (st - rel)
                else:
                    mark = "%.1f" % (st - rel)
                tile = zoom_tile(rt, st, c, f"shot {sh['id']} {mark}", xy_hint=xy)
                if tile is not None:
                    tiles.append(tile)
            p = os.path.join(OUT, f"r{c['i']:03d}_shot_{sh['id']}_{k // 12 + 1}.jpg")
            if grid(tiles, 4, p):
                out.append({"path": os.path.basename(p), "shot_id": sh["id"], "release_src": rel, "made": sh.get("made"), "points": sh.get("points"),
                            "src_from": times[k], "src_to": times[min(k + 11, len(times) - 1)], "fps": 10,
                            "type_from_pipeline": a.get("type", ""),
                            "view": "640x560 window on the shooter, 10 fps (4 cols x 3 rows, read left-right then down)"})
    return out


def release_fullframe(c):
    """One full-resolution frame at each release (for arc/feet context)."""
    out = []
    for sh in c["shots"]:
        rt = c["reel_start"] + (sh["t"] - c["src_start"])
        im = frame_at(rt)
        if im is None:
            continue
        label(im, f"r{c['i']:03d}  shot {sh['id']}  RELEASE  reel {fmt(rt)}  src {fmt(sh['t'])}")
        p = os.path.join(OUT, f"r{c['i']:03d}_release_{sh['id']}.jpg")
        im.save(p, quality=86)
        out.append({"path": os.path.basename(p), "shot_id": sh["id"], "view": "full 1920x1080 frame at the release"})
    return out


if __name__ == "__main__":
    decode()
    index = []
    for c in clips:
        entry = {"clip": c["i"], "reel_start": c["reel_start"], "reel_end": c["reel_end"], "src_start": c["src_start"], "src_end": c["src_end"],
                 "flow": flow_sheets(c), "zoom": zoom_sheets(c), "shots": shot_strips(c), "release_frames": release_fullframe(c)}
        index.append(entry)
        print(f"r{c['i']:03d}: flow {len(entry['flow'])}  zoom {len(entry['zoom'])}  shot {len(entry['shots'])}  rel {len(entry['release_frames'])}", flush=True)
    json.dump(index, open(os.path.join(HERE, "sheets_index.json"), "w", encoding="utf-8"), indent=1)
    print("sheets:", len(glob.glob(os.path.join(OUT, "*.jpg"))))
