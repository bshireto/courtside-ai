"""Render user-centred contact sheets (5 fps, 6 s per sheet) for possession labelling.

Every tile is a square crop around the user's detected box (interpolated across
short gaps). Tiles where the user could not be located show the whole frame
with a red "NOT LOCATED" banner so the reviewer can look for him manually.
Output: SCRATCH/usheets/u_<start>.jpg and data/user_sheets.json
"""
import json, os, bisect
from PIL import Image, ImageDraw, ImageFont

import sys as _s, os as _o
_s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
import bbconfig
F5 = bbconfig.F5
OUT = _o.path.join(bbconfig.WORK, "usheets")
TILE, COLS, SPAN = 220, 6, 6.0
os.makedirs(OUT, exist_ok=True)
tl = json.load(open("data/user_timeline_v2.json"))["frames"]
ts = [f["t"] for f in tl]
font = ImageFont.truetype("arialbd.ttf", 17)


def box_at(t):
    i = bisect.bisect_left(ts, t - 1e-6)
    if i < len(ts) and abs(ts[i] - t) < 1e-3:
        return tl[i]["box"], "det"
    a = tl[i - 1] if i > 0 else None
    b = tl[i] if i < len(ts) else None
    if a and b and b["t"] - a["t"] <= 1.6 and bbconfig.setup_of(a["t"]) == bbconfig.setup_of(b["t"]):
        w = (t - a["t"]) / (b["t"] - a["t"])
        return [a["box"][j] * (1 - w) + b["box"][j] * w for j in range(4)], "interp"
    return None, None


def fmt(t):
    return f"{int(t // 60)}:{t % 60:04.1f}"


def main():
    index = []
    segs = [(float(s["start"]), float(s["end"])) for s in bbconfig.SETUPS]
    for s0, s1 in segs:
        t0 = s0
        while t0 < s1:
            times = [round(t0 + i * 0.2, 2) for i in range(int(SPAN * 5)) if t0 + i * 0.2 < s1]
            rows = (len(times) + COLS - 1) // COLS
            sheet = Image.new("RGB", (COLS * TILE, rows * TILE), (25, 25, 25))
            located = 0
            for j, t in enumerate(times):
                k = int(round(t * 5)) + 1
                p = os.path.join(F5, f"{k:05d}.jpg")
                if not os.path.exists(p):
                    continue
                im = Image.open(p).convert("RGB")
                box, how = box_at(t)
                if box:
                    x0, y0, x1, y1 = box
                    h = y1 - y0
                    S = max(170, 1.55 * h)
                    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2 - 0.05 * h
                    c = im.crop((int(cx - S / 2), int(cy - S / 2), int(cx + S / 2), int(cy + S / 2))).resize((TILE, TILE), Image.LANCZOS)
                    located += 1
                else:
                    th = im.resize((TILE, int(TILE * 1080 / 1920)), Image.LANCZOS)
                    c = Image.new("RGB", (TILE, TILE), (60, 0, 0))
                    c.paste(th, (0, (TILE - th.height) // 2))
                d = ImageDraw.Draw(c)
                lab = fmt(t) + ("~" if how == "interp" else "")
                d.rectangle([0, 0, d.textlength(lab, font=font) + 6, 20], fill="black")
                d.text((3, 1), lab, fill="yellow", font=font)
                if not box:
                    d.rectangle([0, TILE - 22, TILE, TILE], fill=(170, 0, 0))
                    d.text((4, TILE - 21), "NOT LOCATED", fill="white", font=font)
                sheet.paste(c, ((j % COLS) * TILE, (j // COLS) * TILE))
            name = os.path.join(OUT, f"u_{int(round(t0 * 10)):05d}.jpg")
            sheet.save(name, quality=87)
            index.append({"start": round(t0, 2), "end": round(times[-1] + 0.2, 2), "path": name, "located": located, "n": len(times)})
            t0 += SPAN
    json.dump(index, open("data/user_sheets.json", "w"), indent=0)
    loc = sum(i["located"] for i in index) / sum(i["n"] for i in index)
    print("sheets", len(index), f"located {loc:.0%}")


if __name__ == "__main__":
    main()
