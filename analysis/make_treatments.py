"""Render one still per coaching-video treatment (for the output-format decision map).
Texts and coordinates come from treatments.json so the stills can be re-rendered with verified captions.
Outputs ../docs/assets/treat_<key>.jpg at 1280x720.
"""
import json, os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FR = os.path.join(HERE, "work", "frames")
OUT = os.path.join(HERE, "..", "docs", "assets")
os.makedirs(OUT, exist_ok=True)
T = json.load(open(os.path.join(HERE, "treatments.json"), encoding="utf-8"))
F = lambda s: ImageFont.truetype("segoeuib.ttf", s)
FR_ = lambda s: ImageFont.truetype("segoeui.ttf", s)
ORANGE = (255, 107, 0)


def frame(reel_t):
    return Image.open(os.path.join(FR, f"{int(round(reel_t * 10)) + 1:05d}.jpg")).convert("RGB")


def crop16(im, cx, cy, w=1280):
    h = int(w * 9 / 16)
    x0 = int(max(0, min(im.width - w, cx - w / 2))); y0 = int(max(0, min(im.height - h, cy - h / 2)))
    return im.crop((x0, y0, x0 + w, y0 + h)), x0, y0


def caption_bar(im, text, size=34, y=None):
    d = ImageDraw.Draw(im, "RGBA")
    f = F(size)
    tw = d.textlength(text, font=f)
    y = im.height - 86 if y is None else y
    d.rectangle([im.width / 2 - tw / 2 - 26, y - 12, im.width / 2 + tw / 2 + 26, y + size + 16], fill=(0, 0, 0, 165))
    d.text((im.width / 2 - tw / 2, y), text, fill="white", font=f)


def corner_tag(im, text):
    d = ImageDraw.Draw(im, "RGBA"); f = F(22); tw = d.textlength(text, font=f)
    d.rectangle([im.width - tw - 60, 36, im.width - 30, 72], fill=(0, 0, 0, 150)); d.text((im.width - tw - 45, 42), text, fill="white", font=f)


def arrow(d, a, b, col=ORANGE, w=7):
    d.line([a, b], fill=col, width=w)
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    for s in (-1, 1):
        d.line([b, (b[0] - 26 * math.cos(ang + s * 0.5), b[1] - 26 * math.sin(ang + s * 0.5))], fill=col, width=w)


def ring(d, c, r, col=ORANGE):
    d.ellipse([c[0] - r - 4, c[1] - r - 4, c[0] + r + 4, c[1] + r + 4], outline=(0, 0, 0, 170), width=10)
    d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], outline=col, width=6)


def save(im, key):
    p = os.path.join(OUT, f"treat_{key}.jpg"); im.save(p, quality=86); print("wrote", p)


# A. caption bar
a = T["caption_bar"]
im, _, _ = crop16(frame(a["reel_t"]), *a["center"])
caption_bar(im, a["text"]); corner_tag(im, "LIVE")
save(im, "caption_bar")

# B. coach card
b = T["coach_card"]
im, _, _ = crop16(frame(b["reel_t"]), *b["center"])
d = ImageDraw.Draw(im, "RGBA")
d.rectangle([40, 40, 560, 232], fill=(24, 28, 33, 225))
d.rectangle([40, 40, 48, 232], fill=ORANGE)
d.text((70, 56), b["eyebrow"], fill=ORANGE, font=F(20))
d.text((70, 86), b["title"], fill="white", font=F(32))
d.text((70, 134), b["cue"], fill=(255, 213, 184), font=FR_(26))
d.text((70, 176), b["stat"], fill=(189, 191, 194), font=FR_(22))
save(im, "coach_card")

# C. split screen
c = T["split"]
src = frame(c["reel_t"])
wide = src.crop((380, 150, 1920, 1016)).resize((640, 360), Image.LANCZOS)
zx, zy = c["zoom_center"]
zoom = src.crop((zx - 320, zy - 180, zx + 320, zy + 180))
canvas = Image.new("RGB", (1280, 720), (24, 28, 33))
canvas.paste(wide, (0, 0)); canvas.paste(zoom, (640, 0))
# second row: the same two 1 s later
src2 = frame(c["reel_t"] + c.get("dt", 1.0))
canvas.paste(src2.crop((380, 150, 1920, 1016)).resize((640, 360), Image.LANCZOS), (0, 360))
zx2, zy2 = c.get("zoom_center2", c["zoom_center"])
canvas.paste(src2.crop((zx2 - 320, zy2 - 180, zx2 + 320, zy2 + 180)), (640, 360))
d = ImageDraw.Draw(canvas, "RGBA")
for (x, y, t) in ((10, 10, "WIDE"), (650, 10, "FOLLOW"), (10, 370, "WIDE +1 s"), (650, 370, "FOLLOW +1 s")):
    tw = d.textlength(t, font=F(18)); d.rectangle([x, y, x + tw + 16, y + 28], fill=(0, 0, 0, 160)); d.text((x + 8, y + 3), t, fill="white", font=F(18))
d.line([(640, 0), (640, 720)], fill=(24, 28, 33), width=4); d.line([(0, 360), (1280, 360)], fill=(24, 28, 33), width=4)
caption_bar(canvas, c["text"], size=30)
save(canvas, "split")

# D. freeze + ring + arrow
dd = T["freeze_ring"]
im, x0, y0 = crop16(frame(dd["reel_t"]), *dd["center"])
d = ImageDraw.Draw(im, "RGBA")
rx, ry = dd["ring"]; ring(d, (rx - x0, ry - y0), dd.get("r", 70))
ax, ay = dd["arrow_from"]; bx, by = dd["arrow_to"]; arrow(d, (ax - x0, ay - y0), (bx - x0, by - y0))
lx, ly = dd["label_at"]; f = F(24); tw = d.textlength(dd["label"], font=f)
d.rectangle([lx - x0 - 8, ly - y0 - 6, lx - x0 + tw + 8, ly - y0 + 30], fill=(0, 0, 0, 170)); d.text((lx - x0, ly - y0), dd["label"], fill="white", font=f)
corner_tag(im, "FREEZE"); caption_bar(im, dd["text"])
save(im, "freeze_ring")

# E. pose skeleton with measured angles
e = T["pose"]
try:
    os.environ["YOLO_VERBOSE"] = "False"
    from ultralytics import YOLO
    model = YOLO(os.path.join(HERE, "..", "yolo11m-pose.pt")) if os.path.exists(os.path.join(HERE, "..", "yolo11m-pose.pt")) else YOLO("yolo11m-pose.pt")
    src = frame(e["reel_t"]); cx, cy = e["center"]
    W, H = 640, 560
    x0 = int(max(0, min(1920 - W, cx - W / 2))); y0 = int(max(0, min(1080 - H, cy - H / 2)))
    crop = src.crop((x0, y0, x0 + W, y0 + H)).resize((W * 2, H * 2), Image.LANCZOS)
    res = model.predict(np.asarray(crop)[:, :, ::-1], imgsz=1280, conf=0.25, verbose=False)[0]
    plotted = Image.fromarray(res.plot(boxes=False, labels=False, kpt_radius=6, kpt_line=True)[:, :, ::-1])
    kp = res.keypoints.xy.cpu().numpy(); n = len(kp)
    kc = res.keypoints.conf.cpu().numpy()
    ci = min(range(n), key=lambda i: abs(kp[i][:, 0].mean() - W) + abs(kp[i][:, 1].mean() - H))
    P = kp[ci]; C = kc[ci]

    def ang(a, b, c):
        if min(C[a], C[b], C[c]) < 0.5:
            return None   # a joint the model is not sure about: do not print a number
        v1, v2 = P[a] - P[b], P[c] - P[b]
        return math.degrees(math.acos(np.clip(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6), -1, 1)))
    fmt_a = lambda v: "n/a" if v is None else f"{v:.0f}°"
    r_elbow = ang(6, 8, 10); l_elbow = ang(5, 7, 9); r_knee = ang(12, 14, 16); l_knee = ang(11, 13, 15)
    # crop plotted (1280x1120) to 16:9
    im = plotted.crop((0, 120, 1280, 840))
    d = ImageDraw.Draw(im, "RGBA")
    d.rectangle([40, 40, 470, 215], fill=(24, 28, 33, 225)); d.rectangle([40, 40, 48, 215], fill=ORANGE)
    d.text((70, 52), "MEASURED AT THE RELEASE", fill=ORANGE, font=F(18))
    d.text((70, 82), f"Right elbow  {fmt_a(r_elbow)}    Left elbow  {fmt_a(l_elbow)}", fill="white", font=F(24))
    d.text((70, 118), f"Right knee  {fmt_a(r_knee)}    Left knee  {fmt_a(l_knee)}", fill="white", font=F(24))
    d.text((70, 160), e["note"], fill=(189, 191, 194), font=FR_(20))
    corner_tag(im, "POSE"); caption_bar(im, e["text"])
    save(im, "pose")
    json.dump({"r_elbow": r_elbow, "l_elbow": l_elbow, "r_knee": r_knee, "l_knee": l_knee, "joint_conf": [float(x) for x in C]}, open(os.path.join(HERE, "work", "pose", "angles_c077.json"), "w"))
except Exception as ex:
    print("pose treatment skipped:", ex)

# F. before / after (practice July vs game October)
f_ = T["before_after"]
left = Image.open(os.path.join(HERE, "..", "frames", f_["july_frame"])).convert("RGB")
left = left.resize((int(left.width * 720 / left.height), 720), Image.LANCZOS)
src = frame(f_["reel_t"]); cx, cy = f_["center"]
right = src.crop((cx - 270, cy - 360, cx + 270, cy + 360)).resize((540, 720), Image.LANCZOS)
canvas = Image.new("RGB", (1280, 720), (24, 28, 33))
lw = left.width
canvas.paste(left, ((640 - lw) // 2, 0)); canvas.paste(right, (640 + 50, 0))
d = ImageDraw.Draw(canvas, "RGBA")
for (x, t) in ((20, f_["left_label"]), (660, f_["right_label"])):
    tw = d.textlength(t, font=F(22)); d.rectangle([x, 14, x + tw + 20, 50], fill=(0, 0, 0, 170)); d.text((x + 10, 18), t, fill="white", font=F(22))
caption_bar(canvas, f_["text"], size=28)
save(canvas, "before_after")

# G. telestration on the floor
g = T["telestration"]
im, x0, y0 = crop16(frame(g["reel_t"]), *g["center"])
over = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(over)
poly = [(x - x0, y - y0) for x, y in g["zone"]]
d.polygon(poly, fill=(0, 124, 50, 70), outline=(0, 124, 50, 220))
ax, ay = g["arrow_from"]; bx, by = g["arrow_to"]; arrow(d, (ax - x0, ay - y0), (bx - x0, by - y0), col=(255, 107, 0, 255))
for (lx, ly, t) in g["labels"]:
    f = F(22); tw = d.textlength(t, font=f); d.rectangle([lx - x0 - 8, ly - y0 - 6, lx - x0 + tw + 8, ly - y0 + 28], fill=(0, 0, 0, 170)); d.text((lx - x0, ly - y0), t, fill="white", font=f)
im = Image.alpha_composite(im.convert("RGBA"), over).convert("RGB")
corner_tag(im, "TELESTRATION"); caption_bar(im, g["text"])
save(im, "telestration")
print("done")
