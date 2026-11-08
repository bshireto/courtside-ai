"""Per-drive diagrams on the real court: Barak's tracked path during the drive, the defender at the decision moment,
the side that was open. Also builds (and caches) the players-removed court background.

  python make_drive_diagrams.py            -> work/drives/d<clip>.jpg for every record in results/drives.json
Inputs: results/drives.json (DRIVE records), clip_map.json, ../recap_2026-10-07/data/user_timeline_v2.json, work/frames.
"""
import glob, json, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.join(HERE, "..", "recap_2026-10-07")
FR = os.path.join(HERE, "work", "frames")
OUT = os.path.join(HERE, "work", "drives")
os.makedirs(OUT, exist_ok=True)
RIM = (1254, 320)
SUNSET, THUNDER, NAVY, GREEN, WHITE = (239, 59, 36), (0, 122, 193), (0, 45, 98), (0, 124, 50), (255, 255, 255)


def background():
    p = os.path.join(HERE, "court_bg.jpg")
    if os.path.exists(p):
        return Image.open(p).convert("RGB")
    cfg = json.load(open(os.path.join(GAME, "game.json"), encoding="utf-8"))
    arc = cfg["hoops"]["A"]["arc"]
    files = sorted(glob.glob(os.path.join(FR, "*.jpg")))
    pick = files[20:-120:max(1, (len(files) - 140) // 25)][:25]
    stack = np.stack([np.asarray(Image.open(f).convert("RGB")) for f in pick])
    bg = np.empty(stack.shape[1:], np.uint8)
    for y in range(0, 1080, 90):
        bg[y:y + 90] = np.median(stack[:, y:y + 90], axis=0).astype(np.uint8)
    bg = Image.fromarray(bg)
    bg = Image.blend(bg, Image.new("RGB", bg.size, (0, 0, 0)), 0.2)
    d = ImageDraw.Draw(bg)
    d.line([tuple(arc["apex"])] + [tuple(q) for q in arc["near"]], fill=WHITE, width=3)
    d.line([tuple(arc["apex"])] + [tuple(q) for q in arc["far"]], fill=WHITE, width=3)
    d.line([tuple(q) for q in arc["baseline"]], fill=WHITE, width=2)
    bg.save(p, quality=90)
    return bg


def arrow(d, a, b, col, w=6, head=22):
    d.line([a, b], fill=col, width=w)
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    for s in (-1, 1):
        d.line([b, (b[0] - head * math.cos(ang + s * 0.5), b[1] - head * math.sin(ang + s * 0.5))], fill=col, width=w)


def side_vector(pos, side):
    """unit vector on the image for 'left'/'right' from a player at pos facing the rim"""
    vx, vy = RIM[0] - pos[0], RIM[1] - pos[1]
    n = math.hypot(vx, vy) or 1
    vx, vy = vx / n, vy / n
    if side == "left":
        return (vy, -vx)
    if side == "right":
        return (-vy, vx)
    return (vx, vy)


def main():
    drives = json.load(open(os.path.join(HERE, "results", "drives.json"), encoding="utf-8"))
    clips = {c["i"]: c for c in json.load(open(os.path.join(HERE, "clip_map.json"), encoding="utf-8"))}
    tl = json.load(open(os.path.join(GAME, "data", "user_timeline_v2.json"), encoding="utf-8"))["frames"]
    tl.sort(key=lambda f: f["t"])
    bg = background()
    font = ImageFont.truetype("segoeuib.ttf", 26)
    out = {}
    for dr in drives:
        c = clips[dr["clip"]]
        t0 = c["src_start"] + (dr["decision_reel"] - c["reel_start"]) - 0.6
        t1 = c["src_start"] + (dr["passby_reel"] - c["reel_start"]) + 0.8
        pts = [((f["box"][0] + f["box"][2]) / 2, f["box"][3]) for f in tl if t0 <= f["t"] <= t1]
        im = bg.copy()
        d = ImageDraw.Draw(im)
        bf = tuple(dr.get("barak_feet_px") or (pts[len(pts) // 2] if pts else (900, 600)))
        df = tuple(dr["defender_at_decision"].get("feet_px") or (bf[0] + 60, bf[1] - 40))
        # open side arrow (green) from the decision spot
        if dr.get("side_open") in ("left", "right"):
            vx, vy = side_vector(bf, dr["side_open"])
            fx, fy = (RIM[0] - bf[0]), (RIM[1] - bf[1]); n = math.hypot(fx, fy) or 1
            # a drive line: sideways step then toward the rim
            p1 = (bf[0] + vx * 70, bf[1] + vy * 70)
            p2 = (p1[0] + fx / n * 150, p1[1] + fy / n * 150)
            d.line([bf, p1], fill=GREEN, width=6)
            arrow(d, p1, p2, GREEN, w=6)
        # actual path (sunset)
        if len(pts) >= 2:
            for i in range(len(pts) - 1):
                d.line([pts[i], pts[i + 1]], fill=SUNSET, width=7)
            arrow(d, pts[-2], pts[-1], SUNSET, w=7)
        # defender + Barak at the decision moment
        d.ellipse([df[0] - 14, df[1] - 14, df[0] + 14, df[1] + 14], fill=NAVY, outline=WHITE, width=3)
        d.ellipse([bf[0] - 14, bf[1] - 14, bf[0] + 14, bf[1] + 14], fill=SUNSET, outline=WHITE, width=3)
        # crop around the action
        xs = [p[0] for p in pts] + [bf[0], df[0]]; ys = [p[1] for p in pts] + [bf[1], df[1]]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2 - 40
        w = max(760, (max(xs) - min(xs)) * 1.8); h = w * 9 / 16
        x0 = int(max(0, min(1920 - w, cx - w / 2))); y0 = int(max(0, min(1080 - h, cy - h / 2)))
        im = im.crop((x0, y0, int(x0 + w), int(y0 + h))).resize((880, 495), Image.LANCZOS)
        p = os.path.join(OUT, f"d{dr['clip']:02d}.jpg")
        im.save(p, quality=84)
        out[dr["clip"]] = p
        print("wrote", p, "path points", len(pts))
    return out


if __name__ == "__main__":
    main()
