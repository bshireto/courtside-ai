"""Paste a Weavy-generated figure of Barak onto a real frame in place of the real Barak ("what a better choice would look like").

  python make_weavy_sim.py <spec.json>

spec = {
  "frame_reel": 264.2,                      # reel time of the real frame used as the base
  "generated": "work/weavy/gen_01.png",     # figure on a flat green background
  "flip": false,                            # mirror the figure (note: this swaps his hands)
  "outfit": "maroon_tee",                   # game 1 only (clips 0-11): he wore no orange bib, recolour it to the maroon shirt
  "barak_at": [455, 560],                   # body centre of the real Barak in the base frame: he is erased. null = keep him
  "anchor": "right_foot",                   # which point of the figure is placed: right_foot | left_foot | feet_center
  "anchor_frame": [585, 642],               # where that point lands, in frame pixels (a spot on the floor)
  "figure_height_px": 156,                  # height of the pasted figure, head top to sole, in frame pixels
  "in_front": [[620, 560]],                 # body centres of players who stand NEARER the camera than the simulated figure
  "brightness": 0.84,
  "out": "work/weavy/sim_c23_right.png",
  "zones": [{"poly": [[x, y], ...]}], "arrows": [{"pts": [[x, y], ...], "col": [r, g, b]}],
  "rings": [{"at": [x, y], "r": 50}], "labels": [{"at": [x, y], "text": "...", "size": 28}],      # drawn on the simulated frame
  "panel": {"crop": [260, 330, 1320, 780], "left_title": "...", "right_title": "...", "real_reel": 265.0,
            "real_arrows": [...], "real_rings": [...], "real_labels": [...], "out": "work/weavy/sim_c23_panel.jpg"}
}
Older specs with "anchor_gen": "front_foot" and "standing_height_px" * "crouch_ratio" still work.

Steps: erase the real player with the empty-court plate (work/weavy/court_clean.png) under his segmentation mask, key the
figure off its green background, match size / softness / brightness, add a floor shadow, paste, put the nearer players back
on top, annotate (Hebrew is fine), and build a two-up panel: what really happened next to the simulation.
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from bidi.algorithm import get_display

HERE = os.path.dirname(os.path.abspath(__file__))
SUNSET, GREEN, NAVY, WHITE = (239, 59, 36), (0, 160, 70), (0, 45, 98), (255, 255, 255)
_seg = None


def frame(rt):
    return Image.open(os.path.join(HERE, "work", "frames", f"{int(round(rt * 10)) + 1:05d}.jpg")).convert("RGB")


def key_green(im):
    """RGBA cut-out of a figure on a flat green background, with despill."""
    a = np.asarray(im.convert("RGB")).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    green = g - np.maximum(r, b)
    alpha = np.clip(1.0 - (green - 40) / 60.0, 0, 1)
    alpha = np.asarray(Image.fromarray((alpha * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.2))) / 255.0
    g2 = np.minimum(g, np.maximum(r, b) + 12)
    return Image.fromarray(np.dstack([r, g2, b, alpha * 255]).astype(np.uint8), "RGBA")


def maroon_tee(im):
    """Game-1 outfit: recolour the orange bib of a generated figure to the maroon of the T-shirt under it.
    The bib is the largest orange region (the ball is orange too, but smaller and separate)."""
    import cv2
    a = np.asarray(im.convert("RGB")).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    orange = ((r > 150) & (r - b > 80) & (g > 0.2 * r) & (g < 0.62 * r)).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(cv2.morphologyEx(orange, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8)), 8)
    if n < 2:
        return im
    k = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    bib = (lab == k) & (orange > 0)
    sleeve = (r > 70) & (r < 165) & (g < 0.5 * r) & (b < 0.62 * r) & (r - g > 40)
    base = a[sleeve].mean(axis=0) if sleeve.sum() > 200 else np.array([118.0, 34.0, 48.0])
    luma = a[..., :3].mean(axis=2)
    gain = (luma / max(1.0, luma[bib].mean()))[..., None]
    out = a.copy()
    out[bib] = np.clip(base[None, :] * gain[bib] * 1.05, 0, 255)
    res = Image.fromarray(out.astype(np.uint8))
    return res


def person_mask(fr, at, grow=0, blur=1.5):
    """Full-frame mask (L) of the person whose body centre is nearest to `at`."""
    global _seg
    if _seg is None:
        os.environ["YOLO_VERBOSE"] = "False"
        from ultralytics import YOLO
        w = os.path.join(HERE, "yolo11s-seg.pt")
        _seg = YOLO(w if os.path.exists(w) else "yolo11s-seg.pt")
    x0, y0 = int(max(0, at[0] - 240)), int(max(0, at[1] - 220))
    x1, y1 = int(min(fr.width, at[0] + 240)), int(min(fr.height, at[1] + 220))
    S = 3
    crop = fr.crop((x0, y0, x1, y1)); big = crop.resize((crop.width * S, crop.height * S), Image.LANCZOS)
    r = _seg.predict(np.asarray(big)[:, :, ::-1], imgsz=1280, conf=0.2, classes=[0], verbose=False)[0]
    full = Image.new("L", fr.size, 0)
    if r.masks is None:
        return full
    target = np.array([(at[0] - x0) * S, (at[1] - y0) * S])
    cents = [((b[0] + b[2]) / 2, (b[1] + b[3]) / 2) for b in r.boxes.xyxy.cpu().numpy()]
    k = int(np.argmin([np.hypot(c[0] - target[0], c[1] - target[1]) for c in cents]))
    mk = Image.fromarray((r.masks.data[k].cpu().numpy() * 255).astype(np.uint8)).resize(crop.size, Image.BILINEAR)
    if grow:
        mk = mk.filter(ImageFilter.MaxFilter(grow))
    mk = mk.filter(ImageFilter.GaussianBlur(blur))
    full.paste(mk, (x0, y0))
    return full


def text(d, xy, s, size=30, fill=WHITE, box=(0, 0, 0, 170), anchor="l"):
    f = ImageFont.truetype("segoeuib.ttf", size)
    vis = get_display(s); tw = d.textlength(vis, font=f)
    x = xy[0] - (tw if anchor == "r" else tw / 2 if anchor == "c" else 0)
    d.rectangle([x - 10, xy[1] - 6, x + tw + 10, xy[1] + size + 10], fill=box)
    d.text((x, xy[1]), vis, fill=fill, font=f)


def arrow(d, pts, col, w=7, head=24):
    d.line(pts, fill=col, width=w, joint="curve")
    a, b = pts[-2], pts[-1]; ang = math.atan2(b[1] - a[1], b[0] - a[0])
    for s in (-1, 1):
        d.line([b, (b[0] - head * math.cos(ang + s * 0.5), b[1] - head * math.sin(ang + s * 0.5))], fill=col, width=w)


def annotate(im, zones=(), arrows=(), rings=(), labels=()):
    ann = im.convert("RGBA"); over = Image.new("RGBA", ann.size, (0, 0, 0, 0)); d = ImageDraw.Draw(over)
    for z in zones:
        d.polygon([tuple(p) for p in z["poly"]], fill=tuple(z.get("fill", (0, 160, 70, 60))), outline=tuple(z.get("outline", (0, 160, 70, 220))))
    for ar in arrows:
        arrow(d, [tuple(p) for p in ar["pts"]], tuple(ar.get("col", GREEN)) + (255,))
    for r in rings:
        c, rad = r["at"], r.get("r", 34)
        d.ellipse([c[0] - rad, c[1] - rad, c[0] + rad, c[1] + rad], outline=tuple(r.get("col", SUNSET)) + (255,), width=5)
    for lb in labels:
        text(d, lb["at"], lb["text"], size=lb.get("size", 28), anchor=lb.get("anchor", "l"))
    return Image.alpha_composite(ann, over).convert("RGB")


def main(spec):
    fr = frame(spec["frame_reel"])
    plate = Image.open(os.path.join(HERE, "work", "weavy", "court_clean.png")).convert("RGB")
    base = fr
    if spec.get("barak_at"):
        base = Image.composite(plate, fr, person_mask(fr, spec["barak_at"], grow=13, blur=2.5))
    gen = Image.open(os.path.join(HERE, spec["generated"]))
    if spec.get("flip"):
        gen = gen.transpose(Image.FLIP_LEFT_RIGHT)
    if spec.get("outfit") == "maroon_tee":                  # game 1: no orange bib
        gen = maroon_tee(gen)
    fig = key_green(gen)
    al = np.asarray(fig)[..., 3]; ys, xs = np.where(al > 128)
    fig = fig.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    target_h = spec.get("figure_height_px") or spec["standing_height_px"] * spec.get("crouch_ratio", 0.82)
    sc = target_h / fig.height
    fig = fig.resize((max(1, int(fig.width * sc)), max(1, int(fig.height * sc))), Image.LANCZOS)
    rgb = fig.convert("RGB").filter(ImageFilter.GaussianBlur(0.7))
    arr = np.asarray(rgb).astype(np.float32); grey = arr.mean(axis=2, keepdims=True)
    arr = (grey + (arr - grey) * 0.9) * spec.get("brightness", 0.86)
    fig = Image.merge("RGBA", (*Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).split(), fig.split()[3].filter(ImageFilter.GaussianBlur(0.6))))
    a = np.asarray(fig)[..., 3]
    low = np.where(a[int(fig.height * 0.9):] > 128)[1]
    anchor = spec.get("anchor") or ("right_foot" if spec.get("anchor_gen", "front_foot") == "front_foot" else "feet_center")
    if anchor == "right_foot":
        ax = int(low.max() - 0.04 * fig.width)
    elif anchor == "left_foot":
        ax = int(low.min() + 0.04 * fig.width)
    else:
        ax = int((low.min() + low.max()) / 2)
    # the sole of the anchored foot, not the bottom of the whole cut-out (a trailing foot on its toe can hang lower)
    half = max(3, int(0.09 * fig.width))
    cols = a[:, max(0, ax - half):min(fig.width, ax + half)]
    rows = np.where((cols > 128).any(axis=1))[0]
    ay = int(rows.max()) if len(rows) and anchor != "feet_center" else fig.height - 2
    px, py = int(spec["anchor_frame"][0] - ax), int(spec["anchor_frame"][1] - ay)
    sh = Image.new("L", base.size, 0); ds = ImageDraw.Draw(sh)
    ds.ellipse([px + fig.width * 0.05, py + ay - 9, px + fig.width * 0.95, py + ay + 12], fill=110)
    base = Image.composite(Image.new("RGB", base.size, (10, 14, 18)), base, sh.filter(ImageFilter.GaussianBlur(7)))
    base.paste(fig, (px, py), fig)
    for pt in spec.get("in_front", []):                     # players nearer the camera go back on top of the figure
        base = Image.composite(fr, base, person_mask(fr, pt, grow=0, blur=1.2))
    out = os.path.join(HERE, spec["out"])
    base.save(out)
    ann = annotate(base, spec.get("zones", []), spec.get("arrows", []), spec.get("rings", []), spec.get("labels", []))
    ann.save(out.replace(".png", "_annotated.jpg"), quality=90)
    print("wrote", out, "| figure", fig.size, "pasted at", (px, py), "to", (px + fig.width, py + fig.height))
    pn = spec.get("panel")
    if pn:
        C = tuple(pn["crop"])
        real = annotate(frame(pn.get("real_reel", spec["frame_reel"])), (), pn.get("real_arrows", []), pn.get("real_rings", []), pn.get("real_labels", []))
        left, right = real.crop(C), ann.crop(C)
        W, H = left.size
        panel = Image.new("RGB", (W * 2 + 24, H + 64), NAVY); dp = ImageDraw.Draw(panel)
        panel.paste(left, (0, 64)); panel.paste(right, (W + 24, 64))
        text(dp, (W // 2, 14), pn.get("left_title", ""), size=30, box=NAVY + (255,), anchor="c")
        text(dp, (W + 24 + W // 2, 14), pn.get("right_title", ""), size=30, box=NAVY + (255,), anchor="c")
        po = os.path.join(HERE, pn["out"])
        panel.save(po, quality=90)
        print("wrote", po, panel.size)


if __name__ == "__main__":
    main(json.load(open(sys.argv[1], encoding="utf-8")))
